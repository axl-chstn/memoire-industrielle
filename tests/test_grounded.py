import json
from dataclasses import replace
from unittest.mock import Mock

import pytest

from memoire.answers import generate_answer, verified_quotes
from memoire.documents import chunk_document, read_document
from memoire.knowledge import extract_record, validate_record
from memoire.qa import search_reports
from memoire.retrieval import Hit, SearchIndex


def corpus(*texts):
    docs = [read_document(f"rapport-{i}.txt", text.encode()) for i, text in enumerate(texts)]
    records = [validate_record(extract_record(d), d) for d in docs]
    return records, SearchIndex([p for d in docs for p in chunk_document(d)])


@pytest.fixture
def undated():
    return corpus(
        "Rapport : Visite-A\nIncident : INC811\nÉquipement : EQ81\nDate : 2025-04-03\nIntervention : Nettoyage\nRésultat : Inconnu",
        "Rapport : Visite-B\nIncident : INC811\nÉquipement : EQ81\nIntervention : Remplacement du ventilateur\nRésultat : Résolu",
    )


@pytest.mark.parametrize("question", [
    "Quel est le dernier état documenté de INC811 ?",
    "Peut-on établir l'ordre chronologique des visites de INC811 ?",
    "Quel est le statut de clôture de INC811 ?",
    "Peux-tu retracer l'évolution de INC811 ?",
])
def test_missing_date_cannot_be_replaced_with_an_invented_order(undated, monkeypatch, question):
    records, index = undated
    model = Mock(side_effect=AssertionError("Le modèle ne doit pas décider la chronologie"))
    monkeypatch.setattr("memoire.answers.chat_local", model)
    answer = generate_answer(question, search_reports(index, question, records), local=True, records=records)
    assert answer.documented and "inconnu" in answer.text
    assert "antérieur" not in answer.text and "postérieur" not in answer.text
    assert "2025-04-03" in answer.text or "non daté" in answer.text
    model.assert_not_called()


def test_unknown_action_and_outcome_are_not_rewritten_as_absence_and_failure():
    records, index = corpus("Rapport : Note-X\nIncident : INC823\nÉquipement : EQ91\nDate : 2024-12-04\nRésultat : Inconnu\nSignalement visuel seulement.")
    question = "Quels travaux ont été réalisés pour INC823 ?"
    answer = generate_answer(question, search_reports(index, question, records), records=records)
    assert "Intervention : non renseigné dans la fiche" in answer.text
    assert "Inconnu" in answer.text
    assert "ne prouve pas" in answer.text
    assert "non résolu" not in answer.text
    assert "aucune intervention n'a été réalisée" not in answer.text.lower()


def test_latest_control_does_not_invent_absence_of_older_measurements():
    records, index = corpus(
        "Rapport : Controle-A\nIncident : INC832\nÉquipement : C41\nDate : 2024-02-01\nRésultat : Non résolu\nConstat de contrôle : Pression entre 4 et 5 bar",
        "Rapport : Controle-B\nIncident : INC832\nÉquipement : C41\nDate : 2024-02-08\nRésultat : Non résolu\nConstat de contrôle : Pression entre 6 et 7 bar",
    )
    question = "Quelles pressions au dernier contrôle de INC832 ?"
    answer = generate_answer(question, search_reports(index, question, records), records=records)
    assert "2024-02-08" in answer.text and "6 et 7 bar" in answer.text
    assert "aucune" not in answer.text.lower()
    assert "4 et 5 bar" not in answer.text


def test_failed_then_successful_actions_have_a_readable_order_without_model():
    records, index = corpus(
        "Rapport : Essai-A\nIncident : INC843\nÉquipement : P87\nDate : 2023-11-04\nIntervention : Inspection\nDurée : 12 minutes\nRésultat : Non résolu",
        "Rapport : Essai-B\nIncident : INC843\nÉquipement : P87\nDate : 2023-11-09\nIntervention : Nettoyage du filtre\nDurée : 37 minutes\nRésultat : Résolu",
    )
    question = "Dans quel ordre les tentatives pour INC843 ont-elles été menées ?"
    answer = generate_answer(question, search_reports(index, question, records), records=records)
    assert answer.documented
    assert answer.text.index("Essai-A") < answer.text.index("Essai-B")
    assert "12 minutes" in answer.text and "37 minutes" in answer.text
    assert "résolu selon le dernier état documenté (2023-11-09)" in answer.text


@pytest.mark.parametrize("response", [
    '{"sources": ["S99"]}', '{"sources": [1]}', '{"sources": "S1"}',
    '{"sources": ["S1"], "conclusion": "Incident résolu"}',
    '{"sources": ["S1"], "extrait": "résolu"}', 'Une phrase inventée [S1]',
    '{"sources": ["S1", "S1", "S1", "S1"]}', 'null',
])
def test_model_cannot_add_a_claim_even_with_a_valid_reference(response):
    doc = read_document("rapport.txt", b"Le resultat reste inconnu. Aucune mesure n'est jointe.")
    hits = [Hit(chunk_document(doc)[0], 1, 1)]
    with pytest.raises(ValueError):
        verified_quotes(response, hits)


def test_model_cannot_remove_a_negation_or_turn_no_attached_measurement_into_no_measurement():
    doc = read_document("rapport.txt", "Le résultat n'est pas résolu. Aucun relevé vibratoire n'est joint ; des mesures peuvent exister ailleurs.".encode())
    hits = [Hit(chunk_document(doc)[0], 1, 1)]
    selected = verified_quotes('{"sources": ["S1"]}', hits)
    assert selected == [("S1", hits[0].passage.text)]
    assert "n'est pas résolu" in selected[0][1]
    assert "peuvent exister ailleurs" in selected[0][1]


