# 版式分类器：给一页（第几页 + 标题），返回它该用哪种版式
import numpy as np
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

decks = [
    ("伪随机数", ["计算机没有骰子", "种子决定一切", "常见生成器", "线性同余法"]),
    ("贝叶斯定理", ["先验与后验", "似然函数", "经典例子"]),
    ("梯度下降", ["损失函数", "学习率", "收敛过程"]),
    ("决策树", ["信息增益", "分裂规则", "剪枝"]),
    ("聚类", ["K 怎么选", "中心点", "无监督的特点"]),
    ("神经网络", ["神经元", "激活函数", "反向传播"]),
    ("电动力学", ["麦克斯韦方程组", "电磁波", "边界条件", "矢量势"]),
    ("短视频脚本", ["前三秒抓人", "钩子怎么写", "节奏控制", "结尾引导"]),
    ("RAG", ["文档切分", "向量检索", "上下文拼接"]),
]

# ===== 训练（模块被导入时做一次）=====
titles, pages, labels, is_last = [], [], [], []
# ← 用 day74 那套循环，把三个列表填满
for name,points in decks:
    titles.append(name)
    pages.append(1)
    labels.append("标题页")
    is_last.append(0)
    for i,p in enumerate(points,start=2):
        titles.append(p)
        pages.append(i)
        labels.append("要点页")
        is_last.append(0)
    titles.append("总结与回顾")
    pages.append(len(points)+2)
    labels.append("总结页")
    is_last.append(1)

vec = TfidfVectorizer(analyzer="char", ngram_range=(1, 2))
Xtxt = vec.fit_transform(titles)
Xpage = np.array(pages, dtype=float).reshape(-1, 1)
Xlast = np.array(is_last, dtype=float).reshape(-1, 1)

model = LogisticRegression(max_iter=2000).fit(
    hstack([Xtxt, Xpage, Xlast]).tocsr(), labels
)

def classify_layout(page_no, title,is_last):
    x_txt = vec.transform([title])              # ← 注意是 transform
    x_num = np.array([[float(page_no),float(is_last)]])
    return model.predict(hstack([x_txt, x_num]).tocsr())[0]

