# Super PPT

输入一个主题，自动生成一份 5 页 PPT。

Super PPT 支持两种模式：

- **主题模式**：根据主题自由生成大纲和 PPT；
- **RAG 文档模式**：先从 Markdown/TXT 文档中检索资料，再基于资料生成 PPT，并记录每页来源。

## 安装

需要 Python 3.10 以上。

```powershell
cd D:\ai-learning\super-ppt
python -m pip install -r requirements.txt
```

## 设置 API Key

1. 到 `platform.deepseek.com` 创建 API Key；
2. 将 Key 保存到名为 `DEEPSEEK_API_KEY` 的环境变量中。

PowerShell，只对当前窗口有效：

```powershell
$env:DEEPSEEK_API_KEY = "sk-你的Key"
```

PowerShell，永久保存：

```powershell
setx DEEPSEEK_API_KEY "sk-你的Key"
```

macOS / Linux：

```bash
export DEEPSEEK_API_KEY="sk-你的Key"
```

Key 只应保存在环境变量中，不要写进代码或提交到 Git。

## 使用

### 1. 按主题生成

```powershell
python ppt.py "给大三学生讲什么是伪随机数"
```

程序直接让 DeepSeek 生成 5 页大纲，再渲染为 PPT。

### 2. 基于文档生成

```powershell
python ppt.py "热力学第二定律" --doc "资料.md"
```

程序会：

1. 读取指定文档；
2. 切分并检索最相关的 3 个片段；
3. 将检索内容加入大纲提示词；
4. 要求每页记录实际使用的 `chunk` 来源；
5. 生成 PPT 和大纲 JSON。
6. 自动检查页数、空页、要点数量和来源，并保存评测 JSON。

查看命令行帮助：

```powershell
python ppt.py --help
```

## 输出文件

以主题“热力学第二定律”为例：

```text
热力学第二定律.pptx
热力学第二定律.outline.json
热力学第二定律.eval.json
```

- `.pptx`：可直接用 PowerPoint 或 WPS 打开；
- `.outline.json`：保留标题、副标题、每页要点和来源，便于检查内容依据。
- `.eval.json`：保存自动评测分数、指标和问题列表。

这三类生成文件默认不会提交到 Git。

## RAG 工作方式

当前版本使用轻量、可复现的本地检索：

```text
Markdown/TXT
→ 按固定窗口切块并保留重叠
→ 字符级 TF-IDF 向量
→ 余弦相似度排序
→ 取 Top-3 资料
→ 交给 DeepSeek 生成大纲
```

RAG 模式只检索用户指定的文档，不会自动联网搜索。

## 自动评测

每次生成大纲后，程序会检查：

- 页数是否为 5；
- 页面类型是否合法；
- 标题和要点是否为空；
- 每页是否超过 4 个要点；
- 单条要点是否超过 80 个字符；
- RAG 来源是否存在并属于允许的 chunk。

严重结构问题会阻止渲染并触发重试；要点过多、要点过长等质量问题只扣分并给出警告。

评测结果会保存到 `<主题>.eval.json`，包括 `passed`、`score`、各项 `metrics`
和具体 `issues`。自动评测只检查结构和来源，不判断事实内容是否足够准确。

## 项目文件

| 文件 | 作用 |
|---|---|
| `ppt.py` | 命令行入口、模型调用、PPT 与大纲渲染 |
| `rag.py` | 文档读取、切块、TF-IDF 检索和上下文拼接 |
| `evaluate.py` | 自动检查大纲结构、质量问题和来源 |
| `layout_clf.py` | 判断每页使用标题页、要点页或总结页 |
| `requirements.txt` | Python 依赖 |

## 已知限制

- `--doc` 当前只支持 `.md` 和 `.txt`；
- 当前检索基于字符 TF-IDF，能利用关键词重合，但不能可靠理解同义表达；
- 只检索最相关的 3 个片段，长文档可能漏掉其他相关内容；
- 模型输出仍可能出错，生成后应检查事实和来源；
- 主题中含 `\ / : * ? " < > |` 时，无法直接用作 Windows 文件名；
- 调用 DeepSeek API 需要网络，并可能产生费用。
