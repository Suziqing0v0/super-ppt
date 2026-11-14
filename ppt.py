import os
import json
from openai import OpenAI
from pptx import Presentation
import sys
from layout_clf import classify_layout

if len(sys.argv) < 2:
    print('用法:python ppt.py "主题"')
    sys.exit()

if "DEEPSEEK_API_KEY" not in os.environ:
    print("没有找到 DEEPSEEK_API_KEY 环境变量。")
    print("请先设置它（见 README 的「怎么设 Key」一节）。")
    sys.exit()

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
)

topic = sys.argv[1]

system_prompt = """你是PPT大hao纲助手。
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

LAYOUTS = {"标题页": 0, "要点页": 1, "总结页": 2}


def ask_llm(topic):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"主题：{topic}\n听众：大三物理系学生\n请生成 5 页大纲。"},
        ],
    )
    return response.choices[0].message.content


# ===== 第一半：让模型写大纲 =====
outline = None
for attempt in range(2):
    text = ask_llm(topic)
    try:
        outline = json.loads(text)
        break
    except json.JSONDecodeError:
        print(f"第 {attempt + 1} 次格式不对，重试……")

# ===== 第二半：照着大纲画文件 =====
if outline is None:
    print("两次 都没成功，先停下")
else:
    total = len(outline["页"])
    prs = Presentation()

    for i, page in enumerate(outline["页"], start=1):
        is_last = (i == total)
        predicted = classify_layout(i, page["标题"], is_last)
        print(f"第 {i} 页「{page['标题']}」：模型={page['类型']}  分类器={predicted}")

        layout = prs.slide_layouts[LAYOUTS.get(predicted, 1)]
        slide = prs.slides.add_slide(layout)
        slide.shapes.title.text = page["标题"] 

        tf = slide.placeholders[1].text_frame
        if page["要点"]:
            tf.text = page["要点"][0]
            for point in page["要点"][1:]:
                tf.add_paragraph().text = point

    out_name = f"{topic}.pptx"
    prs.save(out_name)
    print(f"已生成 {out_name}，共 {len(outline['页'])} 页")




