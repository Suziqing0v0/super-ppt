"""Super PPT 可复用生成核心。"""

import json
import os

from openai import OpenAI
from pptx import Presentation

from evaluate import evaluate_outline
from layout_clf import classify_layout
import rag

MODEL_NAME = "deepseek-chat"
LAYOUTS = {"标题页": 0, "要点页": 1, "总结页": 2}
INVALID_FILENAME_CHARS = set('\\/:*?"<>|')

GENERAL_SYSTEM_PROMPT = """你是 PPT 大纲助手。
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
每页最多 4 个要点，每条要点不超过 80 个字符。
只输出 JSON，不要解释，不要代码块标记。"""

RAG_SYSTEM_PROMPT = """你是 PPT 大纲助手。
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
每页最多 4 个要点，每条要点不超过 80 个字符。
资料不足时，应在要点中写"资料未提供"，不能自行补充。
只输出 JSON，不要解释，不要代码块标记。"""


def build_messages(topic, doc_path, context, allowed_sources):
    if doc_path is None:
        system_prompt = GENERAL_SYSTEM_PROMPT
        user_prompt = (
            f"主题：{topic}\n"
            "听众：大三物理系学生\n"
            "请生成 5 页大纲。"
        )
    else:
        system_prompt = RAG_SYSTEM_PROMPT
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


def ask_llm(client, topic, doc_path, context, allowed_sources):
    messages = build_messages(
        topic,
        doc_path,
        context,
        allowed_sources,
    )
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
    )
    return response.choices[0].message.content


def safe_filename(topic):
    name = "".join(
        "_" if char in INVALID_FILENAME_CHARS else char
        for char in topic
    ).strip(" .")
    return name[:80] or "super-ppt"


def generate_presentation(topic, doc_path=None, output_dir=None):
    topic = topic.strip()
    if not topic:
        raise ValueError("PPT 主题不能为空")

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("没有找到 DEEPSEEK_API_KEY 环境变量")

    output_dir = os.path.abspath(output_dir or os.getcwd())
    os.makedirs(output_dir, exist_ok=True)

    context = ""
    allowed_sources = []

    if doc_path is not None:
        chunks = rag.load_chunks(doc_path)
        hits = rag.retrieve(topic, chunks, top_k=3)

        if not hits:
            raise ValueError("文档中没有找到足够相关的资料")

        context = rag.format_context(hits)
        allowed_sources = [hit["id"] for hit in hits]

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )

    expected = {
        "max_points_per_page": 4,
        "max_chars_per_point": 80,
    }
    eval_allowed_sources = set(allowed_sources) if doc_path else None

    outline = None
    eval_report = None
    last_errors = []

    for _ in range(2):
        text = ask_llm(
            client,
            topic,
            doc_path,
            context,
            allowed_sources,
        )

        try:
            candidate = json.loads(text)
        except json.JSONDecodeError:
            last_errors = ["模型没有返回有效 JSON"]
            continue

        report = evaluate_outline(
            candidate,
            expected,
            eval_allowed_sources,
        )
        if not report["passed"]:
            last_errors = [
                issue["message"]
                for issue in report["issues"]
                if issue["severity"] == "error"
            ]
            continue

        outline = candidate
        eval_report = report
        break

    if outline is None:
        detail = "；".join(last_errors) or "未知错误"
        raise RuntimeError(f"两次生成都没有通过评测：{detail}")

    file_stem = safe_filename(topic)
    pptx_path = os.path.join(output_dir, f"{file_stem}.pptx")
    outline_path = os.path.join(output_dir, f"{file_stem}.outline.json")
    eval_path = os.path.join(output_dir, f"{file_stem}.eval.json")

    total = len(outline["页"])
    prs = Presentation()
    page_results = []

    for page_no, page in enumerate(outline["页"], start=1):
        is_last = page_no == total
        predicted = classify_layout(page_no, page["标题"], is_last)
        page_results.append({
            "page": page_no,
            "title": page["标题"],
            "model_type": page["类型"],
            "layout": predicted,
            "sources": page.get("来源", []),
        })

        layout = prs.slide_layouts[LAYOUTS.get(predicted, 1)]
        slide = prs.slides.add_slide(layout)
        slide.shapes.title.text = page["标题"]

        text_frame = slide.placeholders[1].text_frame
        if page["要点"]:
            text_frame.text = page["要点"][0]
            for point in page["要点"][1:]:
                text_frame.add_paragraph().text = point

    prs.save(pptx_path)

    with open(outline_path, "w", encoding="utf-8") as file:
        json.dump(outline, file, ensure_ascii=False, indent=2)
    with open(eval_path, "w", encoding="utf-8") as file:
        json.dump(eval_report, file, ensure_ascii=False, indent=2)

    return {
        "pptx_path": pptx_path,
        "outline_path": outline_path,
        "eval_path": eval_path,
        "outline": outline,
        "eval_report": eval_report,
        "page_results": page_results,
    }
