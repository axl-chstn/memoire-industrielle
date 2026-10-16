from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_demo_question_and_export_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
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


def test_remove_all_documents_does_not_reload_demo():
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    app.session_state.documents = {}
    app.run()
    assert not app.exception
    assert app.metric[0].value == "0"
    assert app.chat_input[0].disabled
