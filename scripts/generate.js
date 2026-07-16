import fs from "fs";
import yaml from "yaml";
import axios from "axios";


const config =
    yaml.parse(
        fs.readFileSync(
            "./config/subscriptions.yaml",
            "utf8"
        ));


let nodes=[];



async function download(url){

    let r =
        await axios.get(
            url,
            {
                timeout:30000,
                headers:{
                    "User-Agent":"clash"
                }
            }
        );

    return r.data;
}



function decode(data){

    try{

        let text =
            Buffer.from(
                data,
                "base64"
            ).toString("utf8");


        if(text.includes("://"))
            return text;


    }catch(e){}


    return data;
}



async function main(){


    for(
        let sub of config.subscriptions
        ){

        console.log(
            "download",
            sub.name
        );


        let data =
            await download(
                sub.url
            );


        let text =
            decode(data);


        nodes.push(text);

    }



    fs.mkdirSync(
        "./out",
        {
            recursive:true
        }
    );


    fs.writeFileSync(

        "./out/all.txt",

        nodes.join("\n"),

        "utf8"

    );


    console.log(
        "done"
    );

}


main();