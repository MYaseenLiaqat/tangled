import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/t.db"
os.environ["JWT_SECRET"] = "test-secret-that-is-at-least-32-bytes"
