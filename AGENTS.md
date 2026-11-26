# Super PPT 项目记忆与多智能体交接

## 1. 文件定位与优先级

- **用途**：用于多智能体（OpenCode、Claude Code、Antigravity 等）跨会话、跨工具交接，在新会话启动时快速恢复项目状态、接口契约与协作规范。
- **信息优先级**：`用户当前明确要求 > 本文件 > 历史文档 / 旧 handoff`。
- **最后更新**：`2026-11-26`
- **当前阶段**：第 20 周本地部分已完成；Streamlit Web 应用、三类下载、部署文档和作品集均已落地。**公网部署仍等待用户登录 Streamlit Community Cloud，因此第 20 周尚未完整通过。**
- **Git 基线**：`main` 分支，HEAD `0a5e855`（`第20周：Streamlit 界面、生成重构与部署文档`）。

---

## 2. 项目概况与关联仓库

**Super PPT** 是从第 8 周起持续迭代的贯穿项目：输入一个主题（可选附带参考文档），自动生成 5 页教学用 PPT。

- **两种运行模式**：
  - **主题模式**：直接基于 `topic` 调用 DeepSeek 生成 5 页 JSON 大纲并渲染为 `.pptx`。
  - **RAG 文档模式**（`--doc`）：先对 `.md` / `.txt` 文档切块并做字符级 TF-IDF 检索（Top-3），再将检索片段与允许的 `chunk-xxx` ID 传给 DeepSeek 生成带来源的大纲，若未命中（Top-1 相似度 < `0.1`）则停止生成。
- **三类输出文件**（已在 `.gitignore` 中忽略，默认不入库）：
  - `<主题>.pptx`：最终幻灯片文件。
  - `<主题>.outline.json`：结构化大纲（含标题、副标题、每页类型/标题/要点/来源）。
  - `<主题>.eval.json`：大纲自动评测报告（`passed`、`score`、`metrics`、`issues`）。
- **关联课程仓库**：`C:\Users\15503\Desktop\opencode\ai-learning`
  - `progress.md`：第 1–20 周课程及 Super PPT 里程碑勾选状态。
  - `学习日志.md`：每周实验数值、错题与概念验收记录。
  - `.claude\handoffs\2026-11-15-context-memory.md`：课程长期教学记忆与历史基线。

---

## 3. 代码结构与核心接口

### 项目文件清单（`D:\ai-learning\super-ppt`）

| 文件 | 角色 | 关键说明 |
|---|---|---|
| `app.py` | Streamlit Web 界面 | 输入主题、上传文档、生成、展示评测和三个下载按钮 |
| `ppt.py` | 命令行入口 | 解析 CLI 参数并调用 `generator.generate_presentation` |
| `generator.py` | 可复用生成核心 | RAG、DeepSeek、评测、渲染、保存三类输出 |
| `rag.py` | 轻量本地 RAG | 读取 `.md` / `.txt`，滑窗切块 + 字符 TF-IDF 检索 + 上下文拼接 |
| `evaluate.py` | 自动规则评测 | 检查大纲结构、页数、页面类型、空页、要点数量/长度及 RAG 来源合法性 |
| `layout_clf.py` | 版式分类器 | 导入时用内置 9 个示例大纲训练 `LogisticRegression` |
| `hello_llm.py` / `outline.py` | 早期练习脚本 | 第 8 周保留的历史原型脚本，非当前主流程入口 |
| `DEPLOYMENT.md` / `PORTFOLIO.md` | 部署与作品集 | Cloud 部署步骤、Secret 配置、项目说明和限制 |
| `README.md` / `requirements.txt` / `.gitignore` | 文档与配置 | `.gitignore` 忽略真实 Secret 和所有生成产物 |

### 核心接口契约

1. **`rag.py`**
   - `chunk_text(text, chunk_size=220, overlap=40) -> list[str]`
   - `load_chunks(path, chunk_size=220, overlap=40) -> list[dict]`：仅支持 `.md` / `.txt`，每项含 `id`（`chunk-001` 起）、`source`、`text`。
   - `retrieve(query, chunks, top_k=3, min_score=0.1) -> list[dict]`：字符 2–3 gram TF-IDF + 余弦相似度；Top-1 `< min_score` 返回 `[]`，否则返回含 `id`、`score`、`text` 的 Top-K 列表。
   - `format_context(hits) -> str`：格式化为 `[chunk-xxx]\n<text>` 拼接块。

2. **`evaluate.py`**
   - `EXPECTED_PAGE_COUNT = 5`，`VALID_PAGE_TYPES = {"标题页", "要点页", "总结页"}`。
   - `evaluate_outline(outline, expected=None, allowed_sources=None) -> dict`：
     - `expected` 默认读取 `max_points_per_page=4`、`max_chars_per_point=80`。
     - `allowed_sources` 为 `None` 时跳过来源校验；非 `None` 时每页必须存在非空 `"来源"` 且全部属于 `allowed_sources`。
     - 返回 `{"passed": bool, "score": int, "metrics": {...}, "issues": [...]}`；存在任意 `severity == "error"` 时 `passed` 为 `False`（阻断渲染），`warning` 仅扣分不阻断。

