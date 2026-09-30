"""
Milvus 向量库封装（pymilvus）

集合字段设计（对应 5.3.2）：
- pk:        主键（自增）
- vector:    BGE-M3 稠密向量（1024 维）
- doc_type:  知识类别（regulation 监管规则 / penalty 处罚案例 / announcement 历史公告）
- title:     标题
- source:    发文机关
- content:   文本块
"""
import uuid
from typing import Any

from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections, utility

from app.config import settings

DIM = 1024  # BGE-M3 向量维度


class MilvusStore:
    """Milvus 向量库操作类：集合管理、写入、向量检索"""

    def __init__(self, alias: str = "default"):
        self.alias = alias
        self.collection_name = settings.MILVUS_COLLECTION
        self._collection: Collection | None = None

    def connect(self):
        connections.connect(alias=self.alias, host=settings.MILVUS_HOST, port=settings.MILVUS_PORT)

    @property
    def collection(self) -> Collection:
        if self._collection is None:
            self.connect()
            if not utility.has_collection(self.collection_name, using=self.alias):
                self._create_collection()
            self._collection = Collection(self.collection_name, using=self.alias)
            self._collection.load()
        return self._collection

    def _create_collection(self):
        fields = [
            FieldSchema(name="pk", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=DIM),
            FieldSchema(name="doc_type", dtype=DataType.VARCHAR, max_length=32),
            FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=4096),
        ]
        schema = CollectionSchema(fields, description="监管知识库向量集合")
        collection = Collection(self.collection_name, schema, using=self.alias)
        # HNSW 索引：高召回近似最近邻检索
        index = {"index_type": "HNSW", "metric_type": "COSINE", "params": {"M": 16, "efConstruction": 200}}
        collection.create_index("vector", index)

    def insert(self, vectors: list[list[float]], doc_type: str, title: str,
               source: str, contents: list[str]) -> list[str]:
        """批量写入向量与元数据，返回主键列表"""
        pks = [str(uuid.uuid4()) for _ in vectors]
        data = [pks, vectors, [doc_type] * len(vectors), [title] * len(vectors),
                [source] * len(vectors), contents]
        self.collection.insert(data)
        self.collection.flush()
        return pks

    def delete_by_title(self, title: str) -> None:
        self.collection.delete(f'title == "{title}"')

    def search(self, query_vector: list[float], top_k: int = 5,
               doc_type: str | None = None) -> list[dict[str, Any]]:
        """向量相似度检索，返回命中列表（含相似度分数）"""
        expr = f'doc_type == "{doc_type}"' if doc_type else None
        results = self.collection.search(
            data=[query_vector],
            anns_field="vector",
            param={"metric_type": "COSINE", "params": {"ef": 64}},
            limit=top_k,
            expr=expr,
            output_fields=["doc_type", "title", "source", "content"],
        )
        hits = []
        for r in results[0]:
            hits.append({
                "pk": r.id,
                "score": float(r.score),
                "doc_type": r.entity.get("doc_type"),
                "title": r.entity.get("title"),
                "source": r.entity.get("source"),
                "content": r.entity.get("content"),
            })
        return hits


milvus_store = MilvusStore()
