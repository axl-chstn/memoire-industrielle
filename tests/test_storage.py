import json
from dataclasses import replace

import pytest

from memoire.demo import load_workshop
from memoire.documents import read_document
from memoire.knowledge import Fact, correct_fact, extract_record, validate_record
from memoire.storage import (
    ConflictError,
    Snapshot,
    StorageError,
    WorkspaceStore,
    decode,
    encode,
    merge,
)


@pytest.fixture
def personal():
    document = read_document("rapport.md", "Incident : INC900\nÉquipement : P01\nIntervention : Inspection\nRésultat : Inconnu".encode())
    record = validate_record(extract_record(document), document)
    return Snapshot("Mes documents", {document.id: document}, {document.id: record})


def test_restart_keeps_text_pages_and_human_validation(tmp_path, personal):
    store = WorkspaceStore(tmp_path)
    assert store.save(personal) == 1
    restored = WorkspaceStore(tmp_path).load("Mes documents")
    assert restored.documents == personal.documents
    assert restored.overrides == personal.overrides
    assert restored.revision == 1
    assert store.path.stat().st_mode & 0o777 == 0o600


def test_empty_space_stays_empty_after_restart(tmp_path):
    store = WorkspaceStore(tmp_path)
    store.save(Snapshot("Atelier fictif", {}, {}))
    defaults = {d.id: d for d in load_workshop()}
    assert not store.load("Atelier fictif", defaults).documents


def test_spaces_are_independent(tmp_path, personal):
    store = WorkspaceStore(tmp_path)
    store.save(personal)
    assert not store.load("Atelier fictif").documents
    store.save(Snapshot("Atelier fictif", {}, {}))
    assert store.load("Mes documents").documents == personal.documents


def test_stale_tab_cannot_overwrite_a_new_validation(tmp_path, personal):
    first, second = WorkspaceStore(tmp_path), WorkspaceStore(tmp_path)
    stale = second.load("Mes documents")
    first.save(personal)
    with pytest.raises(ConflictError, match="autre onglet"):
        second.save(stale)
    assert first.load("Mes documents").overrides == personal.overrides


def test_invalid_edit_keeps_previous_saved_version(tmp_path, personal):
    store = WorkspaceStore(tmp_path)
    personal.revision = store.save(personal)
    identity = next(iter(personal.documents))
    bad = replace(personal.overrides[identity], facts={"action": Fact("Inventée", "Texte", "Inventée")})
    with pytest.raises(StorageError, match="justificatif"):
        store.save(replace(personal, overrides={identity: bad}))
    assert store.load("Mes documents").overrides == personal.overrides
    assert store.load("Mes documents").revision == 1


def test_corrupt_database_is_not_replaced(tmp_path):
    path = tmp_path / "espaces.sqlite3"
    original = b"fichier endommage a conserver"
    path.write_bytes(original)
    with pytest.raises(StorageError):
        WorkspaceStore(tmp_path).load("Mes documents")
    assert path.read_bytes() == original


def test_backup_restores_corrections_with_new_review_required(personal):
    identity = next(iter(personal.documents))
    document = personal.documents[identity]
    changed = correct_fact(personal.overrides[identity], document, "outcome", "", "Texte", "")
    personal.overrides[identity] = validate_record(changed, document)
    restored = decode(encode(personal), imported=True)
    assert restored.documents == personal.documents
    assert restored.overrides[identity].facts == personal.overrides[identity].facts
    assert "outcome" not in restored.overrides[identity].facts
    assert not restored.overrides[identity].validated
    assert "à vérifier" in restored.overrides[identity].origin


def test_missing_record_in_external_backup_does_not_bypass_review():
    document = load_workshop()[0]
    restored = decode(encode(Snapshot("Atelier fictif", {document.id: document}, {})), imported=True)
    assert not restored.overrides[document.id].validated


def test_merge_is_additive_and_keeps_existing_corrections(personal):
    restored = decode(encode(personal), imported=True)
    empty = Snapshot("Mes documents", {}, {})
    combined, added, duplicates = merge(empty, restored)
    assert (added, duplicates) == (1, 0)
    assert combined.documents == personal.documents
    combined, added, duplicates = merge(personal, restored)
    assert (added, duplicates) == (0, 1)
    assert combined.overrides == personal.overrides
    with pytest.raises(StorageError, match="Choisis l'espace"):
        merge(Snapshot("Atelier fictif", {}, {}), restored)


@pytest.mark.parametrize("mutation", [
    lambda raw: raw.update(version=2),
    lambda raw: raw["documents"][0].update(name="../../rapport.md"),
    lambda raw: raw["documents"][0].update(demo=True),
    lambda raw: raw["documents"][0].update(pages=[]),
    lambda raw: raw["documents"].append(raw["documents"][0]),
    lambda raw: raw["overrides"][0]["facts"]["action"].update(value="Valeur inventée"),
    lambda raw: raw["overrides"][0].update(document_id="absent"),
    lambda raw: raw.update(workspace="Atelier fictif"),
])
def test_invalid_backup_is_rejected_before_merge(personal, mutation):
    raw = json.loads(encode(personal))
    mutation(raw)
    with pytest.raises(StorageError):
        decode(json.dumps(raw).encode(), imported=True)


@pytest.mark.parametrize("data", [b"", b"[]", b"null", b"{", b'\xff', b'{"version":1,"version":2}'])
def test_malformed_json_is_rejected(data):
    with pytest.raises(StorageError):
        decode(data)
