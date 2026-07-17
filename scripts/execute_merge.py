import requests
import base64
import yaml
import re
import time
from pathlib import Path


# ====================== 配置 ======================
CONFIG_FILE = "config/Subscriptions-config.yaml"
OUTPUT_RAW = "out/result.txt"
TIMEOUT = 30
# ================================================
def load_config():
    with open(CONFIG_FILE,encoding="utf-8") as f:
        return yaml.safe_load(f)

def smart_decode(text: str) -> str:
    """
    智能解码多层 Base64
    """
    text = text.strip()
    for _ in range(6):
        try:
            # 判断是否像base64
            if re.match(r'^[A-Za-z0-9+/=\s-]+$',text):
                padding = '=' * (-len(text) % 4)
                decoded = base64.b64decode(text + padding).decode("utf-8").strip()
                # 防止死循环
                if decoded == text:
                    break
                text = decoded
            else:
                break
        except Exception:
            break
    return text

def parse_nodes(content):
    """
    解码后的文本转节点列表
    """
    nodes=[]
    for line in content.splitlines():
        line=line.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        nodes.append(line)
    return nodes

# ====================== 主程序 ======================
def main():
    config = load_config()
    subs = config.get("subscriptions",[]).get("v2rayN", [])
    print(f"加载订阅数量: {len(subs)}")
    all_nodes=[]
    for sub in subs:
        name = sub.get("name","unknown")
        url = sub.get("url")
        if not url:
            continue
        print("\n==============================")
        print(f"订阅: {name}")
        print(f"地址: {url}")
        try:
            r=requests.get(url,timeout=TIMEOUT,headers={"User-Agent":"v2rayN"})
            r.raise_for_status()
            # Base64解码
            decoded = smart_decode(r.text)
            nodes=parse_nodes(decoded)
            print(f"解码后节点数量: {len(nodes)}")
            all_nodes.extend(nodes)
        except Exception as e:
            print(f"获取失败: {e}")
            time.sleep(1)
    print("\n==============================")
    all_count = len(all_nodes)
    print(f"全部合并节点数量: {all_count}")

    print("\n===============正在去重===============")
    # 整行去重
    all_nodes = list(dict.fromkeys(all_nodes))
    done_count = len(all_nodes)
    print(f"去重后节点数量: {done_count} , 删除重复节点: {all_count-done_count}")
    Path("out").mkdir(exist_ok=True)
    Path(OUTPUT_RAW).write_text("\n".join(all_nodes),encoding="utf-8")
    print(f"输出文件: {OUTPUT_RAW}")

if __name__ == "__main__":
    main()