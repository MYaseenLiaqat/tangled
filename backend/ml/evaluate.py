"""python -m ml.evaluate data/gold.csv
Compares the 'any follow-up' baseline with embeddings + logistic regression (5-fold CV),
picks a threshold for the target precision, and saves the model for INTENT_BACKEND=logreg."""
import csv, sys
import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, precision_recall_curve, precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from app.config import settings
from app.services import rag

TARGET_PRECISION = 0.85
rows = [r for r in csv.DictReader(open(sys.argv[1], encoding="utf-8")) if r["label"]]
X = np.array(rag.ef()([r["text"] for r in rows]), dtype=float)
y = np.array([r["label"] for r in rows])


def report(name, pred):
    p, r, f, _ = precision_recall_fscore_support(y == "confusion", pred == "confusion", average="binary", zero_division=0)
    print(f"{name:32s} precision={p:.2f} recall={r:.2f} f1={f:.2f}")


report("baseline: any follow-up", np.where(np.array([int(r["turn"]) for r in rows]) > 1, "confusion", "information"))
clf = LogisticRegression(max_iter=1000, class_weight="balanced")
proba = cross_val_predict(clf, X, y, cv=StratifiedKFold(5, shuffle=True, random_state=0), method="predict_proba")
classes = sorted(set(y))
pred = np.array(classes)[proba.argmax(1)]
report("embeddings + logistic regression", pred)
print(classes); print(confusion_matrix(y, pred, labels=classes))
prec, _, th = precision_recall_curve(y == "confusion", proba[:, classes.index("confusion")])
ok = [t for p, t in zip(prec[:-1], th) if p >= TARGET_PRECISION]
thr = min(ok) if ok else 0.5
print(f"Threshold for precision >= {TARGET_PRECISION}: {thr:.2f}" + ("" if ok else "  (target not reachable; collect more labels)"))
clf.fit(X, y)
joblib.dump({"clf": clf, "threshold": float(thr)}, settings.intent_model_path)
