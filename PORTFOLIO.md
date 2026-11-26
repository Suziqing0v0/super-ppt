# Super PPT 作品集

## 一句话介绍

根据主题或指定文档，自动生成带每页来源和自动质量检查的 PowerPoint。

## 解决的问题

普通“主题生成 PPT”工具容易出现内容空泛、资料不可追溯和页面结构失控。
Super PPT 在生成流程中加入文档检索、来源限制和质量评测，让输出更容易检查。

## 主要功能

- 输入主题生成普通 PPT；
- 上传 Markdown/TXT 后按文档内容生成；
- 使用字符级 TF-IDF 检索相关段落；
- 每页标注实际使用的 chunk 来源；
- 自动检查页数、空页、要点数量、字符长度和来源；
- 下载 `.pptx`、大纲 JSON 和评测 JSON；
- 支持命令行的同时提供 Streamlit Web 界面。

## 技术结构

```text
Streamlit / CLI
→ generator.py
→ rag.py（文档切块与检索）
→ DeepSeek API（JSON 大纲）
→ evaluate.py（自动评测）
→ python-pptx（渲染）
→ pptx / outline.json / eval.json
```

## 关键工程决策

- 使用 JSON 约束模型输出结构；
- 将检索与生成分离，先鉴定资料是否足够；
- 不把词表 ID 当向量，使用 TF-IDF 和余弦相似度；
- 严重结构错误阻止生成，质量警告只扣分；
- 评测报告独立保存，避免只依赖终端输出；
- 把生成核心抽成函数，供 CLI 和 Web 共用。

## 验证结果

- 样例文档成功切成 6 个带重叠的块；
- 卡诺问题 Top-1 来源为 `chunk-005`；
- 无资料问题在调用模型前停止；
- RAG 实际生成 5 页 PPT；
- 正常样例自动评测 `score=100`；
- 异常样例能发现标题为空、空页、5 个要点、超长要点和非法来源；
- UI 的输入校验、成功页和三个下载按钮已通过自动化测试。

## 当前限制

- 只支持 Markdown/TXT 文档；
- TF-IDF 对同义表达和跨段推理能力有限；
- 只取 Top-3 片段；
- 自动评测不能替代事实核验和人工审阅；
- 公网部署需要账号配置和 API 成本控制。

## 运行

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

部署步骤见 `DEPLOYMENT.md`。
