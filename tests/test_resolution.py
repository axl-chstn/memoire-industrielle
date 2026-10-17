from memoire.answers import generate_answer
from memoire.demo import load_demo
from memoire.documents import chunk_document
from memoire.retrieval import SearchIndex


def test_definite_unresolved_claim_is_rejected_when_report_says_unknown(monkeypatch):
    index = SearchIndex([p for d in load_demo() for p in chunk_document(d)])
    monkeypatch.setattr("memoire.answers.chat_local", lambda messages: "L'incident INC07 n'est pas résolu. [S1]")
    answer = generate_answer("INC07 est-il résolu ?", index.search("INC07"), local=True)
    assert not answer.generated
    assert "le rapport le laisse inconnu" in answer.notice


def test_unknown_response_remains_available(monkeypatch):
    index = SearchIndex([p for d in load_demo() for p in chunk_document(d)])
    monkeypatch.setattr("memoire.answers.chat_local", lambda messages: "L'état de résolution reste inconnu. [S1]")
    assert generate_answer("INC07 est-il résolu ?", index.search("INC07"), local=True).generated
