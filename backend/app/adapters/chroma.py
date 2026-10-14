from pathlib import Path
from ..config import settings


class ChromaVectorStore:
    def __init__(self):
        Path(settings.embedding_cache_dir).mkdir(parents=True, exist_ok=True)
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        from chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2 import ONNXMiniLM_L6_V2
        import chromadb
        ONNXMiniLM_L6_V2.DOWNLOAD_PATH = Path(settings.embedding_cache_dir) / "all-MiniLM-L6-v2"
        self.collection = chromadb.PersistentClient(path=settings.chroma_dir).get_or_create_collection(
            "materials", embedding_function=DefaultEmbeddingFunction(), metadata={"hnsw:space": "cosine"})

    def add(self, ids, documents, embeddings, metadatas):
        self.collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

    def query(self, course_id, query, limit):
        count = self.count()
        if not count:
            return []
        result = self.collection.query(query_texts=[query], n_results=min(limit, count),
                                       where={"course_id": course_id})
        return [{"text": d, "meta": m, "sim": 1 - x}
                for d, m, x in zip(result["documents"][0], result["metadatas"][0], result["distances"][0])]

    def delete_by_material(self, course_id, material_id):
        self.collection.delete(where={"$and": [{"course_id": course_id}, {"material_id": material_id}]})

    def delete_by_course(self, course_id):
        self.collection.delete(where={"course_id": course_id})

    def count(self):
        return self.collection.count()
