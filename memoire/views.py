"""Pages métier de la V2 : équipement, incident, sources et corrections."""

from __future__ import annotations

import csv
import io
from dataclasses import replace

import streamlit as st

from memoire.knowledge import (
    FIELDS,
    component_type,
    correct_fact,
    normalized,
    similar_incidents,
    symptom_types,
    validate_record,
)

ROUTES = ["Vue d'ensemble", "Équipements", "Incidents", "Cas similaires", "Questions", "Documents"]


def navigate(route, *, equipment=None, incident=None, document=None):
    st.session_state.route = route
    if route == "Cas similaires" and incident is not None:
        st.session_state.similar_seed = incident
    for key, value in (("equipment_choice", equipment), ("incident_choice", incident),
                       ("document_choice", document)):
        if value is not None:
            st.session_state[key] = value


def choose(label, options, *, key, format_func=str):
    if st.session_state.get(key) not in options:
        st.session_state.pop(key, None)
    return st.selectbox(label, options, key=key, format_func=format_func)


def event_source(record, documents, *, expanded=False):
    document = documents[record.document_id]
    label = f"{record.report} · {record.event_date or 'Date non renseignée'} · {record.status}"
    with st.expander(label, expanded=expanded):
        st.caption(record.origin)
        rows = [{"Information": label, "Valeur": record.value(key) or "Non renseigné",
                 "Source": record.facts[key].page if key in record.facts else "—"}
                for key, label in FIELDS.items()]
        st.dataframe(rows, hide_index=True, width="stretch")
        st.button("Ouvrir ce rapport", key=f"open_{record.document_id}_{expanded}",
                  on_click=navigate, args=("Documents",), kwargs={"document": document.id})
        if st.checkbox("Afficher les extraits justificatifs", key=f"proof_{record.document_id}"):
            for key, fact in record.facts.items():
                st.caption(f"{FIELDS[key]} · {document.name} · {fact.page}")
                st.code(fact.quote, language=None, wrap_lines=True)


def incident_rows(items, records_by_doc=None):
    return [{"Incident": item.reference, "Équipement": item.equipment,
             "Dernier état": item.status,
             "Dernière date connue": max(r.event_date for r in item.events) or "Non renseignée",
             "Rapports": len(item.events),
             "Vérification": "Vérifié" if item.validated else "À vérifier"}
            for item in items]


def overview(documents, records, items, catalog):
    st.subheader("Une mémoire commune pour l'atelier")
    st.write("Partez d'un équipement, retrouvez ses incidents et vérifiez ce qui a été tenté avant de consulter les cas proches.")
    left, right = st.columns(2)
    with left:
        st.markdown("**Dernier état documenté des incidents**")
        counts = {state: sum(item.status == state for item in items)
                  for state in ("Résolu", "Non résolu", "Inconnu", "À clarifier")}
        st.bar_chart(counts, color="#087F75")
    with right:
        st.markdown("**Par où commencer ?**")
        st.button("Explorer les équipements", on_click=navigate, args=("Équipements",), width="stretch")
        st.button("Retrouver une panne similaire", on_click=navigate, args=("Cas similaires",), width="stretch")
        st.button("Poser une question aux rapports", on_click=navigate, args=("Questions",), width="stretch")
        pending = sum(not r.validated for r in records)
        if pending:
            st.info(f"{pending} fiche(s) extraite(s) à vérifier dans Documents. Elles sont exclues des vues métier par défaut.")
        else:
            st.caption("Les données de démonstration ont été préparées et contrôlées pour ce scénario fictif.")
    st.markdown("**Derniers rapports datés**")
    recent = sorted((r for r in records if r.validated and r.event_date),
                    key=lambda r: r.event_date, reverse=True)[:5]
    for record in recent:
        st.text(f"{record.event_date} · {record.report} · {record.incident} · {record.equipment} · {record.status}")
        st.button("Consulter", key=f"recent_{record.document_id}", on_click=navigate,
                  args=("Documents",), kwargs={"document": record.document_id})
    if not documents:
        st.info("L'espace est vide. Ajoute des rapports dans la colonne de gauche.")


def equipment_view(documents, records, items, catalog):
    st.subheader("Fiches équipements")
    codes = sorted({e for document in documents.values() for e in document.equipment})
    if not codes:
        st.info("Aucun identifiant d'équipement repéré dans les rapports de cet espace.")
        return
    selected = choose("Équipement", codes, key="equipment_choice",
                      format_func=lambda code: f"{code} · {catalog.get(code, {}).get('name', 'Équipement repéré')}")
    info = catalog.get(selected, {})
    st.text(f"Type : {info.get('type', 'Non renseigné')} · Zone : {info.get('zone', 'Non renseignée')}")
    if info:
        st.caption("Description et composition issues du registre fictif de l'atelier Horizon.")
        st.text("Appellations : " + ", ".join(info.get("aliases", [])))
    scoped = [item for item in items if item.equipment == selected]
    components = info.get("components", [])
    if components:
        st.markdown("**Composition connue**")
        st.dataframe([{"Référence": c["id"], "Composant": c["name"], "Catégorie": c["type"]}
                      for c in components], hide_index=True, width="stretch")
    st.markdown("**Historique des incidents**")
    if scoped:
        st.dataframe(incident_rows(scoped), hide_index=True, width="stretch")
        incident = choose("Incident à explorer", [item.key for item in scoped], key="equipment_incident",
                          format_func=lambda key: next(i.reference for i in scoped if i.key == key))
        st.button("Ouvrir cet historique", on_click=navigate, args=("Incidents",), kwargs={"incident": incident})
    else:
        st.info("Aucun incident vérifié pour cet équipement. Consulte les fiches à vérifier dans Documents.")
    reports = [r for r in records if r.equipment == selected]
    if reports:
        st.caption(f"{len(reports)} rapport(s) associé(s), dont {sum(not r.validated for r in reports)} à vérifier.")


