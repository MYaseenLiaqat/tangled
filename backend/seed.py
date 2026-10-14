"""python seed.py  ->  creates the course concepts and 24 student codes."""
from sqlmodel import Session, select
from app.db import engine, migrate
from app.models import Concept

CONCEPTS = [
    ("numpy", "NumPy arrays", "Module 1 · Unit 3", "NumPy arrays, shapes, broadcasting, axis, reshape, slicing, views and copies"),
    ("pandas_eda", "EDA with Pandas", "Module 3 · Unit 1", "Exploratory data analysis with Pandas: DataFrames, describe, plots, groupby, missing values"),
    ("neural_nets", "Neural networks", "Module 4 · Unit 3", "Perceptrons, neural networks, activation functions, backpropagation, layers and neurons"),
    ("bias_variance", "Bias–variance", "Module 4 · Unit 4", "Bias-variance tradeoff, overfitting, underfitting, training versus test error"),
    ("preprocessing", "Data preprocessing", "Module 3 · Unit 1", "Cleaning, encoding, scaling and transforming data before modelling"),
    ("gradient_descent", "Gradient descent", "Module 1 · Unit 1", "Derivatives, gradients, learning rate and optimisation by gradient descent"),
    ("eval_metrics", "Evaluation metrics", "Module 4 · Unit 4", "Accuracy, precision, recall, F1, confusion matrix, imbalanced data"),
    ("regularization", "Regularization", "Module 5 · Unit 2", "Regularization, L1 L2 penalties, dropout, learning rate tuning"),
    ("clustering", "Clustering", "Module 6 · Unit 1", "K-Means, DBSCAN and unsupervised clustering"),
]

if __name__ == "__main__":
    migrate()
    with Session(engine) as s:
        for k, n, m, d in CONCEPTS:
            if not s.exec(select(Concept).where(Concept.key == k)).first():
                s.add(Concept(key=k, name=n, module=m, description=d))
        s.commit()
    print("Seeded.")
