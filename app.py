"""Super PPT Streamlit 界面。"""

import os
import tempfile

import streamlit as st

from generator import generate_presentation


def configure_api_key():
    if os.environ.get("DEEPSEEK_API_KEY"):
        return

    try:
        secret_key = st.secrets.get("DEEPSEEK_API_KEY")
    except Exception:
        return

    if secret_key:
        os.environ["DEEPSEEK_API_KEY"] = secret_key


configure_api_key()

st.set_page_config(
    page_title="Super PPT",
    page_icon="📽️",
    layout="wide",
)

st.title("Super PPT")
st.caption("输入主题，可选上传 Markdown/TXT 资料，生成带来源和自动评测的 PPT。")

with st.sidebar:
    st.header("生成设置")
    topic = st.text_input(
        "PPT 主题",
        placeholder="例如：给大一学生讲牛顿第二定律",
    )
    use_doc = st.checkbox("使用 Markdown/TXT 文档")
    uploaded_file = None
    if use_doc:
        uploaded_file = st.file_uploader(
            "上传资料",
            type=["md", "txt"],
        )

    generate_clicked = st.button(
        "生成 PPT",
        type="primary",
        width="stretch",
    )


def run_generation(topic_value, uploaded):
    with tempfile.TemporaryDirectory() as work_dir:
        doc_path = None
        if uploaded is not None:
            doc_path = os.path.join(
                work_dir,
                os.path.basename(uploaded.name),
            )
            with open(doc_path, "wb") as file:
                file.write(uploaded.getvalue())

        output_dir = os.path.join(work_dir, "output")
        result = generate_presentation(
            topic_value,
            doc_path=doc_path,
            output_dir=output_dir,
        )

        with open(result["pptx_path"], "rb") as file:
            pptx_bytes = file.read()
        with open(result["outline_path"], "r", encoding="utf-8") as file:
            outline_text = file.read()
        with open(result["eval_path"], "r", encoding="utf-8") as file:
            eval_text = file.read()

        return {
            "pptx_bytes": pptx_bytes,
            "outline_text": outline_text,
            "eval_text": eval_text,
            "outline": result["outline"],
            "eval_report": result["eval_report"],
            "page_results": result["page_results"],
            "pptx_name": os.path.basename(result["pptx_path"]),
            "outline_name": os.path.basename(result["outline_path"]),
            "eval_name": os.path.basename(result["eval_path"]),
        }


if generate_clicked:
    st.session_state.pop("generation_result", None)

    if not topic.strip():
        st.warning("请先输入 PPT 主题。")
    elif use_doc and uploaded_file is None:
        st.warning("已选择文档模式，请上传 .md 或 .txt 文件。")
    else:
        try:
            configure_api_key()
            with st.spinner("正在检索资料、生成大纲并评测……"):
                st.session_state["generation_result"] = run_generation(
                    topic,
                    uploaded_file,
                )
        except Exception as error:
            st.error(f"生成失败：{error}")


result = st.session_state.get("generation_result")
if result is not None:
    report = result["eval_report"]

    st.subheader("生成结果")
    metric_cols = st.columns(4)
    metric_cols[0].metric("评测分数", report["score"])
    metric_cols[1].metric("页数", report["metrics"]["page_count"])
    metric_cols[2].metric("问题数", len(report["issues"]))
    metric_cols[3].metric(
        "状态",
        "通过" if report["passed"] else "未通过",
    )

    st.download_button(
        "下载 PPT",
        data=result["pptx_bytes"],
        file_name=result["pptx_name"],
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        type="primary",
    )

    download_cols = st.columns(2)
    download_cols[0].download_button(
        "下载大纲 JSON",
        data=result["outline_text"],
        file_name=result["outline_name"],
        mime="application/json",
    )
    download_cols[1].download_button(
        "下载评测 JSON",
        data=result["eval_text"],
        file_name=result["eval_name"],
        mime="application/json",
    )

    st.subheader("页面与来源")
    st.dataframe(
        result["page_results"],
        width="stretch",
        hide_index=True,
    )

    if report["issues"]:
        st.subheader("评测问题")
        for issue in report["issues"]:
            message = (
                f"第 {issue['page']} 页：{issue['message']}"
                if issue["page"] is not None
                else issue["message"]
            )
            if issue["severity"] == "error":
                st.error(message)
            else:
                st.warning(message)
    else:
        st.success("自动评测未发现问题。")

    with st.expander("查看大纲 JSON"):
        st.code(result["outline_text"], language="json")

    with st.expander("查看评测 JSON"):
        st.code(result["eval_text"], language="json")
