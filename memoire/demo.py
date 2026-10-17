"""Corpus fictif indépendant des documents importés par l'utilisateur."""

import json
from pathlib import Path

from memoire.documents import Document, read_document

DEMO_PATH = Path(__file__).resolve().parents[1] / "data" / "demo" / "rapports.json"


def load_demo() -> list[Document]:
    return [read_document(item["filename"], item["text"].encode("utf-8"), demo=True)
            for item in json.loads(DEMO_PATH.read_text(encoding="utf-8"))]


def load_workshop() -> list[Document]:
    path = DEMO_PATH.with_name("atelier_rapports.json")
    return [read_document(item["filename"], item["text"].encode("utf-8"), demo=True)
            for item in json.loads(path.read_text(encoding="utf-8"))]


def workshop_catalog() -> dict:
    return json.loads(DEMO_PATH.with_name("atelier.json").read_text(encoding="utf-8"))
