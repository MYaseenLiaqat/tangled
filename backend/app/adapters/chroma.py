from ..config import settings


class ChromaVectorStore:
    def __init__(self):
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        import chromadb
        self.collection = chromadb.PersistentClient(path=settings.chroma_dir).get_or_create_collection(
            "materials", embedding_function=DefaultEmbeddingFunction(), metadata={"hnsw:space": "cosine"})

    def add(self, ids, documents, embeddings, metadatas):
        self.collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

    def query(self, query, limit):
        count = self.count()
        if not count:
            return []
        result = self.collection.query(query_texts=[query], n_results=min(limit, count))
        return [{"text": d, "meta": m, "sim": 1 - x}
                for d, m, x in zip(result["documents"][0], result["metadatas"][0], result["distances"][0])]

    def delete_by_material(self, material_id):
        self.collection.delete(where={"material_id": material_id})

    def count(self):
        return self.collection.count()
