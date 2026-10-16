"""Import en mémoire, découpage et provenance des passages."""

from __future__ import annotations

import hashlib
import io
import re
from dataclasses import dataclass
from pathlib import PurePosixPath

MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_PAGES = 100
REFERENCE_RE = re.compile(r"\b[A-Z]{1,4}[-_]?\d{1,5}(?:_[A-Z]{1,6})?\b", re.I)


def references(text: str) -> set[str]:
    return {m.group().upper() for m in REFERENCE_RE.finditer(text)}


def equipment_ids(text: str) -> tuple[str, ...]:
    return tuple(sorted({r.split("_")[0] for r in references(text)
                         if re.match(r"^(?:P|M|C|EQ)[-]?\d", r)}))


@dataclass(frozen=True)
class Page:
    label: str
    text: str


@dataclass(frozen=True)
class Document:
    id: str
    name: str
    pages: tuple[Page, ...]
    warnings: tuple[str, ...] = ()
    demo: bool = False

    @property
    def equipment(self) -> tuple[str, ...]:
        return equipment_ids(" ".join(p.text for p in self.pages))


@dataclass(frozen=True)
class Passage:
    id: str
    document_id: str
    source: str
    location: str
    text: str
    equipment: tuple[str, ...]


def read_document(name: str, data: bytes, *, demo: bool = False) -> Document:
    """Ne persiste jamais le contenu d'un document sur disque."""
    safe_name = PurePosixPath(name.replace("\\", "/")).name
    if not data or len(data) > MAX_FILE_BYTES:
        raise ValueError("Le fichier doit contenir entre 1 octet et 10 Mo.")
    extension = PurePosixPath(safe_name).suffix.lower()
    warnings: list[str] = []
    pages: list[Page] = []
    if extension == ".pdf":
        from pypdf import PdfReader

        try:
            reader = PdfReader(io.BytesIO(data))
            if reader.is_encrypted and not reader.decrypt(""):
                raise ValueError("Ce PDF est protégé par un mot de passe.")
            if len(reader.pages) > MAX_PAGES:
                raise ValueError("Limite de la maquette : 100 pages par PDF.")
            for number, page in enumerate(reader.pages, 1):
                text = (page.extract_text() or "").strip()
                if text:
                    pages.append(Page(f"Page {number}", text))
                else:
                    warnings.append(f"Page {number} sans texte exploitable ; OCR non inclus.")
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError("PDF illisible ou endommagé.") from exc
    elif extension in {".txt", ".md"}:
        try:
            text = data.decode("utf-8-sig").strip()
        except UnicodeDecodeError as exc:
            raise ValueError("Enregistre le texte en UTF-8 avant de l'importer.") from exc
        pages.append(Page("Texte", text))
    else:
        raise ValueError("Formats acceptés : PDF, TXT et Markdown.")
    if not any(p.text.strip() for p in pages):
        raise ValueError("Aucun texte exploitable. Un PDF scanné nécessite un OCR préalable.")
    return Document(hashlib.sha256(data).hexdigest(), safe_name, tuple(pages),
                    tuple(warnings), demo)


def chunk_document(document: Document, size: int = 160, overlap: int = 30) -> list[Passage]:
    if size < 1 or not 0 <= overlap < size:
        raise ValueError("Le chevauchement doit être inférieur à la taille du passage.")
    chunks: list[Passage] = []
    for page_index, page in enumerate(document.pages):
        words = page.text.split()
        for start in range(0, len(words), size - overlap):
            text = " ".join(words[start:start + size])
            if not text:
                continue
            number = start // (size - overlap) + 1
            chunks.append(Passage(
                f"{document.id[:16]}:{page_index}:{number}", document.id,
                document.name, f"{page.label} · passage {number}", text,
                equipment_ids(text),
            ))
            if start + size >= len(words):
                break
    return chunks
