"""Sélection des rapports et ajout des suivis d'un incident explicitement demandé."""

from memoire.documents import references
from memoire.knowledge import Record, normalized
from memoire.retrieval import Hit, SearchIndex


def expand_aliases(question: str, catalog: dict[str, dict]) -> str:
    padded = " " + normalized(question) + " "
    codes = []
    for code, info in catalog.items():
        aliases = [info.get("name", ""), *info.get("aliases", [])]
        if any(alias and " " + normalized(alias) + " " in padded for alias in aliases):
            codes.append(code)
    return question + (" " + " ".join(codes) if codes else "")


def search_reports(index: SearchIndex, question: str, records: list[Record], *,
                   top_k: int = 4, equipment: str | None = None) -> list[Hit]:
    ranked = index.search(question, top_k=len(index.passages), equipment=equipment)
    hits = []
    seen_documents = set()
    for hit in ranked:
        if hit.passage.document_id not in seen_documents:
            hits.append(hit)
            seen_documents.add(hit.passage.document_id)
        if len(hits) == top_k:
            break
    wanted = {ref for ref in references(question) if ref.startswith("INC")}
    if not wanted:
        return hits
    by_document = {r.document_id: r for r in records}
    # Un rapport qui mentionne un autre incident pour le distinguer n'en fait pas partie.
    hits = [h for h in hits if not by_document.get(h.passage.document_id)
            or not by_document[h.passage.document_id].value("incident")
            or by_document[h.passage.document_id].incident in wanted]
    related = sorted((r for r in records if r.validated and r.incident in wanted
                      and (equipment is None or r.equipment == equipment)),
                     key=lambda r: (r.event_date or "9999", r.report), reverse=True)
    selected = []
    for record in related:
        passage = next((p for p in index.passages if p.document_id == record.document_id), None)
        if passage:
            selected.append(Hit(passage, 0.0, 0.0))
    seen = {h.passage.document_id for h in selected}
    selected.extend(h for h in hits if h.passage.document_id not in seen)
    return selected[:max(top_k, min(len(related), 8))]
