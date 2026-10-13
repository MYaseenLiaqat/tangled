"""Retrieval + grounded answering. Chroma and the embedding model load lazily."""
from collections import defaultdict
from ..config import settings
from . import llm

_ef = None
_col = None
REFUSAL = "I can only answer from your course materials, and I could not find this in them. Try rephrasing, or ask your instructor."
SYSTEM = ("You are a course tutor. Answer ONLY from the numbered course excerpts. Cite sources like [1]. "
          "If the excerpts do not contain the answer, say so. Be concise and explain step by step.")


def ef():
    global _ef
    if _ef is None:
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction  # ONNX MiniLM, no torch
        _ef = DefaultEmbeddingFunction()
    return _ef


def col():
    global _col
    if _col is None:
        import chromadb
        _col = chromadb.PersistentClient(path=settings.chroma_dir).get_or_create_collection(
            "materials", embedding_function=ef(), metadata={"hnsw:space": "cosine"})
    return _col


def retrieve(q: str, k: int = 4) -> list[dict]:
    c = col()
    if c.count() == 0:
        return []
    r = c.query(query_texts=[q], n_results=min(k, c.count()))
    return [{"text": d, "meta": m, "sim": 1 - x} for d, m, x in zip(r["documents"][0], r["metadatas"][0], r["distances"][0])]


def topic_of(hits: list[dict]) -> str | None:
    """Topic = the course concept the retrieved passages belong to (weighted by similarity)."""
    if not hits or hits[0]["sim"] < settings.min_similarity:
        return None
    w: dict[str, float] = defaultdict(float)
    for h in hits:
        if h["meta"].get("concept"):
            w[h["meta"]["concept"]] += h["sim"]
    return max(w, key=w.get) if w else None


async def answer(q: str, hits: list[dict]) -> tuple[str, list[dict]]:
    if not hits or hits[0]["sim"] < settings.min_similarity:
        return REFUSAL, []  # grounded refusal: saves a model call and prevents made-up answers
    ctx = "\n\n".join(f"[{i+1}] ({h['meta'].get('material')}, {h['meta'].get('section')})\n{h['text']}" for i, h in enumerate(hits))
    text = await llm.chat([{"role": "system", "content": SYSTEM},
                           {"role": "user", "content": f"Course excerpts:\n{ctx}\n\nStudent question: {q}"}])
    return text, [{"n": i + 1, "material": h["meta"].get("material"), "section": h["meta"].get("section")} for i, h in enumerate(hits)]
