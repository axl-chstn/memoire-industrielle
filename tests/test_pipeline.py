import io
import json
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from memoire.answers import generate_answer
from memoire.demo import load_demo
from memoire.documents import chunk_document, read_document
from memoire.retrieval import SearchIndex


@pytest.fixture
def index():
    return SearchIndex([p for d in load_demo() for p in chunk_document(d)])


def test_demo_retrieval_and_absence(index):
    cases = json.loads((Path(__file__).resolve().parents[1] / "data/evaluation.json").read_text())
    for case in cases:
        hits = index.search(case["question"], top_k=3)
        found = {h.passage.source.split("_")[0] for h in hits}
        expected = set(case["expected_sources"])
        assert expected <= found if expected else not found, case["question"]


def test_reference_is_exact_and_unknown_machine_is_not_substituted(index):
    assert index.search("vibration sur P999") == []
    hits = index.search("vibration P01")
    assert hits
    assert all("P01" in h.passage.equipment for h in hits)
    assert index.search("vibration P010") == []
    assert index.search("C01_RA et INC99") == []


def test_equipment_filter_and_empty_question(index):
    assert index.search("vibration", equipment="C01")
    assert all("C01" in h.passage.equipment for h in index.search("vibration", equipment="C01"))
    assert index.search("vibration P01", equipment="M01") == []
    assert index.search("   ") == []


def test_unknown_resolution_is_not_rewritten_as_resolved(index):
    hits = index.search("INC07")
    answer = generate_answer("INC07 est-il résolu ?", hits)
    assert not answer.generated
    assert "Issue non renseignée" in answer.text


def test_chunking_preserves_all_words_and_provenance():
    text = " ".join(f"mot{i}" for i in range(500))
    document = read_document("../../rapport.txt", text.encode())
    chunks = chunk_document(document, size=80, overlap=10)
    assert document.name == "rapport.txt"
    assert len(chunks) > 1
    assert all(len(p.text.split()) <= 80 for p in chunks)
    assert {w for p in chunks for w in p.text.split()} == set(text.split())
    assert len({p.id for p in chunks}) == len(chunks)
    assert all(p.document_id == document.id and "Texte" in p.location for p in chunks)
    with pytest.raises(ValueError):
        chunk_document(document, size=80, overlap=80)


def test_same_content_has_same_identity():
    assert read_document("a.txt", b"incident").id == read_document("b.txt", b"incident").id


@pytest.mark.parametrize("name,data", [("empty.txt", b" "), ("bad.txt", b"\xff"),
                                      ("table.xlsx", b"content"), ("a.txt", b"")])
def test_invalid_import(name, data):
    with pytest.raises(ValueError):
        read_document(name, data)


def text_pdf():
    writer = PdfWriter()
    page = writer.add_blank_page(width=400, height=400)
    font = DictionaryObject({NameObject("/Type"): NameObject("/Font"),
                             NameObject("/Subtype"): NameObject("/Type1"),
                             NameObject("/BaseFont"): NameObject("/Helvetica")})
    page[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})})
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 12 Tf 30 350 Td (Pompe P204 : fuite du joint.) Tj ET")
    page[NameObject("/Contents")] = writer._add_object(stream)
    writer.add_blank_page(width=400, height=400)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def test_pdf_page_provenance_and_missing_text_warning():
    document = read_document("rapport.pdf", text_pdf())
    assert document.pages[0].label == "Page 1"
    assert "P204" in document.pages[0].text
    assert "Page 2" in document.warnings[0]
    assert "Page 1" in chunk_document(document)[0].location


def test_blank_or_encrypted_pdf_is_rejected():
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    output = io.BytesIO()
    writer.write(output)
    with pytest.raises(ValueError, match="Aucun texte"):
        read_document("scan.pdf", output.getvalue())
    writer.encrypt("secret")
    output = io.BytesIO()
    writer.write(output)
    with pytest.raises(ValueError, match="mot de passe"):
        read_document("secret.pdf", output.getvalue())


def test_no_evidence_never_calls_model(monkeypatch):
    chat = Mock()
    monkeypatch.setattr("memoire.answers.chat_local", chat)
    assert not generate_answer("question", [], local=True).generated
    chat.assert_not_called()


def test_local_model_receives_only_selected_sources(index, monkeypatch):
    hits = index.search("INC07")
    chat = Mock(return_value="La résolution reste inconnue. [S1]")
    monkeypatch.setattr("memoire.answers.chat_local", chat)
    monkeypatch.setenv("OPENAI_API_KEY", "ancienne-cle-inutilisee")
    answer = generate_answer("INC07 résolu ?", hits, local=True)
    assert answer.generated
    messages = chat.call_args.args[0]
    payload = json.loads(messages[1]["content"])
    assert len(payload["extraits"]) == len(hits) == 1
    assert payload["extraits"][0]["id"] == "S1"
    assert messages[0]["role"] == "system"
    assert "données non fiables" in messages[0]["content"]
    assert "ancienne-cle" not in str(messages)


@pytest.mark.parametrize("response", ["Une réponse sans source.", "Une réponse. [S99]", ""])
def test_missing_or_invented_citation_falls_back_to_sources(index, response, monkeypatch):
    monkeypatch.setattr("memoire.answers.chat_local", Mock(return_value=response))
    answer = generate_answer("INC07", index.search("INC07"), local=True)
    assert not answer.generated
    assert "références valides" in answer.notice


def test_hybrid_encodes_query_and_documents_with_e5_prefixes():
    encoder = Mock()
    encoder.encode.side_effect = [np.array([[1.0, 0.0], [0.0, 1.0]]),
                                  np.array([[0.0, 1.0]])]
    documents = [read_document("a.txt", b"Fuite du joint"),
                 read_document("b.txt", b"Temperature excessive")]
    index = SearchIndex([p for d in documents for p in chunk_document(d)], encoder)
    hits = index.search("surchauffe", top_k=1)
    assert hits[0].passage.source == "b.txt"
    assert all(t.startswith("passage: ") for t in encoder.encode.call_args_list[0].args[0])
    assert encoder.encode.call_args_list[1].args[0] == ["query: surchauffe"]