3. **`generator.py`**
   - `generate_presentation(topic, doc_path=None, output_dir=None) -> dict`
   - 返回 `pptx_path`、`outline_path`、`eval_path`、`outline`、`eval_report`、`page_results`。

4. **`layout_clf.py`**
   - `classify_layout(page_no, title, is_last) -> str`：输入页码、页标题、`is_last` 标志，返回 `"标题页"`、`"要点页"` 或 `"总结页"`（`ppt.py` 映射到 `LAYOUTS = {"标题页": 0, "要点页": 1, "总结页": 2}`）。

---

## 4. 本地环境与硬约束

- **Python 环境**：`D:\Python312\python.exe`（Python `3.12.10`）。
- **核心依赖**（`requirements.txt`）：`openai`、`python-pptx`、`scikit-learn`、`streamlit`。
- **环境变量**：
  - `DEEPSEEK_API_KEY`：必须通过环境变量读取，**严禁写入代码或提交到 Git**。
  - `PYTHONUTF8=1`
  - `OPENBLAS_NUM_THREADS=1`、`OMP_NUM_THREADS=1`（防止 Windows 下 OpenBLAS 内存分配失败）。
- **API 约束**：本机 `api.openai.com` 不可达，统一使用 DeepSeek 的 OpenAI 兼容接口（`base_url="https://api.deepseek.com"`，`model="deepseek-chat"`）。
- **目录约束**：保持 `C:\Users\15503\Desktop\opencode\ai-learning` 与 `D:\ai-learning\super-ppt` 当前双仓库结构，**不要主动迁移 C 盘课程目录**。

---

## 5. 多智能体协作与教学规范

用户是物理学（师范）大三学生，目标是掌握实用的 AI 工程能力（“能做出别人能用、而且知道质量好不好的 AI 工具”）。各智能体协作时必须遵守：

1. **交互直达对话**：所有需要用户阅读、理解或动手做的内容直接写在对话中，不要只扔给用户看任务卡（`weekNN.md` 等仅作助手侧存档）。
2. **代码讲解不跳步**：给出新代码时，在代码块下方附带逐行/逐段解释，说明做什么、为什么这样写及输入输出结构。
3. **引导为主、不越俎代庖**：核心逻辑（循环、数据拼接、接口设计、业务流程）由用户练习完成；除非用户明确说“给答案”，否则按“提问 → 指位置 → 指错误类型 → 给类似例子”引导，不直接替写完整核心实现。
4. **不擅自代跑代码**：平时让用户自己运行并观察输出；仅当用户说“看一下”或明确要求验证时才主动读取最新保存文件并运行报告真实结果（注意排查 VS Code 未保存情况）。
5. **收尾检查**：提交或推送 `super-ppt` 与 `ai-learning` 前，核对是否混入 API Key、`.pptx` / `.eval.json` 等生成产物或临时文件，再完成周总结与里程碑同步。

---

## 6. 当前路线与已知问题

### 第 20 周实施路线

| 阶段 | 目标 | 关键交付 | 状态 |
|---|---|---|---|
| Day 100 | Streamlit 基础输入界面（不调 API） | `ai-learning\homework\week20\day100_streamlit_basics.py` | 通过 |
| Day 101 | 抽离核心生成逻辑 | `generator.py` + CLI 薄入口 | 通过 |
| Day 102 | Streamlit 接入与下载 | `app.py` | 通过，真实网页生成 `score=100` |
| Day 103 | 部署说明与作品集 | 依赖、README、`DEPLOYMENT.md`、`PORTFOLIO.md` | 本地部分完成；公网部署待用户操作 |

### 当前已知小问题（后续按需修复）

1. `evaluate.py` 对顶层 `"标题"`、`"副标题"` 仅校验键存在，未校验是否为空字符串/纯空白。
2. `evaluate.py` 当某页 `"要点"` 不是 `list` 时直接 `continue`，会跳过该页的 RAG `"来源"` 校验。
3. `evaluate.py` 未检查 5 页的页面类型组合合理性（例如全为 `"要点页"` 也能通过）。
4. `ppt.py` 在 `passed=True` 但存在 `warning` 时，终端只打印 `issues=<数量>`，未直接打印每条警告内容。
5. `ppt.py` 最多重试 2 次，第 2 次重试时未将第 1 次失败的 `issues` 反馈给模型。
6. 输出文件名已通过 `generator.safe_filename` 替换非法字符。
7. 当前没有用户登录、调用配额和公网 API 滥用保护，不适合直接开放给大量陌生用户。

---

## 7. 维护约定

- 每完成一个周里程碑、核心模块接口变更（如新增 `generator.py`、`app.py`）或依赖变化后，交接或结束会话前须同步更新本文件的**当前阶段、Git 基线、代码结构表与待办状态**，避免后续智能体依据过期状态工作。
