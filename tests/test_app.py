from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


@pytest.fixture(autouse=True)
def offline_model_status(monkeypatch):
    monkeypatch.setattr("memoire.local_llm.model_status", lambda: (False, "Modèle local absent"))


def test_demo_question_and_export_without_api_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "ancienne-cle-inutilisee")
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    assert not app.exception
    assert app.metric[0].value == "12"
    app.chat_input[0].set_value("L'incident INC07 est-il résolu ?").run()
    assert not app.exception
    assert len(app.session_state.history) == 1
    _, answer, hits, _ = app.session_state.history[0]
    assert not answer.generated
    assert len(hits) == 1
    assert hits[0].passage.source.startswith("RAP07")
    assert "Issue non renseignée" in answer.text
    assert not app.text_input
    assert all("OpenAI" not in c.label for c in app.checkbox)


def test_remove_all_documents_does_not_reload_demo():
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    app.session_state.documents = {}
    app.run()
    assert not app.exception
    assert app.metric[0].value == "0"
    assert app.chat_input[0].disabled


def test_ready_local_model_is_used_without_key(monkeypatch):
    monkeypatch.setattr("memoire.local_llm.model_status", lambda: (True, "Modèle local prêt"))
    monkeypatch.setattr("memoire.answers.chat_local", lambda messages: "La résolution reste inconnue. [S1]")
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    app.chat_input[0].set_value("INC07 est-il résolu ?").run()
    assert not app.exception
    assert app.session_state.history[0][1].generated


def test_local_failure_keeps_sources_available(monkeypatch):
    monkeypatch.setattr("memoire.local_llm.model_status", lambda: (True, "Modèle local prêt"))

    def failed_chat(messages):
        raise OSError("moteur arrêté")

    monkeypatch.setattr("memoire.answers.chat_local", failed_chat)
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    app.chat_input[0].set_value("INC07 est-il résolu ?").run()
    assert not app.exception
    answer = app.session_state.history[0][1]
    assert not answer.generated
    assert "aucun service payant" in answer.notice
