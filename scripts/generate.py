import requests
import base64
import yaml
import hashlib
import re
import time
from urllib.parse import urlparse, parse_qs
from pathlib import Path

# ====================== 配置 ======================
CONFIG_FILE = "sub.yaml"
OUTPUT_RAW = "merged.txt"
OUTPUT_BASE64 = "merged_base64.txt"

DEDUPE_MODE = "moderate"   # none / moderate / strict （推荐 moderate）
TIMEOUT = 30
# ================================================

def load_config():
    with open(CONFIG_FILE, encoding='utf-8') as f:
        return yaml.safe_load(f)

def smart_decode(text: str) -> str:
    """智能解码多层 Base64"""
    text = text.strip()
    for _ in range(6):
        try:
            if re.match(r'^[A-Za-z0-9+/=\s-]+$', text):
                padding = '=' * (-len(text) % 4)
                text = base64.b64decode(text + padding).decode('utf-8').strip()
            else:
                break
        except:
            break
    return text

def get_dedupe_key(node: str) -> str:
    """生成去重键"""
    if DEDUPE_MODE == "none":
        return hashlib.md5(node.encode('utf-8')).hexdigest()

    node = node.strip()
    try:
        if node.startswith("vmess://"):
            b64 = node[8:].split("#")[0]
            cfg = json.loads(base64.b64decode(b64 + "===").decode('utf-8'))
            if DEDUPE_MODE == "moderate":
                return f"vmess:{cfg.get('add')}:{cfg.get('port')}:{cfg.get('id')}:{cfg.get('path','')}"
            return f"vmess:{cfg.get('add')}:{cfg.get('port')}"

        # vless / trojan / ss 等
        if "://" in node:
            parsed = urlparse(node)
            host = parsed.hostname or ""
            port = parsed.port or ""
            if DEDUPE_MODE == "moderate":
                query = parse_qs(parsed.query)
                sni = query.get("sni", [""])[0]
                return f"{parsed.scheme}:{host}:{port}:{sni or ''}"
            return f"{parsed.scheme}:{host}:{port}"
    except:
        pass
    return hashlib.md5(node.encode('utf-8')).hexdigest()

# ====================== 主程序 ======================
def main():
    config = load_config()
    subs = config.get("subscriptions", [])

    print(f"加载到 {len(subs)} 个订阅源")

    all_nodes = []
    seen = set()

    for sub in subs:
        name = sub.get("name", "unknown")
        url = sub.get("url")
        if not url:
            continue

        print(f"正在获取 [{name}] {url}")
        try:
            r = requests.get(url, timeout=TIMEOUT, headers={
                "User-Agent": "Sub-Store-Merger/1.0"
            })
            r.raise_for_status()

            content = smart_decode(r.text)

            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                key = get_dedupe_key(line)
                if key not in seen:
                    seen.add(key)
                    all_nodes.append(line)
        except Exception as e:
            print(f"  获取失败: {e}")
            time.sleep(1)

    print(f"\n合并完成！最终节点数: {len(all_nodes)}")

    # 保存明文
    Path(OUTPUT_RAW).write_text("\n".join(all_nodes), encoding="utf-8")

    # 保存 Base64（v2rayN 推荐）
    b64_content = base64.b64encode("\n".join(all_nodes).encode("utf-8")).decode("utf-8")
    Path(OUTPUT_BASE64).write_text(b64_content, encoding="utf-8")

    print(f"文件已生成：")
    print(f"   • {OUTPUT_RAW}")
    print(f"   • {OUTPUT_BASE64}  ← v2rayN 直接导入此文件的 Raw 链接")

if __name__ == "__main__":
    main()