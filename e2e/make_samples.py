"""Generate sample course files for the manual end-to-end test.

Run from the repo root with the backend virtualenv:
    backend/.venv/Scripts/python e2e/make_samples.py      (Windows)
    backend/.venv/bin/python e2e/make_samples.py          (macOS/Linux)

Writes into e2e/samples/.
"""
from pathlib import Path
import json

OUT = Path(__file__).parent / "samples"
OUT.mkdir(exist_ok=True)

GRADIENT = [
    "Gradient descent is an optimisation algorithm that minimises a loss function by repeatedly moving the "
    "parameters in the direction of the negative gradient.",
    "The learning rate controls the step size. If the learning rate is too large the loss can diverge or "
    "oscillate; if it is too small, training converges very slowly.",
    "Stochastic gradient descent (SGD) estimates the gradient from one example or a mini-batch, which makes "
    "each step cheaper but noisier. Momentum averages past gradients to smooth the updates.",
]
BIAS = [
    "A model with high bias underfits: it is too simple and has high training error.",
    "A model with high variance overfits: it has low training error but high test error.",
    "Regularisation such as L2 weight decay or dropout reduces variance by penalising complex models. "
    "Cross-validation estimates generalisation error.",
]
METRICS = [
    "Precision is the fraction of predicted positives that are truly positive.",
    "Recall is the fraction of actual positives that the model finds.",
    "The F1 score is the harmonic mean of precision and recall. On imbalanced data accuracy can be "
    "misleading, because always predicting the majority class gives high accuracy.",
]


def markdown() -> None:
    text = "# Gradient descent\n\n" + "\n\n".join(GRADIENT) + "\n"
    (OUT / "01_gradient_descent.md").write_text(text, encoding="utf-8")


def docx() -> None:
    from docx import Document
    doc = Document()
    doc.add_heading("Bias and variance", level=1)
    for para in BIAS[:2]:
        doc.add_paragraph(para)
    doc.add_heading("Regularisation", level=1)
    doc.add_paragraph(BIAS[2])
    doc.save(OUT / "02_bias_variance.docx")


def pptx() -> None:
    from pptx import Presentation
    deck = Presentation()
    for title, body in [("Precision and recall", " ".join(METRICS[:2])), ("F1 and accuracy", METRICS[2])]:
        slide = deck.slides.add_slide(deck.slide_layouts[1])
        slide.shapes.title.text = title
        slide.placeholders[1].text = body
    deck.save(OUT / "03_evaluation_metrics.pptx")


def _pdf(path: Path, lines: list[str]) -> None:
    """Minimal one-page PDF with selectable Helvetica text (no external library)."""
    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    ops = ["BT", "/F1 11 Tf", "14 TL", "50 780 Td"]
    for line in lines:
        ops.append(f"({esc(line)}) Tj T*")
    ops.append("ET")
    stream = "\n".join(ops).encode("latin-1")
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    path.write_bytes(bytes(out))


def wrap(paragraphs: list[str], width: int = 90) -> list[str]:
    lines = []
    for para in paragraphs:
        cur = ""
        for word in para.split():
            if len(cur) + len(word) + 1 > width:
                lines.append(cur)
                cur = word
            else:
                cur = f"{cur} {word}".strip()
        lines += [cur, ""]
    return lines


def pdfs() -> None:
    _pdf(OUT / "04_course_summary.pdf", wrap(["Course summary"] + GRADIENT + BIAS + METRICS))
    _pdf(OUT / "bad_scanned_no_text.pdf", [])          # valid PDF, no text -> should fail to index
    (OUT / "bad_fake.pdf").write_text("this is not really a pdf", encoding="utf-8")  # rejected on upload
    (OUT / "bad_unsupported.exe").write_bytes(b"MZ\x00\x00")                        # rejected on upload


def notebook() -> None:
    nb = {"cells": [
        {"cell_type": "markdown", "metadata": {}, "source": ["# Clustering\n", "K-Means groups points around k centroids; "
                                                              "DBSCAN groups dense regions and marks noise."]},
        {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
         "source": ["from sklearn.cluster import KMeans\n", "KMeans(n_clusters=3).fit(X)"]},
    ], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}
    (OUT / "05_clustering.ipynb").write_text(json.dumps(nb, indent=1), encoding="utf-8")


def quiz() -> None:
    (OUT / "quiz_good.csv").write_text(
        "item,concept,option,count,correct\n"
        "Q1,Gradient descent,A,4,true\nQ1,Gradient descent,B,9,false\nQ1,Gradient descent,C,3,false\n"
        "Q2,Bias-variance,A,10,true\nQ2,Bias-variance,B,6,false\n"
        "Q3,Evaluation metrics,A,13,true\nQ3,Evaluation metrics,B,3,false\n"
        "Q4,Unknown topic,A,5,true\n", encoding="utf-8")
    (OUT / "quiz_bad_headers.csv").write_text("question,topic,answer,n\nQ1,Gradient descent,A,4\n", encoding="utf-8")
    (OUT / "quiz_bad_identifiers.csv").write_text(
        "item,concept,option,count,correct,email\nQ1,Gradient descent,A,4,true,a@b.c\n", encoding="utf-8")
    (OUT / "quiz_bad_rows.csv").write_text(
        "item,concept,option,count,correct\nQ1,Gradient descent,A,-3,maybe\n", encoding="utf-8")


if __name__ == "__main__":
    markdown(); docx(); pptx(); pdfs(); notebook(); quiz()
    for f in sorted(OUT.iterdir()):
        print(f"{f.stat().st_size:>7}  {f.name}")
