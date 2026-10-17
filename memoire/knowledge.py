"""Faits sourcés, chronologie et vocabulaire commun de la V2.

Les étiquettes détectées dans un import restent des propositions à vérifier.
L'absence de champ n'est jamais transformée en un résultat négatif.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field, replace
from datetime import date

from memoire.documents import Document, equipment_ids, references

FIELDS = {
    "incident": "Incident", "equipment": "Équipement", "date": "Date",
    "component": "Composant", "symptoms": "Symptômes", "diagnosis": "Diagnostic",
    "diagnosis_status": "Statut du diagnostic", "action": "Intervention",
    "duration": "Durée", "outcome": "Résultat", "control": "Constat de contrôle",
}


def normalized(text: str) -> str:
    text = "".join(c for c in unicodedata.normalize("NFKD", text.lower())
                   if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+", text))


@dataclass(frozen=True)
class Fact:
    value: str
    page: str
    quote: str


@dataclass(frozen=True)
class Record:
    document_id: str
    report: str
    facts: dict[str, Fact] = field(default_factory=dict)
    validated: bool = False
    origin: str = "Extraction à vérifier"

    def value(self, name: str) -> str:
        return self.facts[name].value if name in self.facts else ""

    @property
    def incident(self) -> str:
        value = self.value("incident")
        return value.upper() if re.fullmatch(r"INC\d+", value, re.I) else value or f"Sans référence · {self.report}"

    @property
    def equipment(self) -> str:
        ids = equipment_ids(self.value("equipment"))
        return ids[0] if len(ids) == 1 else "Non renseigné"

    @property
    def event_date(self) -> str:
        value = self.value("date")
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError:
            return ""

    @property
    def status(self) -> str:
        text = normalized(self.value("outcome"))
        if text in {"non resolu", "non resolue", "n est pas resolu", "n est pas resolue"}:
            return "Non résolu"
        if text in {"resolu", "resolue", "resolu confirme", "resolution confirmee"}:
            return "Résolu"
        return "Inconnu"


def evidence_valid(document: Document, fact: Fact) -> bool:
    if not fact.value.strip() or not fact.quote.strip():
        return False
    def norm(s):
        return " ".join(s.split()).casefold()
    return any(page.label == fact.page and norm(fact.quote) in norm(page.text)
               and norm(fact.value) in norm(fact.quote) for page in document.pages)


def extract_record(document: Document) -> Record:
    facts: dict[str, Fact] = {}
    report = document.name
    found: dict[str, list[Fact]] = {}
    for page in document.pages:
        for key, label in {"report": "Rapport", **FIELDS}.items():
            matches = list(re.finditer(r"^\s*" + re.escape(label) + r"\s*:\s*([^\n]+)",
                                       page.text, re.M | re.I))
            for match in matches:
                value = match.group(1).strip()
                found.setdefault(key, []).append(Fact(value, page.label, match.group().strip()))
    for key, candidates in found.items():
        if len({f.value for f in candidates}) == 1:
            if key == "report":
                report = candidates[0].value
            else:
                facts[key] = candidates[0]
    # Détection conservatrice des identifiants : aucun diagnostic déduit de symptômes.
    all_text = "\n".join(p.text for p in document.pages)
    for key, values in (("equipment", set(equipment_ids(all_text))),
                        ("incident", {r for r in references(all_text) if r.startswith("INC")})):
        if key not in facts and len(values) == 1:
            value = next(iter(values))
            page = next(p for p in document.pages if value in p.text.upper())
            match = re.search(re.escape(value), page.text, re.I)
            literal = match.group()
            facts[key] = Fact(literal, page.label, literal)
    return Record(document.id, report, facts, document.demo,
                  "Scénario fictif contrôlé" if document.demo else "Extraction à vérifier")


def correct_fact(record: Record, document: Document, key: str,
                 value: str, page: str, quote: str) -> Record:
    if record.document_id != document.id or key not in FIELDS:
        raise ValueError("Fiche ou champ invalide.")
    facts = dict(record.facts)
    if not value.strip():
        facts.pop(key, None)
    else:
        fact = Fact(value.strip(), page, quote.strip())
        if not evidence_valid(document, fact):
            raise ValueError("La valeur doit figurer dans l'extrait, et l'extrait dans la page sélectionnée.")
        if key == "date" and re.match(r"\d{4}-\d{2}-\d{2}", value):
            try:
                date.fromisoformat(value)
            except ValueError as exc:
                raise ValueError("La date ISO est invalide.") from exc
        facts[key] = fact
    return replace(record, facts=facts, validated=False, origin="Correction à vérifier")


def validate_record(record: Record, document: Document) -> Record:
    if not record.facts or record.document_id != document.id:
        raise ValueError("Il faut au moins une information reliée à ce document.")
    if not all(evidence_valid(document, fact) for fact in record.facts.values()):
        raise ValueError("Chaque valeur doit être reliée à un extrait exact du document.")
    return replace(record, validated=True, origin="Validé par l'utilisateur")


@dataclass(frozen=True)
class Incident:
    key: str
    reference: str
    equipment: str
    events: tuple[Record, ...]

    @property
    def chronology_complete(self) -> bool:
        return len(self.events) == 1 or all(r.event_date for r in self.events)

    @property
    def latest(self) -> tuple[Record, ...]:
        if not self.chronology_complete:
            return self.events
        last_date = max(r.event_date for r in self.events)
        return tuple(r for r in self.events if r.event_date == last_date)

    @property
    def status(self) -> str:
        if not self.chronology_complete:
            return "Inconnu"
        statuses = {r.status for r in self.latest}
        return next(iter(statuses)) if len(statuses) == 1 else "À clarifier"

    @property
    def validated(self) -> bool:
        return all(r.validated for r in self.events)


def incidents(records: list[Record], *, include_drafts: bool = False) -> list[Incident]:
    groups: dict[tuple[str, str], list[Record]] = {}
    for record in records:
        if not record.validated and not include_drafts:
            continue
        key = (record.incident, record.equipment)
        groups.setdefault(key, []).append(record)
    return [Incident(f"{ref}|{eq}", ref, eq,
                     tuple(sorted(events, key=lambda r: (r.event_date or "9999", r.report))))
            for (ref, eq), events in sorted(groups.items())]


def component_type(value: str) -> str:
    text = normalized(value)
    for label in ("Roulement", "Rotor", "Joint", "Capteur", "Ventilation", "Palier"):
        if normalized(label) in text:
            return label
    return "Non renseigné"


def symptom_types(value: str) -> set[str]:
    text = normalized(value)
    mapping = {"Vibration": ("vibr",), "Bruit": ("bruit",),
               "Surchauffe": ("surchauff", "echauff", "chauffe"),
               "Fuite": ("fuite",), "Mesure instable": ("mesure instable", "affichage instable")}
    return {label for label, words in mapping.items() if any(w in text for w in words)}


def similar_incidents(items: list[Incident], *, query: str = "", symptom: str = "",
                      component: str = "", equipment_type: str = "",
                      catalog: dict[str, dict] | None = None, exclude: str = "") -> list[tuple[Incident, list[str]]]:
    from memoire.retrieval import tokens

    query_tokens = set(tokens(query))
    query_symptoms = symptom_types(query)
    query_component = component_type(query)
    ranked = []
    for item in items:
        if item.key == exclude:
            continue
        facts = item.events
        symptoms = set().union(*(symptom_types(r.value("symptoms")) for r in facts))
        components = {component_type(r.value("component")) for r in facts}
        kind = (catalog or {}).get(item.equipment, {}).get("type", "Non renseigné")
        if symptom and symptom not in symptoms or component and component not in components:
            continue
        if equipment_type and kind != equipment_type:
            continue
        text = " ".join(r.value(k) for r in facts for k in ("symptoms", "component", "diagnosis", "action", "control"))
        overlap = len(query_tokens & set(tokens(text)))
        matching_symptoms = query_symptoms & symptoms
        matching_component = query_component != "Non renseigné" and query_component in components
        if query_tokens and not overlap and not matching_symptoms and not matching_component:
            continue
        reasons = ([f"Symptôme : {symptom}"] if symptom else [])
        reasons += [f"Composant : {component}"] if component else []
        reasons += [f"Type : {kind}"] if equipment_type else []
        reasons += ["Description proche par les termes utilisés"] if overlap else []
        reasons += ["Symptôme rapproché : " + ", ".join(sorted(matching_symptoms))] if matching_symptoms else []
        ranked.append((overlap + 2 * bool(symptom) + 2 * bool(component)
                       + 3 * len(matching_symptoms) + 2 * matching_component, item, reasons))
    ranked.sort(key=lambda entry: (-entry[0], entry[1].reference))
    return [(item, reasons) for _, item, reasons in ranked]
