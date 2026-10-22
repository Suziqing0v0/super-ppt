# Super PPT

输入一个主题，自动生成一份 5 页的 PPT 文件。

## 怎么装

需要 Python 3.10 以上。

```
pip install -r requirements.txt
```

## 怎么设 Key

1. 到 `platform.deepseek.com` 注册，创建一个 API Key
2. 把它存进名为 `DEEPSEEK_API_KEY` 的环境变量

Windows（PowerShell，只对当前窗口有效）：

```
$env:DEEPSEEK_API_KEY = "sk-你的Key"
```

想永久保存（新开窗口也有效）：

```
setx DEEPSEEK_API_KEY "sk-你的Key"
```

macOS / Linux：

```
export DEEPSEEK_API_KEY="sk-你的Key"
```

Key 只放在环境变量里，不要写进代码，也不要提交到 Git。

## 怎么用

```
python ppt.py "给大三学生讲什么是伪随机数"
```

输出：

```
已生成 给大三学生讲什么是伪随机数.pptx，共 5 页
```

生成的文件用 PowerPoint 或 WPS 打开即可。

## 已知限制

- 主题里带 `\ / : * ? " < > |` 这些字符时，文件名存不下来
- 内容是模型生成的，可能有事实错误，也可能出现"主讲人：XXX"这类占位符
