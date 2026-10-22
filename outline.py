import os
import json
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
)

def ask_llm(topic):
    response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
    {"role":"system","content":system_prompt},
    {"role":"user","content":f"主题:{topic}\n请生成5页大纲。"},
],
)
    text = response.choices[0].message.content
    return text

system_prompt = """你是PPT大纲助手。
只输出一个JSON对象，键名一个字都不能改:
{
    "标题":"……",
    "副标题":"……",
    "页":[
        {"类型":"要点页","标题":"……","要点":["……","……"]},
        {"类型":"总结页","标题":"……","要点":["……"]}
    ]
}
"类型"只能是"标题页"/"要点页"/"总结页"之一。
只输出 JSON 本身，不要解释，不要代码块标记。"""

topic = "给大三学生讲什么是伪随机数"

outline = None
for attempt in range(2):
    text = ask_llm(topic)
    try:
        outline = json.loads(text)
        break
    except json.JSONDecodeError:
        print(f"第{attempt + 1}次格式不对，重试……")

if outline is None:
    print("两次都没成功，先停下")
else:
    for i,page in enumerate(outline["页"]):
        print(f"第{i+1}页[{page['类型']}]:{page['标题']}({len(page['要点'])}个要点)")


