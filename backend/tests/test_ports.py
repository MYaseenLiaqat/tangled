from pathlib import Path
from app.adapters.files import LocalFileStorage


class MemoryVectorStore:
    def __init__(self):
        self.items = {}

    def add(self, ids, documents, embeddings, metadatas):
        self.items.update(dict(zip(ids, zip(documents, metadatas))))

    def query(self, course_id, query, limit):
        self.items = {key: value for key, value in self.items.items() if value[1].get("course_id") == course_id}
        return [{"text": text, "meta": meta, "sim": 1.0} for text, meta in list(self.items.values())[:limit]]

    def delete_by_material(self, course_id, material_id):
        self.items = {key: value for key, value in self.items.items()
                      if not (value[1].get("course_id") == course_id and value[1].get("material_id") == material_id)}

    def delete_by_course(self, course_id):
        self.items = {key: value for key, value in self.items.items() if value[1].get("course_id") != course_id}

    def count(self):
        return len(self.items)


def test_vector_store_interface():
    store = MemoryVectorStore()
    store.add(["1"], ["text"], [[1.0]], [{"course_id": 2, "material_id": 3}])
    assert store.count() == 1 and store.query(2, "text", 1)[0]["text"] == "text"
    assert store.query(99, "text", 1) == []
    store.delete_by_material(2, 3)
    assert store.count() == 0


def test_file_storage_interface(tmp_path: Path):
    storage = LocalFileStorage(str(tmp_path))
    storage.save("material.txt", b"content")
    with storage.open("material.txt") as file:
        assert file.read() == b"content"
    storage.delete("material.txt")
    assert not (tmp_path / "material.txt").exists()


def test_jobs_interface():
    calls = []

    class MemoryJobs:
        def enqueue(self, function, *args, **kwargs):
            calls.append(function(*args, **kwargs))

    MemoryJobs().enqueue(lambda value: value + 1, 1)
    assert calls == [2]