def incidents_view(documents, records, items, catalog):
    st.subheader("Historique des incidents")
    status = st.selectbox("Dernier état documenté", ["Tous", "Résolu", "Non résolu", "Inconnu", "À clarifier"])
    options = ["Tous"] + sorted({item.equipment for item in items})
    eq = st.selectbox("Équipement concerné", options)
    filtered = [item for item in items if (status == "Tous" or item.status == status)
                and (eq == "Tous" or item.equipment == eq)]
    if not filtered:
        st.info("Aucun incident ne correspond aux filtres. Les fiches non vérifiées sont exclues par défaut.")
        return
    st.dataframe(incident_rows(filtered), hide_index=True, width="stretch")
    selected = choose("Ouvrir un incident", [i.key for i in filtered], key="incident_choice",
                      format_func=lambda key: next(f"{i.reference} · {i.equipment}" for i in filtered if i.key == key))
    item = next(i for i in filtered if i.key == selected)
    st.markdown("**Évolution documentée**")
    st.text(f"{item.reference} · {item.equipment} · Dernier état : {item.status}")
    if not item.chronology_complete:
        st.warning("Un rapport n'est pas daté. Le dernier état ne peut pas être établi avec certitude.")
    if item.status == "À clarifier":
        st.warning("Des rapports de même date donnent des résultats différents. Aucune conclusion unique n'est retenue.")
    if not item.validated:
        st.warning("Cet historique contient des extractions à vérifier.")
    for record in item.events:
        event_source(record, documents, expanded=len(item.events) == 1)
    st.button("Chercher des incidents similaires", on_click=navigate,
              args=("Cas similaires",), kwargs={"incident": item.key})


def similar_view(documents, records, items, catalog):
    st.subheader("Retrouver des précédents utiles")
    st.caption("Rapprochement par symptômes, catégories de composants et termes décrivant le problème. Un cas proche ne prouve pas une cause commune.")
    labels = {item.key: f"{item.reference} · {item.equipment}" for item in items}
    seed_options = [""] + list(labels)
    previous = st.session_state.get("incident_choice", "")
    if "similar_seed" not in st.session_state and previous in labels:
        st.session_state.similar_seed = previous
    seed_key = choose("Partir d'un incident connu (facultatif)", seed_options, key="similar_seed",
                      format_func=lambda key: labels.get(key, "Décrire un nouveau problème"))
    seed = next((item for item in items if item.key == seed_key), None)
    symptoms = sorted(set().union(*(symptom_types(r.value("symptoms")) for r in records)))
    components = sorted({component_type(r.value("component")) for r in records} - {"Non renseigné"})
    seed_symptom = next(iter(sorted(symptom_types(seed.events[-1].value("symptoms")))), "") if seed else ""
    seed_component = component_type(seed.events[-1].value("component")) if seed else ""
    with st.form("similar_form"):
        description = st.text_input("Décrire le problème", placeholder="Ex. : roulement qui chauffe et fortes vibrations")
        a, b = st.columns(2)
        with a:
            symptom = st.selectbox("Symptôme", [""] + symptoms,
                index=([""] + symptoms).index(seed_symptom) if seed_symptom in symptoms else 0,
                format_func=lambda s: s or "Tous")
            component = st.selectbox("Catégorie de composant", [""] + components,
                index=([""] + components).index(seed_component) if seed_component in components else 0,
                format_func=lambda s: s or "Toutes")
        with b:
            kind = st.selectbox("Type d'équipement", ["", "Pompe", "Moteur", "Compresseur"],
                                format_func=lambda s: s or "Tous")
            result_filter = st.selectbox("Résultat à retrouver", ["Tous", "Résolu", "Non résolu", "Inconnu", "À clarifier"])
        submitted = st.form_submit_button("Retrouver les cas", type="primary")
    if submitted:
        results = similar_incidents(items, query=description, symptom=symptom,
            component=component, equipment_type=kind, catalog=catalog, exclude=seed_key)
        st.session_state.similar_result = (st.session_state.workspace,
            [(item.key, reasons) for item, reasons in results
             if result_filter == "Tous" or item.status == result_filter])
    saved = st.session_state.get("similar_result")
    if not saved or saved[0] != st.session_state.workspace:
        st.info("Choisis un symptôme, un composant ou une description, puis lance la recherche.")
        return
    matches = [(next((item for item in items if item.key == key), None), reasons)
               for key, reasons in saved[1]]
    matches = [(item, reasons) for item, reasons in matches if item is not None]
    st.caption(f"{len(matches)} cas trouvé(s) · {min(len(matches), 12)} premier(s) affiché(s) · rapprochement documentaire, sans recommandation automatique")
    for item, reasons in matches[:12]:
        with st.container(border=True):
            st.text(f"{item.reference} · {item.equipment} · Dernier état : {item.status}")
            st.caption(" · ".join(reasons) or "Filtres sélectionnés")
            actions = list(dict.fromkeys(r.value("action") for r in item.events if r.value("action")))
            st.text("Actions documentées : " + " → ".join(actions))
            st.text("Rapports : " + ", ".join(r.report for r in item.events))
            st.button("Voir les étapes et les preuves", key=f"similar_{item.key}",
                      on_click=navigate, args=("Incidents",), kwargs={"incident": item.key})


