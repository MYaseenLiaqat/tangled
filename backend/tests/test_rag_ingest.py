import json

import pytest

from app.services.ingest import _nb


def test_notebook_rejects_invalid_cell_structure(tmp_path):
    path = tmp_path / "invalid.ipynb"
    path.write_text(json.dumps({"cells": [{"source": "not a valid cell"}]}), encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid notebook cell"):
        _nb(path)


def test_notebook_accepts_markdown_and_code_cells(tmp_path):
    path = tmp_path / "valid.ipynb"
    path.write_text(json.dumps({
        "cells": [
            {"cell_type": "markdown", "source": ["Known fact."]},
            {"cell_type": "code", "source": "value = 1"},
        ],
    }), encoding="utf-8")

    assert _nb(path) == [
        ("cell 1", "Known fact."),
        ("cell 2", "value = 1"),
    ]