def test_model_failure_keeps_a_readable_verified_response(monkeypatch):
    records, index = corpus("Rapport : Controle-X\nIncident : INC854\nÉquipement : M77\nDate : 2022-08-01\nIntervention : Inspection\nRésultat : Inconnu")
    monkeypatch.setattr("memoire.answers.chat_local", lambda messages: "Conclusion inventée [S1]")
    answer = generate_answer("Quels passages décrivent INC854 ?", search_reports(index, "INC854", records), local=True, records=records)
    assert answer.documented and not answer.generated
    assert "Voici les informations" in answer.text
    assert "Conclusion inventée" not in answer.text
    assert answer.sections


def test_unvalidated_or_incomplete_history_cannot_produce_a_current_status(undated):
    records, index = undated
    records[1] = replace(records[1], validated=False)
    question = "Quel est le dernier état de INC811 ?"
    answer = generate_answer(question, search_reports(index, question, records), records=records)
    assert "historique incomplet" in answer.text


def test_question_without_reference_does_not_hide_a_known_followup(undated):
    records, index = undated
    hits = [Hit(index.passages[0], 1, 1)]
    answer = generate_answer("Quel est le statut actuel ?", hits, records=records)
    assert answer.documented and "historique incomplet" in answer.text


def test_evidence_outside_the_cited_passage_is_never_used_for_a_status(undated):
    records, index = undated
    passage = index.passages[0]
    fragment = replace(passage, text="Incident : INC811 Équipement : EQ81")
    hits = [Hit(fragment, 1, 1), Hit(index.passages[1], 1, 1)]
    answer = generate_answer("INC811 est-il résolu ?", hits, records=records)
    assert "preuves du résultat" in answer.text


def test_newest_incident_on_a_machine_uses_the_whole_retrieved_history():
    records, index = corpus(
        "Rapport : Episode-A\nIncident : INC865\nÉquipement : P79\nDate : 2021-05-01\nSymptômes : Vibration\nRésultat : Résolu",
        "Rapport : Episode-B\nIncident : INC866\nÉquipement : P79\nDate : 2021-05-03\nSymptômes : Fuite\nRésultat : Non résolu",
    )
    question = "Quel est le dernier incident daté de P79 ?"
    answer = generate_answer(question, search_reports(index, question, records), records=records)
    assert "INC866" in answer.text and "2021-05-03" in answer.text
    assert "INC865" not in answer.text


def test_body_passage_is_kept_alongside_fact_header_for_free_questions():
    records, index = corpus("Rapport : Cout-A\nIncident : INC877\nÉquipement : C78\nDate : 2020-01-02\nRésultat : Inconnu\n" + "contexte " * 170 + "Le coût de la pièce était de 45 euros.")
    hits = search_reports(index, "Quel coût pour INC877 ?", records)
    assert any("Incident : INC877" in h.passage.text for h in hits)
    assert any("45 euros" in h.passage.text for h in hits)


def test_free_question_reads_only_model_selected_sources(monkeypatch):
    records, index = corpus("Rapport : Cout-B\nIncident : INC888\nÉquipement : P78\nDate : 2020-02-04\nRésultat : Inconnu\nCoût total : 55 euros.")
    monkeypatch.setattr("memoire.answers.chat_local", lambda messages: json.dumps({"sources": ["S1"]}))
    hits = search_reports(index, "Quel coût pour INC888 ?", records)
    answer = generate_answer("Quel coût pour INC888 ?", hits, local=True, records=records)
    assert answer.generated and hits[0].passage.text in answer.text


def test_empty_model_selection_can_still_show_an_explicit_cost_statement(monkeypatch):
    records, index = corpus("Rapport : Cout-C\nIncident : INC889\nÉquipement : P78\nDate : 2020-02-04\nRésultat : Inconnu\nLe coût de la pièce n'est pas indiqué.")
    monkeypatch.setattr("memoire.answers.chat_local", lambda messages: '{"sources": []}')
    hits = search_reports(index, "Quel coût pour INC889 ?", records)
    answer = generate_answer("Quel coût pour INC889 ?", hits, local=True, records=records)
    assert answer.documented and not answer.generated
    assert "coût de la pièce n'est pas indiqué" in answer.text
    assert hits[0].passage.text in answer.text


def test_unrelated_header_does_not_identify_an_intervening_person(monkeypatch):
    records, index = corpus("Rapport : Visite-Y\nIncident : INC890\nÉquipement : P78\nDate : 2020-02-04\nIntervention : Inspection\nRésultat : Inconnu")
    monkeypatch.setattr("memoire.answers.chat_local", lambda messages: '{"sources": ["S1"]}')
    question = "Quel technicien est intervenu pour INC890 ?"
    answer = generate_answer(question, search_reports(index, question, records), local=True, records=records)
    assert "Aucun nom de technicien n'a pu être établi" in answer.text
    assert "aucune personne n'est intervenue" in answer.text
    assert "ne prouve pas" in answer.text


def test_explicit_person_name_is_copied_and_not_replaced_with_an_absence(monkeypatch):
    records, index = corpus("Rapport : Visite-Z\nIncident : INC891\nÉquipement : P78\nDate : 2020-02-04\nRésultat : Inconnu\nTechnicien : Personne Fictive")
    monkeypatch.setattr("memoire.answers.chat_local", lambda messages: '{"sources": ["S1"]}')
    question = "Quel technicien pour INC891 ?"
    answer = generate_answer(question, search_reports(index, question, records), local=True, records=records)
    assert "Technicien : Personne Fictive" in answer.text
    assert "Aucun nom" not in answer.text
