"""RAG 最小模块：读取文本文件、切块、TF-IDF 检索。

只支持 .md 和 .txt。PDF / Word 留到后续迭代。
"""

SUPPORTED_SUFFIXES = {".md", ".txt"}
import os
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def chunk_text(text, chunk_size=220, overlap=40):

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start: end]
        start = end - overlap
        
        if not chunk.strip():
            continue
        
        chunks.append(chunk)

    return chunks
    """把全文切成带重叠的块，返回字符串列表。"""

def load_chunks(path, chunk_size=220, overlap=40):
    suffix = os.path.splitext(path)[1]
    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError("不支持该文件格式，仅支持 .md和 .txt")
    
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    text_pieces = chunk_text(text, chunk_size, overlap)

    chunks = []
    for count, piece in enumerate(text_pieces, start=1):
        item = {
                "id": f"chunk-{count:03d}",
                "source": os.path.basename(path),
                "text": piece,
            }   
        chunks.append(item)
    return chunks

    """读取文档，返回含 id、source、text 的字典列表。"""

def retrieve(query, chunks, top_k=3, min_score=0.1):
    if not chunks:
        return []
    texts = [item["text"] for item in chunks]

    vectorizer = TfidfVectorizer(
        analyzer="char",
        ngram_range=(2,3),
    )
    X_chunks = vectorizer.fit_transform(texts)
    X_query = vectorizer.transform([query])
    scores = cosine_similarity(X_query, X_chunks)[0]
    order = np.argsort(scores)[::-1]
    out = []
    if scores[order[0]] < min_score:
        return []
    else:
        for idx in order[:top_k]:
            out.append (
                {
                    "id": chunks[idx]['id'],
                    "score": round(float(scores[idx]),4),
                    "text": texts[idx],
                }
            )
    return out
    """返回 Top-K 字典，至少包含 id、text、score。

    Top-1 分数低于 min_score 时返回空列表。
    """
   
def format_context(hits):
    blocks = []
    for hit in hits:
        block = f"[{hit['id']}]\n{hit['text']}"
        blocks.append(block)
    return "\n\n".join(blocks)
    """把检索结果拼成交给提示词的资料文本。"""
 