def library_view(documents, records, overrides, invalidate):
    st.subheader("Bibliothèque et informations sourcées")
    query = st.text_input("Rechercher dans la bibliothèque", placeholder="Nom, équipement ou mot contenu dans un rapport")
    state_filter = st.selectbox("Vérification des fiches", ["Toutes", "Vérifiées", "À vérifier"])
    by_doc = {r.document_id: r for r in records}
    filtered = [d for d in documents.values()
        if (not query or normalized(query) in normalized(d.name + " " + " ".join(p.text for p in d.pages)))
        and (state_filter == "Toutes" or by_doc[d.id].validated == (state_filter == "Vérifiées"))]
    rows = [{"Document": d.name, "Incident": by_doc[d.id].incident,
             "Équipement": by_doc[d.id].equipment,
             "Date": by_doc[d.id].event_date or "Non renseignée",
             "Fiche": by_doc[d.id].origin} for d in filtered]
    if rows:
        st.dataframe(rows, hide_index=True, width="stretch")
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        st.download_button("Exporter cet inventaire", output.getvalue(), "inventaire-rapports.csv", "text/csv")
    if not filtered:
        st.info("Aucun document ne correspond. Les imports se font dans la colonne de gauche de l'espace Mes documents.")
        return
    selected = choose("Document à consulter", [d.id for d in filtered], key="document_choice",
                      format_func=lambda key: documents[key].name)
    document = documents[selected]
    record = by_doc[selected]
    st.caption(record.origin)
    for page in document.pages:
        with st.expander(f"Texte source · {page.label}", expanded=len(document.pages) == 1):
            st.code(page.text, language=None, wrap_lines=True)
    st.download_button("Télécharger le texte extrait", "\n\n".join(
        f"{p.label}\n{p.text}" for p in document.pages), document.name + ".txt", "text/plain")
    st.markdown("**Informations de la fiche**")
    st.dataframe([{"Champ": label, "Valeur": record.value(key) or "Non renseigné",
                   "Source": record.facts[key].page if key in record.facts else "—"}
                  for key, label in FIELDS.items()], hide_index=True, width="stretch")
    with st.expander("Corriger une information et vérifier sa source"):
        field_key = st.selectbox("Information à corriger", list(FIELDS), format_func=FIELDS.get)
        fact = record.facts.get(field_key)
        # Les valeurs de formulaire sont rechargées quand le champ ou le document change.
        token = f"{selected}:{field_key}:{record.value(field_key)}"
        with st.form(f"correction_{token}"):
            value = st.text_input("Valeur exacte dans le rapport", value=fact.value if fact else "")
            labels = [page.label for page in document.pages]
            page = st.selectbox("Page source", labels,
                index=labels.index(fact.page) if fact and fact.page in labels else 0)
            quote = st.text_area("Extrait qui justifie cette valeur", value=fact.quote if fact else "")
            save = st.form_submit_button("Enregistrer la correction")
        if save:
            try:
                overrides[selected] = correct_fact(record, document, field_key, value, page, quote)
                invalidate()
                st.session_state.flash = "Correction enregistrée. La fiche doit être validée à nouveau."
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    a, b = st.columns(2)
    with a:
        if st.button("Valider les informations présentes", disabled=record.validated):
            try:
                overrides[selected] = validate_record(record, document)
                invalidate()
                st.session_state.flash = "Fiche validée par l'utilisateur."
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    with b:
        if st.button("Remettre à vérifier", disabled=not record.validated):
            overrides[selected] = replace(record, validated=False, origin="Vérification demandée")
            invalidate()
            st.rerun()
    st.caption("La validation humaine porte sur les informations présentes et leurs extraits. Elle ne complète pas les données absentes. Les corrections et validations sont sauvegardées sur ce Mac.")
    with st.expander("Retirer des documents de cet espace"):
        removals = st.multiselect("Documents à retirer", list(documents), format_func=lambda key: documents[key].name)
        if st.button("Retirer la sélection", disabled=not removals):
            for document_id in removals:
                documents.pop(document_id, None)
                overrides.pop(document_id, None)
            invalidate()
            st.rerun()
