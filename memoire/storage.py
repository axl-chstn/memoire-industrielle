"""Espaces locaux transactionnels et sauvegardes JSON portables, sans service distant."""

from __future__ import annotations

import json
import os
import re
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from memoire.documents import Document, Page
from memoire.knowledge import FIELDS, Fact, Record, evidence_valid

SPACES = ("Atelier fictif", "Mes documents")
MAX_BACKUP_BYTES = 100 * 1024 * 1024
FORMAT = "memoire-industrielle-espace"


class StorageError(ValueError):
    pass


class ConflictError(StorageError):
    pass


@dataclass
class Snapshot:
    workspace: str
    documents: dict[str, Document]
    overrides: dict[str, Record]
    revision: int = 0


def encode(snapshot: Snapshot) -> bytes:
    data = {"format": FORMAT, "version": 1, "workspace": snapshot.workspace,
            "documents": [asdict(d) for d in snapshot.documents.values()],
            "overrides": [asdict(r) for r in snapshot.overrides.values()]}
    result = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    if len(result) > MAX_BACKUP_BYTES:
        raise StorageError("Cet espace dépasse la limite de sauvegarde de 100 Mo.")
    return result


def _string(value, *, limit=100_000, empty=False):
    if not isinstance(value, str) or len(value) > limit or (not empty and not value.strip()):
        raise StorageError("Une valeur de la sauvegarde est absente ou trop longue.")
    return value


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise StorageError("La sauvegarde contient des champs en double.")
        result[key] = value
    return result


def decode(data: bytes, *, imported=False) -> Snapshot:
    """Valide tout avant mutation ; un export restauré ne vaut pas validation humaine."""
    if not data or len(data) > MAX_BACKUP_BYTES:
        raise StorageError("Sauvegarde vide ou supérieure à 100 Mo.")
    try:
        raw = json.loads(data.decode("utf-8-sig"), object_pairs_hook=_unique_object)
        if (raw["format"] != FORMAT or type(raw["version"]) is not int
                or raw["version"] != 1 or raw["workspace"] not in SPACES):
            raise StorageError("Format, version ou espace de sauvegarde non reconnu.")
        docs, overrides = raw["documents"], raw["overrides"]
        if not isinstance(docs, list) or len(docs) > 100 or not isinstance(overrides, list):
            raise StorageError("Limite : 100 documents par espace.")
        if len(overrides) > len(docs):
            raise StorageError("Trop de fiches dans la sauvegarde.")
        documents = {}
        official = {}
        if raw["workspace"] == "Atelier fictif":
            from memoire.demo import load_workshop

            official = {d.id: d for d in load_workshop()}
        for entry in docs:
            identity = _string(entry["id"], limit=64)
            name = _string(entry["name"], limit=255)
            if not re.fullmatch(r"[a-f0-9]{64}", identity) or identity in documents:
                raise StorageError("Identifiant de document invalide ou dupliqué.")
            if "/" in name or "\\" in name or name in {".", ".."}:
                raise StorageError("Nom de document invalide.")
            pages = entry["pages"]
            warnings = entry["warnings"]
            if not isinstance(pages, list) or not 1 <= len(pages) <= 100:
                raise StorageError("Chaque document doit contenir de 1 à 100 pages.")
            if not isinstance(warnings, list) or len(warnings) > 100:
                raise StorageError("Liste d'avertissements invalide.")
            if type(entry["demo"]) is not bool:
                raise StorageError("Type de document invalide.")
            document = Document(identity, name,
                tuple(Page(_string(p["label"], limit=100),
                           _string(p["text"], limit=10 * 1024 * 1024)) for p in pages),
                tuple(_string(w, limit=1000) for w in warnings), entry["demo"])
            if len({p.label for p in document.pages}) != len(document.pages):
                raise StorageError("Les pages doivent avoir des repères distincts.")
            if official or raw["workspace"] == "Atelier fictif":
                if official.get(identity) != document:
                    raise StorageError("Ce document ne correspond pas au scénario fictif officiel.")
            elif document.demo:
                raise StorageError("Un rapport personnel ne peut pas être déclaré fictif contrôlé.")
            documents[identity] = document
        records = {}
        for entry in overrides:
            identity = entry["document_id"]
            if identity not in documents or identity in records or not isinstance(entry["facts"], dict):
                raise StorageError("Fiche sans document ou dupliquée.")
            if not set(entry["facts"]) <= FIELDS.keys() or type(entry["validated"]) is not bool:
                raise StorageError("Champs de fiche invalides.")
            facts = {k: Fact(_string(f["value"]), _string(f["page"], limit=100),
                             _string(f["quote"], limit=10 * 1024 * 1024))
                     for k, f in entry["facts"].items()}
            if not all(evidence_valid(documents[identity], fact) for fact in facts.values()):
                raise StorageError("Une fiche contient une valeur sans extrait justificatif exact.")
            if entry["validated"] and not facts:
                raise StorageError("Une fiche vide ne peut pas être validée.")
            records[identity] = Record(identity, _string(entry["report"], limit=1000), facts,
                entry["validated"], _string(entry["origin"], limit=200))
        if imported:
            from memoire.knowledge import extract_record

            # Même une fiche absente de l'export reçoit un état à vérifier.
            records = {key: replace(records.get(key) or extract_record(doc),
                validated=False, origin="Sauvegarde restaurée · à vérifier")
                for key, doc in documents.items()}
        return Snapshot(raw["workspace"], documents, records)
    except StorageError:
        raise
    except (ValueError, TypeError, KeyError, AttributeError, RecursionError) as exc:
        raise StorageError("Sauvegarde JSON invalide ou incomplète.") from exc


