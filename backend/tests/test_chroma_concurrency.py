"""Regression: parallel upload jobs on a fresh server must not race while building the Chroma client.

Before the fix, the first multi-file upload after a restart failed some files with
KeyError(<chroma dir>) or "'RustBindingsAPI' object has no attribute 'bindings'".
"""
import threading
from app.adapters import chroma
from app.config import settings


def test_parallel_vector_store_construction_is_safe(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "chroma_dir", str(tmp_path / "chroma"))
    errors: list[str] = []
    barrier = threading.Barrier(8)

    def build():
        barrier.wait()
        try:
            chroma.ChromaVectorStore().count()
        except Exception as exc:  # collect, so the assertion shows every failure
            errors.append(f"{type(exc).__name__}: {exc}")

    threads = [threading.Thread(target=build) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []
