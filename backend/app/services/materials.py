from pathlib import Path
from sqlmodel import Session, select
from sqlalchemy import delete
from ..adapters.chroma import ChromaVectorStore
from ..adapters.files import LocalFileStorage
from ..db import engine
from ..models import Concept, Material
from .ingest import ingest


def process_material(material_id: int, course_id: int, path: str) -> None:
    with Session(engine) as s:
        material = s.get(Material, material_id)
        if not material:
            return
        try:
            if Path(path).suffix.lower() == ".pdf":
                from pypdf import PdfReader
                text = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages).strip()
                if len(text) < 20:
                    raise ValueError("This PDF has no selectable text. It may be a scan.")
            concepts = s.exec(select(Concept).where(Concept.course_id == course_id)).all()
            material.chunks = ingest(Path(path), course_id, material_id, concepts)
            if not material.chunks:
                raise ValueError("No readable text was found in this file.")
            material.status = "indexed"
            material.error = ""
        except Exception as exc:
            material.status = "failed"
            material.error = str(exc)[:300]
        s.add(material)
        s.commit()


def retag_course(course_id: int) -> None:
    storage = LocalFileStorage()
    with Session(engine) as s:
        concepts = s.exec(select(Concept).where(Concept.course_id == course_id)).all()
        materials = s.exec(select(Material).where(Material.course_id == course_id,
                                                  Material.status == "indexed")).all()
        if not materials:
            return
        vectors = ChromaVectorStore()
        for material in materials:
            vectors.delete_by_material(course_id, material.id)
            path = Path(storage.root) / f"{material.id}_{material.filename}"
            try:
                material.chunks = ingest(path, course_id, material.id, concepts)
            except Exception as exc:
                material.status = "failed"
                material.error = str(exc)[:300]
            s.add(material)
        s.commit()
