from pathlib import Path
from ..config import settings


class LocalFileStorage:
    def __init__(self, root: str | None = None):
        self.root = Path(root or settings.upload_dir)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, name, data):
        path = self.root / name
        path.write_bytes(data)
        return path

    def open(self, name):
        return (self.root / name).open("rb")

    def delete(self, name):
        (self.root / name).unlink(missing_ok=True)
