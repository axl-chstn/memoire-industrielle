from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from memoire.documents import read_document

APP = Path(__file__).resolve().parents[1] / "app.py"


@pytest.fixture(autouse=True)
def offline_model_status(monkeypatch):
    monkeypatch.setattr("memoire.local_llm.model_status", lambda: (False, "Modèle local absent"))


def open_page(app, page):
    return app.radio(key="route").set_value(page).run()


def test_workshop_and_documented_answer_without_api_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "ancienne-cle-inutilisee")
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    assert not app.exception
    assert [m.value for m in app.metric[:3]] == ["30", "10", "22"]
    open_page(app, "Questions")
    app.chat_input[0].set_value("L'incident INC104 est-il résolu ?").run()
    assert not app.exception
    _, answer, hits, _ = app.session_state.history[0]
    assert answer.documented and not answer.generated
    assert "2026-03-08" in answer.text
    assert len(hits) == 2
    assert answer.sections
    assert all("OpenAI" not in c.label for c in app.checkbox)


def test_empty_personal_workspace_does_not_reload_demo():
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    app.selectbox(key="workspace").set_value("Mes documents").run()
    assert not app.exception
    assert app.metric[0].value == "0"
    open_page(app, "Questions")
    assert app.chat_input[0].disabled
    app.selectbox(key="workspace").set_value("Atelier fictif").run()
    assert app.metric[0].value == "30"


def test_ready_local_model_is_used_without_key(monkeypatch):
    monkeypatch.setattr("memoire.local_llm.model_status", lambda: (True, "Modèle local prêt"))
    monkeypatch.setattr("memoire.answers.chat_local", lambda messages: "Une lubrification a été effectuée. [S1]")
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    open_page(app, "Questions")
    app.chat_input[0].set_value("Quelle intervention pour INC103 ?").run()
    assert not app.exception
    assert app.session_state.history[0][1].generated


def test_local_failure_keeps_sources_available(monkeypatch):
    monkeypatch.setattr("memoire.local_llm.model_status", lambda: (True, "Modèle local prêt"))

    def failed_chat(messages):
        raise OSError("moteur arrêté")

    monkeypatch.setattr("memoire.answers.chat_local", failed_chat)
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    open_page(app, "Questions")
    app.chat_input[0].set_value("Quelle intervention pour INC103 ?").run()
    assert not app.exception
    answer = app.session_state.history[0][1]
    assert not answer.generated
    assert "aucun service payant" in answer.notice


@pytest.mark.parametrize("page", ["Équipements", "Incidents", "Cas similaires", "Documents"])
def test_business_pages_render(page):
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    open_page(app, page)
    assert not app.exception


def test_navigation_from_equipment_to_incident():
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    open_page(app, "Équipements")
    next(b for b in app.button if b.label == "Ouvrir cet historique").click().run()
    assert not app.exception
    assert app.radio(key="route").value == "Incidents"


def test_personal_record_needs_human_validation_and_stays_separate():
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    document = read_document("personnel.md", b"Incident : INC900\nEquipement : P01\nIntervention : Inspection")
    spaces = app.session_state.workspaces
    spaces["Mes documents"][document.id] = document
    app.session_state.workspaces = spaces
    app.selectbox(key="workspace").set_value("Mes documents").run()
    assert app.metric[0].value == "1"
    assert app.metric[2].value == "0"
    open_page(app, "Documents")
    next(b for b in app.button if b.label == "Valider les informations présentes").click().run()
    assert not app.exception
    assert app.metric[2].value == "1"
    app.selectbox(key="workspace").set_value("Atelier fictif").run()
    assert app.metric[0].value == "30"
    assert app.metric[2].value == "22"


def test_correction_flow_requires_validation_again():
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    open_page(app, "Documents")
    next(s for s in app.selectbox if s.label == "Information à corriger").set_value("action").run()
    next(t for t in app.text_input if t.label == "Valeur exacte dans le rapport").set_value("Remplacement du roulement")
    app.text_area[0].set_value("Intervention : Remplacement du roulement")
    next(b for b in app.button if b.label == "Enregistrer la correction").click().run()
    assert not app.exception
    assert app.metric[2].value == "21"
    next(b for b in app.button if b.label == "Valider les informations présentes").click().run()
    assert not app.exception
    assert app.metric[2].value == "22"
