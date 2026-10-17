from dataclasses import replace

import pytest

from memoire.answers import generate_answer, structured_sections
from memoire.demo import load_workshop, workshop_catalog
from memoire.documents import Document, Page, Passage, chunk_document, read_document
from memoire.knowledge import (
    Fact,
    correct_fact,
    evidence_valid,
    extract_record,
    incidents,
    similar_incidents,
    validate_record,
)
from memoire.qa import expand_aliases, search_reports
from memoire.retrieval import Hit, SearchIndex


@pytest.fixture
def workshop():
    docs = load_workshop()
    records = [extract_record(d) for d in docs]
    index = SearchIndex([p for d in docs for p in chunk_document(d)])
    return docs, records, index


def test_workshop_is_consistent_and_every_fact_has_an_exact_source(workshop):
    docs, records, _ = workshop
    catalog = workshop_catalog()["equipment"]
    assert len(docs) == 30 and len(catalog) == 10
    assert len(incidents(records)) == 22
    codes = {e["id"] for e in catalog}
    for document, record in zip(docs, records):
        assert record.equipment in codes
        assert record.validated
        assert all(evidence_valid(document, fact) for fact in record.facts.values())
        parts = next(e["components"] for e in catalog if e["id"] == record.equipment)
        assert any(part["id"] in record.value("component") for part in parts)


def test_latest_report_changes_outcome_without_erasing_failed_attempt(workshop):
    _, records, _ = workshop
    item = next(i for i in incidents(records) if i.reference == "INC114")
    assert len(item.events) == 2
    assert [r.status for r in item.events] == ["Non résolu", "Résolu"]
    assert item.events[0].value("action") == "Lubrification"
    assert item.status == "Résolu"
    assert item.latest[0].event_date == "2026-03-20"


def test_replacement_does_not_imply_resolution(workshop):
    _, records, _ = workshop
    item = next(i for i in incidents(records) if i.reference == "INC116")
    assert item.latest[0].value("action") == "Remplacement du roulement"
    assert item.status == "Non résolu"


def test_missing_dates_are_not_invented(workshop):
    _, records, _ = workshop
    item = next(i for i in incidents(records) if i.reference == "INC117")
    assert item.latest[0].event_date == ""
    assert item.status == "Inconnu"


def test_undated_followup_prevents_claiming_a_latest_status(workshop):
    _, records, _ = workshop
    first = next(r for r in records if r.incident == "INC104")
    last = next(r for r in records if r.report == "RAP121")
    last = replace(last, facts={k: v for k, v in last.facts.items() if k != "date"})
    item = incidents([first, last])[0]
    assert not item.chronology_complete and item.status == "Inconnu"


def test_same_date_conflict_is_exposed(workshop):
    _, records, _ = workshop
    record = records[0]
    conflict = replace(record, document_id="other", facts={**record.facts,
        "outcome": Fact("Non résolu", "Texte", "Résultat : Non résolu")})
    item = incidents([record, conflict])[0]
    assert item.status == "À clarifier"


def test_different_machines_with_same_incident_reference_are_not_merged(workshop):
    _, records, _ = workshop
    other = replace(records[0], document_id="other", facts={**records[0].facts,
        "equipment": Fact("P02", "Texte", "Équipement : P02")})
    assert len(incidents([records[0], other])) == 2


def test_untrusted_import_is_never_automatically_validated(workshop):
    docs, _, _ = workshop
    doc = read_document("rapport.md", docs[0].pages[0].text.encode())
    record = extract_record(doc)
    assert not record.validated and incidents([record]) == []
    assert len(incidents([record], include_drafts=True)) == 1
    assert validate_record(record, doc).validated


def test_correction_requires_exact_evidence_and_invalidates_prior_validation(workshop):
    docs, records, _ = workshop
    record = correct_fact(records[0], docs[0], "action", "Remplacement du roulement",
                          "Texte", "Intervention : Remplacement du roulement")
    assert not record.validated
    with pytest.raises(ValueError, match="valeur"):
        correct_fact(records[0], docs[0], "outcome", "Non résolu", "Texte", "Résultat : Résolu confirmé")
    with pytest.raises(ValueError, match="page"):
        correct_fact(records[0], docs[0], "action", "Inspection", "Texte", "Inspection inventée")


def test_conflicting_fields_on_two_pages_are_not_arbitrarily_selected():
    doc = Document("x", "rapport.pdf", (Page("Page 1", "Résultat : Résolu"),
                                        Page("Page 2", "Résultat : Non résolu")))
    assert "outcome" not in extract_record(doc).facts


def test_similar_cases_cross_equipment_and_preserve_failed_results(workshop):
    _, records, _ = workshop
    items = incidents(records)
    seed = next(i for i in items if i.reference == "INC116")
    results = similar_incidents(items, symptom="Vibration", component="Roulement", exclude=seed.key)
    assert any(item.equipment != seed.equipment for item, _ in results)
    assert seed.key not in {item.key for item, _ in results}
    assert all(reasons for _, reasons in results)


def test_query_synonym_is_supported_by_controlled_symptom_vocabulary(workshop):
    _, records, _ = workshop
    result = similar_incidents(incidents(records), query="ça chauffe")
    assert result
    assert any(item.reference == "INC115" for item, _ in result)


def test_incident_question_adds_followup_even_when_top_k_is_one(workshop):
    _, records, index = workshop
    hits = search_reports(index, "INC104 est-il résolu ?", records, top_k=1)
    assert {h.passage.source.split("_")[0] for h in hits} == {"RAP104", "RAP121"}
    answer = generate_answer("INC104 est-il résolu ?", hits, records=records)
    assert answer.documented and "2026-03-08" in answer.text
    assert "non résolu selon" not in answer.text
    assert answer.sections


def test_incomplete_context_never_claims_a_current_status(workshop):
    _, records, index = workshop
    hits = [h for h in index.search("INC104") if h.passage.source.startswith("RAP104")][:1]
    answer = generate_answer("INC104 est-il résolu ?", hits, records=records)
    assert answer.documented and "historique incomplet" in answer.text


def test_comparison_of_two_incidents_can_retrieve_both(workshop):
    _, records, index = workshop
    hits = search_reports(index, "Comparer INC104 et INC116", records)
    assert {"RAP104", "RAP121", "RAP116", "RAP128"} <= {h.passage.source.split("_")[0] for h in hits}


def test_report_mentioning_another_incident_is_not_merged_into_it(workshop):
    _, records, index = workshop
    hits = search_reports(index, "INC107", records)
    assert "RAP129_P01.md" not in {h.passage.source for h in hits}


def test_alias_is_resolved_only_with_the_active_catalog():
    catalog = {e["id"]: e for e in workshop_catalog()["equipment"]}
    assert expand_aliases("Que sait-on de la pompe d'alimentation ?", catalog).endswith(" P01")
    assert expand_aliases("pompe d'alimentation", {}) == "pompe d'alimentation"


def test_structured_fact_is_not_cited_when_its_quote_is_outside_the_passage(workshop):
    docs, records, _ = workshop
    fragment = Passage("fragment", docs[0].id, docs[0].name, "Texte · passage 1",
                       "Incident : INC101 Équipement : P01", ("P01",))
    hits = [Hit(fragment, 1, 1)]
    sections = structured_sections(hits, records)
    assert all(title != "Actions réalisées" for title, _ in sections)
    answer = generate_answer("INC101 est-il résolu ?", hits, records=records)
    assert "preuves du résultat" in answer.text
