# Super PPT 部署说明

**当前公网应用**：
[https://super-ppt-kpcvhtoahtitynwunugtvw.streamlit.app/](https://super-ppt-kpcvhtoahtitynwunugtvw.streamlit.app/)

## 本地运行

```powershell
cd D:\ai-learning\super-ppt
python -m pip install -r requirements.txt
$env:DEEPSEEK_API_KEY = "sk-你的Key"
python -m streamlit run app.py
```

浏览器打开终端显示的地址，通常为 `http://localhost:8501`。

## Streamlit Community Cloud

### 1. 推送代码

项目需要已经推送到 GitHub。入口文件为：

```text
app.py
```

### 2. 创建应用

1. 登录 `share.streamlit.io`；
2. 选择 **New app**；
3. 选择 GitHub 仓库 `Suziqing0v0/super-ppt`；
4. 分支选择 `main`；
5. Main file path 填写 `app.py`；
6. 打开 **Advanced settings → Secrets**。

### 3. 配置 Secret

```toml
DEEPSEEK_API_KEY = "sk-你的真实Key"
```

不要把真实 Key 写入仓库、README 或 `.streamlit/secrets.toml` 后提交。

### 4. 部署后验收

- 页面能打开；
- 普通主题能生成并下载 `.pptx`；
- 上传 `.md` 后能生成；
- 评测分数和来源正常显示；
- 无资料主题能明确拒绝；
- 日志中不出现真实 Key。

## 本地 Secrets 文件

如果不想每次设置环境变量，可以复制：

```text
.streamlit/secrets.toml.example
→ .streamlit/secrets.toml
```

再把示例 Key 替换为真实 Key。`secrets.toml` 已被 `.gitignore` 排除。

## 已知部署限制

- Community Cloud 空闲应用可能休眠，首次访问需要等待启动；
- DeepSeek API 依赖网络，可能受限流或余额影响；
- 当前没有用户登录和配额控制，不适合直接公开给大量陌生用户；
- 上传文档只在单次请求的临时目录中处理，不构成持久知识库；
- TF-IDF 检索不能可靠理解同义表达；
- 自动评测只检查结构和来源，不保证事实完全正确。
