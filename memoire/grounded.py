"""Réponses composées à partir de faits vérifiés, sans conclusion libre du modèle."""

from __future__ import annotations

import re
from dataclasses import dataclass

from memoire.documents import equipment_ids, references
from memoire.knowledge import FIELDS, Record, incidents, normalized
from memoire.retrieval import Hit


@dataclass(frozen=True)
class Reply:
    text: str
    notice: str = "Réponse composée à partir des fiches vérifiées et des extraits cités."


def fact_citation(record: Record, key: str, hits: list[Hit]) -> str:
    fact = record.facts.get(key)
    if fact is None:
        return ""
    quote = " ".join(fact.quote.split()).casefold()
    for i, hit in enumerate(hits, 1):
        if hit.passage.document_id == record.document_id and quote in " ".join(hit.passage.text.split()).casefold():
            return f"[S{i}]"
    return ""


def intent(question: str) -> str | None:
    q = normalized(question)
    # Ces informations ne font pas partie des rubriques des fiches. Leur absence
    # dans une fiche ne prouve pas leur absence dans le texte du rapport.
    if re.search(r"\b(cout|prix|euros?|budget|technicien|personne|auteur)\b|qui .*intervenu", q):
        return None
    if re.search(r"meme (episode|incident)|compar|distinct|difference", q):
        return "compare"
    if re.search(r"\b(dernier|derniere|recent|recente)\b.*incident|incident.*\b(recent|recente)\b", q):
        return "latest_incident"
    if re.search(r"\b(pression|temperature|mesure|releve|controle)\w*\b", q) and re.search(r"dernier|derniere|recent", q):
        return "latest_control"
    if re.search(r"chronolog|\bordre\b|historique|evolution|enchain|succession", q):
        return "timeline"
    if re.search(r"\bdate\b|\bquand\b", q):
        return "dates"
    if re.search(r"\bduree|\bminutes?\b|combien de temps|\btemps\b", q):
        return "duration"
    if re.search(r"cause|diagnostic|origine|confirm|expliqu|usure", q):
        return "diagnosis"
    if re.search(r"intervention|action|essay|tente|tentative|qu a t on|fait|effectu|realise|remplac|nettoy|travaux", q):
        return "actions"
    if re.search(r"resolu|resolution|repar|clotur|\betat\b|\bstatut\b|resultat|issue|termine|reglee?\b", q):
        return "status"
    if re.search(r"\b(pression|temperature|mesure|releve|controle)\w*\b", q):
        return "control"
    return None


def _anchor(record, hits):
    return next((f"[S{i}]" for i, h in enumerate(hits, 1)
                 if h.passage.document_id == record.document_id), "")


def _line(record, keys, hits):
    date = record.event_date if fact_citation(record, "date", hits) else ""
    heading = f"{record.report} · {date or 'date non établie'}"
    parts = []
    for key in keys:
        fact = record.facts.get(key)
        citation = fact_citation(record, key, hits)
        if citation:
            parts.append(f"{FIELDS[key]} : « {fact.value} » {citation}")
        elif fact:
            parts.append(f"{FIELDS[key]} : extrait justificatif absent de la sélection")
        else:
            parts.append(f"{FIELDS[key]} : non renseigné dans la fiche vérifiée {_anchor(record, hits)}")
    return heading + " — " + " ; ".join(parts) + "."


def _chronology_proved(records, hits):
    return all((not r.event_date or fact_citation(r, "date", hits)) for r in records)


def _status(item, hits):
    if not item.chronology_complete:
        return f"{item.reference} · {item.equipment} : statut actuel inconnu, car un rapport non daté empêche d'établir la chronologie complète. " + " ".join(_anchor(r, hits) for r in item.events)
    if not _chronology_proved(item.events, hits) or any(not fact_citation(r, "outcome", hits) for r in item.latest):
        return "Les extraits sélectionnés ne contiennent pas toutes les preuves du résultat et de sa date. Consulte les rapports complets."
    date = item.latest[0].event_date or "date non renseignée"
    return f"{item.reference} · {item.equipment} : {item.status.lower()} selon le dernier état documenté ({date}). " + " ".join(_anchor(r, hits) for r in item.latest)


