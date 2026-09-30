"""
混合检索器（论文 4.4.2）：向量语义检索 + 关键词 BM25 检索，加权融合

LightRAG 风格的双路召回：稠密向量负责语义相似，稀疏 BM25 负责精确术语
（如具体法规名称、处罚文号），按可配置权重融合后重排。
"""
import jieba
import math
from collections import Counter

from app.config import settings
from app.rag.embeddings import get_embedding_model
from app.rag.vector_store import milvus_store


class HybridRetriever:
    """双路混合检索：Milvus 向量检索 + BM25 关键词检索"""

    def __init__(self, corpus: list[dict] | None = None):
        # corpus: [{'title':.., 'content':.., 'doc_type':.., 'source':..}]
        self._corpus = corpus or []
        self._bm25_ready = False

    # ---------- BM25 稀疏检索 ----------
    def _tokenize(self, text: str) -> list[str]:
        return list(jieba.cut(text))

    def _build_bm25(self):
        self._docs_tokens = [self._tokenize(d["content"]) for d in self._corpus]
        df = Counter()
        for tokens in self._docs_tokens:
            df.update(set(tokens))
        n = len(self._docs_tokens)
        self._avgdl = sum(len(t) for t in self._docs_tokens) / max(n, 1)
        self._idf = {t: math.log((n - f + 0.5) / (f + 0.5) + 1) for t, f in df.items()}
        self._bm25_ready = True

    def bm25_search(self, query: str, top_k: int = 5, k1: float = 1.5, b: float = 0.75) -> list[dict]:
        if not self._bm25_ready:
            self._build_bm25()
        q_tokens = self._tokenize(query)
        scored = []
        for idx, tokens in enumerate(self._docs_tokens):
            tf = Counter(tokens)
            dl = len(tokens)
            score = sum(
                self._idf.get(t, 0) * tf.get(t, 0) * (k1 + 1) / (tf.get(t, 0) + k1 * (1 - b + b * dl / self._avgdl))
                for t in q_tokens
            )
            if score > 0:
                scored.append((idx, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        hits = []
        for idx, score in scored[:top_k]:
            doc = self._corpus[idx]
            hits.append({**doc, "score": score, "pk": None})
        return hits

    # ---------- 稠密向量检索 ----------
    def vector_search(self, query: str, top_k: int = 5, doc_type: str | None = None) -> list[dict]:
        embedder = get_embedding_model(settings.EMBEDDING_MODEL, settings.EMBEDDING_DEVICE)
        query_vector = embedder.embed_query(query)
        return milvus_store.search(query_vector, top_k=top_k, doc_type=doc_type)

    # ---------- 混合检索（加权融合 + 归一化重排） ----------
    def hybrid_search(self, query: str, top_k: int | None = None,
                      doc_type: str | None = None) -> list[dict]:
        top_k = top_k or settings.RAG_TOP_K
        w_vector = settings.RAG_VECTOR_WEIGHT

        vec_hits = self.vector_search(query, top_k=top_k * 2, doc_type=doc_type)
        kw_hits = self.bm25_search(query, top_k=top_k * 2) if self._corpus else []

        # 分数归一化到 [0,1]
        def normalize(hits: list[dict]) -> dict[str, float]:
            if not hits:
                return {}
            max_s = max(h["score"] for h in hits) or 1.0
            return {h["title"] + h["content"][:50]: h["score"] / max_s for h in hits}

        vec_norm = normalize(vec_hits)
        kw_norm = normalize(kw_hits)

        fused: dict[str, dict] = {}
        for hits, norm, w in ((vec_hits, vec_norm, w_vector), (kw_hits, kw_norm, 1 - w_vector)):
            for h in hits:
                key = h["title"] + h["content"][:50]
                if key not in fused:
                    fused[key] = {**h, "fused_score": 0.0}
                fused[key]["fused_score"] += norm.get(key, 0) * w

        results = sorted(fused.values(), key=lambda x: x["fused_score"], reverse=True)
        return results[:top_k]


hybrid_retriever = HybridRetriever()
