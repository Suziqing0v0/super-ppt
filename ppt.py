"""Super PPT 命令行入口。"""

import argparse
import sys

from generator import generate_presentation


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("topic")
    parser.add_argument("--doc")
    args = parser.parse_args()

    try:
        result = generate_presentation(
            args.topic,
            doc_path=args.doc,
        )
    except (ValueError, RuntimeError, OSError) as error:
        print(f"生成失败：{error}")
        return 1

    for page in result["page_results"]:
        print(f"第 {page['page']} 页来源：{page['sources']}")
        print(
            f"第 {page['page']} 页「{page['title']}」："
            f"模型={page['model_type']}  分类器={page['layout']}"
        )

    report = result["eval_report"]
    print(
        f"评测：passed={report['passed']} "
        f"score={report['score']} "
        f"issues={len(report['issues'])}"
    )
    print(f"已生成 {result['pptx_path']}")
    print(f"大纲：{result['outline_path']}")
    print(f"评测：{result['eval_path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