def documented_reply(question: str, hits: list[Hit], records: list[Record]) -> Reply | None:
    kind = intent(question)
    if kind is None or not records:
        return None
    ids = {h.passage.document_id for h in hits}
    wanted = {r for r in references(question) if r.startswith("INC")}
    machines = set(equipment_ids(question))
    reports = {r for r in references(question) if r.startswith("RAP")}
    scoped = [r for r in records if (not wanted or r.incident in wanted)
              and (not machines or r.equipment in machines)
              and (not reports or r.report.upper() in reports)]
    named = bool(wanted or machines or reports)
    if not named:
        scoped = [r for r in scoped if r.document_id in ids]
        if kind in {"status", "timeline", "compare", "latest_control"}:
            groups = {(r.incident, r.equipment) for r in scoped}
            # Même sans identifiant dans la question, une sélection du premier
            # rapport ne doit pas masquer un suivi connu du même incident.
            scoped = [r for r in records if (r.incident, r.equipment) in groups]
    if not scoped:
        return None
    if wanted - {r.incident for r in scoped}:
        return Reply("Au moins une référence d'incident demandée n'a pas de fiche correspondante. La comparaison ne peut pas être établie.")
    if any(not r.validated or r.document_id not in ids for r in scoped):
        return Reply("La réponse ne peut pas être établie à partir d'un historique incomplet ou de fiches non vérifiées. Consulte les rapports et leurs dates.",
                     "Les rapports manquants ou non vérifiés empêchent une conclusion à partir des fiches.")
    chronological = kind in {"status", "timeline", "compare", "latest_incident", "latest_control"}
    if chronological and not _chronology_proved(scoped, hits):
        return Reply("Les extraits sélectionnés ne contiennent pas toutes les preuves du résultat et de sa date. Consulte les rapports complets.")
    ordered = sorted(scoped, key=lambda r: (r.event_date or "9999", r.report))
    items = incidents(scoped)
    if kind == "status":
        return Reply("\n".join(_status(item, hits) for item in items))
    if kind == "latest_incident":
        if not named:
            return Reply("Précise l'équipement ou l'incident pour consulter son historique complet. La sélection actuelle ne représente pas nécessairement tout l'atelier.")
        if any(not r.event_date for r in scoped) and "date" not in normalized(question).split():
            return Reply("Un rapport n'est pas daté : le dernier incident ne peut pas être établi avec certitude.\n" + "\n".join(_line(r, ("incident", "date"), hits) for r in ordered))
        dated = [r for r in scoped if r.event_date]
        if not dated:
            return Reply("Aucun rapport daté ne permet d'établir le dernier incident de cette sélection.")
        last_date = max(r.event_date for r in dated)
        selected = [r for r in dated if r.event_date == last_date]
        return Reply("Dernier(s) rapport(s) parmi les rapports datés de cet historique :\n" + "\n".join(
            _line(r, ("incident", "symptoms", "outcome", "control"), hits) for r in selected))
    if kind == "latest_control":
        lines = []
        for item in items:
            if not item.chronology_complete:
                lines.append("Une date manque : aucun dernier contrôle certain ne peut être désigné.")
                selected = item.events
            else:
                selected = item.latest
            lines.extend(_line(r, ("control",), hits) for r in selected)
        return Reply("\n".join(lines))
    if kind in {"timeline", "compare"}:
        lines = []
        for item in items:
            lines.append(_status(item, hits))
            dated = [r for r in item.events if r.event_date]
            undated = [r for r in item.events if not r.event_date]
            lines.extend(_line(r, ("action", "duration", "outcome", "control"), hits) for r in dated)
            if undated:
                lines.append("Rapport(s) sans date, dont la position dans cette chronologie est inconnue :")
                lines.extend(_line(r, ("action", "duration", "outcome", "control"), hits) for r in undated)
        return Reply("\n".join(lines))
    keys = {"actions": ("action", "duration", "outcome", "control"),
            "duration": ("action", "duration"), "diagnosis": ("diagnosis", "diagnosis_status"),
            "dates": ("date", "action"), "control": ("control", "outcome")}[kind]
    lines = [_line(r, keys, hits) for r in ordered]
    if any("action" not in r.facts for r in ordered) and "action" in keys:
        lines.append("Une intervention non renseignée ne prouve pas qu'aucune intervention n'a eu lieu.")
    if any(not r.event_date for r in ordered) and kind == "dates":
        lines.append("Une date absente ou inexploitable ne peut pas être déduite du numéro du rapport ni de l'ordre d'import.")
    return Reply("\n".join(lines))
