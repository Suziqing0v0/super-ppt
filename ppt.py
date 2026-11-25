import os
import json
from openai import OpenAI
from pptx import Presentation
import sys
from layout_clf import classify_layout
import argparse
import rag
from evaluate import evaluate_outline

#argparse 读取 topic / --doc
parser = argparse.ArgumentParser()
parser.add_argument("topic")
parser.add_argument("--doc")
args = parser.parse_args()
topic = args.topic
doc_path = args.doc

#检查 DEEPSEEK_API_KEY 并创建 client
if "DEEPSEEK_API_KEY" not in os.environ:
    print("没有找到 DEEPSEEK_API_KEY 环境变量。")
    print("请先设置它（见 README 的「怎么设 Key」一节）。")
    sys.exit()

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
)

#判断是否提供文档，生成 context / allowed_sources
context = ""
allowed_sources = []

if doc_path is not None:
    chunks = rag.load_chunks(doc_path)
    hits = rag.retrieve(topic, chunks, top_k=3)

    if not hits:
        print("文档中没有找到足够相关的资料，停止生成。")
        sys.exit(1)

    context = rag.format_context(hits)
    allowed_sources = [hit["id"] for hit in hits]

#定义两种 prompt
if doc_path is None:
    general_system_prompt = """你是 PPT 大纲助手。
只输出一个 JSON 对象，键名必须完全一致：
{
    "标题": "……",
    "副标题": "……",
    "页": [
        {
            "类型": "标题页",
            "标题": "……",
            "要点": ["……"],
            "来源": []
        },
        {
            "类型": "要点页",
            "标题": "……",
            "要点": ["……", "……"],
            "来源": []
        },
        {
            "类型": "总结页",
            "标题": "……",
            "要点": ["……"],
            "来源": []
        }
    ]
}
"类型"只能是"标题页"/"要点页"/"总结页"。
只输出 JSON，不要解释，不要代码块标记。"""
else:
    rag_system_prompt = """你是 PPT 大纲助手。
只输出一个 JSON 对象，键名必须完全一致：
{
    "标题": "……",
    "副标题": "……",
    "页": [
        {
            "类型": "标题页",
            "标题": "……",
            "要点": ["……"],
            "来源": ["chunk-xxx"]
        },
        {
            "类型": "要点页",
            "标题": "……",
            "要点": ["……", "……"],
            "来源": ["chunk-xxx"]
        },
        {
            "类型": "总结页",
            "标题": "……",
            "要点": ["……"],
            "来源": ["chunk-xxx"]
        }
    ]
}
"类型"只能是"标题页"/"要点页"/"总结页"。
你只能使用用户消息中提供的检索资料，不得补造事实、数字或引文。
每页必须填写"来源"，来源只能从用户消息中的允许来源 ID 中选择。
资料不足时，应在要点中写"资料未提供"，不能自行补充。
只输出 JSON，不要解释，不要代码块标记。"""

LAYOUTS = {"标题页": 0, "要点页": 1, "总结页": 2}

#定义 build_messages
def build_messages(topic, doc_path, context, allowed_sources):
    if doc_path is None:
        system_prompt = general_system_prompt
        user_prompt = (
            f"主题：{topic}\n"
            "听众：大三物理系学生\n"
            "请生成 5 页大纲。"
        )
    else:
        system_prompt = rag_system_prompt
        user_prompt = (
            f"主题：{topic}\n"
            "听众：大三物理系学生\n"
            f"允许使用的来源：{allowed_sources}\n\n"
            f"检索资料：\n{context}\n\n"
            "请生成 5 页大纲。"
        )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

# ===== 第一半：让模型写大纲 =====

# 定义 ask_llm
def ask_llm(topic, doc_path, context, allowed_sources):
    messages = build_messages(
        topic,
        doc_path,
        context,
        allowed_sources,
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
    )
    return response.choices[0].message.content

# 调用 ask_llm
outline = None
eval_report = None
expected = {
    "max_points_per_page": 4,
    "max_chars_per_point": 80,
}
eval_allowed_sources = set(allowed_sources) if doc_path is not None else None

for attempt in range(2):
    text = ask_llm(topic, doc_path, context, allowed_sources)

    try:
        candidate = json.loads(text)
    except json.JSONDecodeError:
        print(f"第 {attempt + 1} 次 JSON 格式错误，重试")
        continue

    report = evaluate_outline(candidate, expected, eval_allowed_sources)
    if not report["passed"]:
        messages = "; ".join(issue["message"] for issue in report["issues"])
        print(f"第 {attempt + 1} 次评测未通过：{messages}")
        continue

    outline = candidate
    eval_report = report
    break

# ===== 第二半：照着大纲画文件 =====
if outline is None:
    print("两次 都没成功，先停下")
else:
    total = len(outline["页"])
    prs = Presentation()

    for i, page in enumerate(outline["页"], start=1):
        sources = page.get("来源", [])
        print(f"第 {i} 页来源：{sources}")
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
    outline_name = f"{topic}.outline.json"
    with open(outline_name, "w", encoding="utf-8") as f:
        json.dump(outline, f, ensure_ascii=False, indent=2)
    eval_name = f"{topic}.eval.json"
    with open(eval_name, "w", encoding="utf-8") as f:
        json.dump(eval_report, f, ensure_ascii=False, indent=2)
    print(
        f"评测：passed={eval_report['passed']} "
        f"score={eval_report['score']} "
        f"issues={len(eval_report['issues'])}"
    )
    print(f"已生成 {out_name}，共 {len(outline['页'])} 页")




