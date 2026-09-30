"""
文本嵌入模型封装（BGE-M3，经 sentence-transformers 加载，供 LangChain 使用）

BGE-M3 特点：多语言、多粒度（句/段/篇）、稠密+稀疏混合检索，适合中文监管文本。
"""
from functools import lru_cache

from langchain_core.embeddings import Embeddings


@lru_cache(maxsize=1)
def get_embedding_model(model_name: str = "BAAI/bge-m3", device: str = "cpu") -> Embeddings:
    """懒加载并缓存嵌入模型，避免每次请求重复初始化"""
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": device},
        encode_kwargs={"normalize_embeddings": True},  # 归一化，便于余弦相似度计算
    )