def merge(current: Snapshot, restored: Snapshot) -> tuple[Snapshot, int, int]:
    """Ajoute uniquement les documents absents ; les fiches existantes restent intactes."""
    if current.workspace != restored.workspace:
        raise StorageError("Choisis l'espace indiqué dans la sauvegarde avant de la restaurer.")
    additions = {k: d for k, d in restored.documents.items() if k not in current.documents}
    if len(current.documents) + len(additions) > 100:
        raise StorageError("La fusion dépasserait 100 documents ; aucun document n'a été ajouté.")
    documents = {**current.documents, **additions}
    records = {**current.overrides,
               **{k: r for k, r in restored.overrides.items() if k in additions}}
    return (Snapshot(current.workspace, documents, records, current.revision),
            len(additions), len(restored.documents) - len(additions))


class WorkspaceStore:
    def __init__(self, directory: Path | None = None):
        default = Path(__file__).resolve().parents[1] / "data" / "private"
        self.directory = Path(directory or os.environ.get("MEMOIRE_DATA_DIR", default))
        self.path = self.directory / "espaces.sqlite3"

    @contextmanager
    def _connect(self):
        connection = None
        try:
            self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
            connection = sqlite3.connect(self.path, timeout=5)
            self.path.chmod(0o600)
            connection.execute("CREATE TABLE IF NOT EXISTS spaces "
                "(name TEXT PRIMARY KEY, revision INTEGER NOT NULL, payload BLOB NOT NULL)")
            with connection:
                yield connection
        except (OSError, sqlite3.Error) as exc:
            raise StorageError("Le stockage local est inaccessible. Vérifie le dossier data/private.") from exc
        finally:
            if connection is not None:
                connection.close()

    def load(self, workspace: str, defaults: dict[str, Document] | None = None) -> Snapshot:
        if workspace not in SPACES:
            raise StorageError("Espace inconnu.")
        try:
            with self._connect() as connection:
                row = connection.execute("SELECT revision, payload FROM spaces WHERE name = ?",
                                         (workspace,)).fetchone()
            if row is None:
                return Snapshot(workspace, dict(defaults or {}), {})
            snapshot = decode(row[1])
            if snapshot.workspace != workspace:
                raise StorageError("L'espace enregistré ne correspond pas à son nom.")
            snapshot.revision = row[0]
            return snapshot
        except sqlite3.Error as exc:
            raise StorageError("Le stockage local est illisible. Il est conservé sans modification.") from exc

    def save(self, snapshot: Snapshot) -> int:
        payload = encode(snapshot)
        decode(payload)  # Les mêmes règles s'appliquent aux écritures et aux restaurations.
        try:
            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute("SELECT revision FROM spaces WHERE name = ?",
                                         (snapshot.workspace,)).fetchone()
                revision = row[0] if row else 0
                if revision != snapshot.revision:
                    raise ConflictError("Cet espace a changé dans un autre onglet. La version enregistrée a été rechargée ; recommence ta modification.")
                connection.execute("INSERT OR REPLACE INTO spaces VALUES (?, ?, ?)",
                    (snapshot.workspace, revision + 1, payload))
            return revision + 1
        except sqlite3.Error as exc:
            raise StorageError("Échec de la sauvegarde locale. La version précédente est conservée.") from exc
