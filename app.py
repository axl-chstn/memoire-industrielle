"""Mémoire Industrielle V2 : atelier, incidents, cas similaires et RAG local."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import streamlit as st

from memoire.answers import Answer, generate_answer, source_extracts
from memoire.demo import load_workshop, workshop_catalog
from memoire.documents import chunk_document, read_document
from memoire.knowledge import extract_record, incidents
from memoire.local_llm import model_status
from memoire.qa import expand_aliases, search_reports
from memoire.retrieval import MODEL_NAME, SearchIndex
from memoire.views import (
    ROUTES,
    equipment_view,
    incidents_view,
    library_view,
    overview,
    similar_view,
)

ROOT = Path(__file__).resolve().parent
os.environ.setdefault("HF_HOME", str(ROOT / ".cache" / "huggingface"))
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
st.set_page_config(page_title="Mémoire Industrielle · Atelier", page_icon="⚙️", layout="wide")
st.markdown("""<style>
.block-container {max-width:1250px;padding-top:2rem;padding-bottom:3rem;}
h1 {letter-spacing:-1.5px;font-weight:750 !important;}
h2,h3 {letter-spacing:-.4px;}
[data-testid="stMetric"] {background:white;border:1px solid #dce7e7;border-radius:14px;padding:14px 18px;}
[data-testid="stSidebar"] {border-right:1px solid #dee6e7;}
[data-testid="stChatMessage"] {background:white;border:1px solid #e1e8e9;border-radius:14px;}
.eyebrow {color:#087f75;font-size:.75rem;letter-spacing:.14em;font-weight:700;}
.brand {font-size:1.1rem;font-weight:750;color:#142b34;}
.brand-sub {color:#60747c;font-size:.8rem;margin-bottom:18px;}
div.stButton > button {border-radius:9px;}
@media (max-width:700px) {
  [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) {display:grid;grid-template-columns:1fr 1fr;gap:10px;}
  [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="stColumn"] {width:100% !important;min-width:0 !important;}
  [data-testid="stMetric"] {padding:10px 14px;}
}
</style>""", unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def load_encoder():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME, device="cpu", trust_remote_code=False)


def invalidate():
    for key in ("search_index", "index_signature", "similar_result"):
        st.session_state.pop(key, None)
    st.session_state.history = []


def personal_workspace():
    st.session_state.workspace = "Mes documents"
    st.session_state.route = "Documents"


def export_exchange(question, answer, hits, engine):
    lines = ["# Mémoire Industrielle — résultat documentaire", "", f"Question : {question}",
             f"Recherche : {engine}", "", answer.text]
    for title, entries in answer.sections:
        lines.extend(["", "## " + title, *entries])
    lines.extend(["", "## Passages sources"])
    for i, hit in enumerate(hits, 1):
        p = hit.passage
        lines.extend(["", f"### [S{i}] {p.source} — {p.location}", "", p.text])
    lines.extend(["", answer.notice])
    return "\n".join(lines)


def render_exchange(exchange, position):
    question, answer, hits, engine = exchange
    with st.chat_message("user"):
        st.text(question)
    with st.chat_message("assistant"):
        mode = "Réponse documentée" if answer.documented else "Synthèse locale" if answer.generated else "Lecture des sources"
        st.caption(f"{mode} · {engine}")
        if answer.generated or answer.documented or not hits:
            st.text(answer.text)
        elif not answer.sections:
            st.write("Voici les passages retrouvés. Ouvre les sources pour consulter les faits exacts.")
        for title, entries in answer.sections:
            st.markdown("**" + title + "**")
            for entry in entries:
                st.text(entry)
        if answer.notice:
            st.caption(answer.notice)
        for i, hit in enumerate(hits, 1):
            p = hit.passage
            with st.expander(f"[S{i}] {p.source} · {p.location}", expanded=i == 1):
                st.code(p.text, language=None, wrap_lines=True)
        st.download_button("Exporter ce résultat", export_exchange(question, answer, hits, engine),
                           "recherche-maintenance.md", "text/markdown", key=f"export_{position}")


if "workspaces" not in st.session_state:
    # Une éventuelle session V1 est conservée dans l'espace personnel.
    previous = st.session_state.get("documents", {})
    personal = {key: doc for key, doc in previous.items() if not doc.demo}
    st.session_state.workspaces = {
        "Atelier fictif": {d.id: d for d in load_workshop()}, "Mes documents": personal}
    st.session_state.overrides = {"Atelier fictif": {}, "Mes documents": {}}
    st.session_state.history = []
    st.session_state.route = "Vue d'ensemble"

with st.sidebar:
    st.markdown('<div class="brand">◈ Mémoire Industrielle</div>'
                '<div class="brand-sub">Atelier · Version 2</div>', unsafe_allow_html=True)
    workspace = st.selectbox("Espace de travail", ["Atelier fictif", "Mes documents"], key="workspace")
    if st.session_state.get("previous_workspace") != workspace:
        invalidate()
        st.session_state.previous_workspace = workspace
    documents = st.session_state.workspaces[workspace]
    overrides = st.session_state.overrides[workspace]
    st.session_state.documents = documents
    if workspace == "Atelier fictif":
        st.caption("Atelier Horizon · données entièrement fictives. Tes documents personnels restent dans un espace séparé.")
        st.button("Importer mes rapports", on_click=personal_workspace, width="stretch")
    else:
        st.caption("PDF avec texte, TXT ou Markdown · 10 Mo par fichier")
        uploads = st.file_uploader("Ajouter des rapports", type=["pdf", "txt", "md"], accept_multiple_files=True)
        if st.button("Importer les fichiers", type="primary", disabled=not uploads, width="stretch"):
            if len(uploads) > 30 or sum(f.size for f in uploads) > 30 * 1024 * 1024:
                st.error("Limite : 30 fichiers et 30 Mo par import.")
            else:
                added = 0
                for upload in uploads:
                    try:
                        doc = read_document(upload.name, upload.getvalue())
                        if doc.id not in documents:
                            if len(documents) >= 100:
                                st.warning("Limite : 100 documents par espace.")
                                break
                            documents[doc.id] = doc
                            added += 1
                        for warning in doc.warnings:
                            st.warning(f"{doc.name} : {warning}")
                    except ValueError as exc:
                        st.error(f"{upload.name} : {exc}")
                if added:
                    invalidate()
                    st.success(f"{added} document(s) ajouté(s). Les fiches extraites sont à vérifier dans Documents.")
                else:
                    st.info("Aucun nouveau document ajouté ; les doublons sont ignorés.")
    st.divider()
    local_ready, local_notice = model_status()
    with st.expander("IA locale · sans frais d'API"):
        if local_ready:
            st.success(local_notice)
        else:
            st.info(local_notice)
        llm_enabled = st.checkbox("Rédiger les réponses sur cet ordinateur", value=local_ready,
                                 disabled=not local_ready, key="local_summaries_enabled")
        st.caption("Aucune clé nécessaire. La question et les extraits restent sur la machine qui exécute la maquette.")
    with st.expander("Recherche et vérification"):
        semantic_enabled = st.checkbox("Chercher aussi par le sens", value=False,
            help="Utilise le modèle d'embeddings local. Le premier chargement peut nécessiter un téléchargement public.")
        top_k = st.slider("Passages pour une réponse", 1, 8, 4)
        include_drafts = st.checkbox("Inclure les fiches à vérifier dans les vues métier", value=False)
    st.caption("Documents, corrections et validations restent dans cette session. Les modèles publics sont conservés sur le Mac.")

records = [overrides.get(doc.id) or extract_record(doc) for doc in documents.values()]
items = incidents(records, include_drafts=include_drafts)
catalog = {e["id"]: e for e in workshop_catalog()["equipment"]} if workspace == "Atelier fictif" else {}
equipment_codes = sorted({code for d in documents.values() for code in d.equipment})
passages = [p for document in documents.values() for p in chunk_document(document)]

st.markdown('<div class="eyebrow">CAPITALISER · RETROUVER · TRANSMETTRE</div>', unsafe_allow_html=True)
st.title("La mémoire de votre atelier")
st.caption("Atelier Horizon · scénario fictif de janvier à mars 2026" if workspace == "Atelier fictif"
           else "Votre espace personnel · informations extraites à vérifier")
cols = st.columns(4)
cols[0].metric("Rapports", len(documents))
cols[1].metric("Équipements", len(equipment_codes))
cols[2].metric("Incidents suivis", len(items))
cols[3].metric("À suivre", sum(item.status != "Résolu" for item in items))
route = st.radio("Explorer la mémoire", ROUTES, horizontal=True, key="route", label_visibility="collapsed")
if st.session_state.get("flash"):
    st.success(st.session_state.pop("flash"))

if route == "Vue d'ensemble":
    overview(documents, records, items, catalog)
elif route == "Équipements":
    equipment_view(documents, records, items, catalog)
elif route == "Incidents":
    incidents_view(documents, records, items, catalog)
elif route == "Cas similaires":
    similar_view(documents, records, items, catalog)
elif route == "Documents":
    library_view(documents, records, overrides, invalidate)
    if workspace == "Atelier fictif" and len(documents) < 30:
        if st.button("Restaurer les 30 rapports fictifs"):
            documents.update({d.id: d for d in load_workshop()})
            invalidate()
            st.rerun()
else:
    st.subheader("Interroger les rapports et leurs suivis")
    st.caption("Les réponses structurées utilisent les fiches vérifiées. La synthèse locale reste à contrôler dans les sources.")
    equipment = st.selectbox("Limiter à un équipement", ["Tous"] + equipment_codes)
    if not st.session_state.history:
        examples = ["L'incident INC104 est-il résolu ?", "Qu'a-t-on essayé pour les vibrations sur C03 ?",
                    "Quels rapports parlent de la pompe d'alimentation ?"] if workspace == "Atelier fictif" else []
        for i, example in enumerate(examples):
            if st.button(example, key=f"suggestion_{i}"):
                st.session_state.pending_question = example
    for position, exchange in enumerate(st.session_state.history):
        render_exchange(exchange, position)
    question = st.chat_input("Ex. : qu'a-t-on essayé et quel résultat a été constaté ?",
                             disabled=not documents, max_chars=2000)
    question = question or st.session_state.pop("pending_question", None)
    if question:
        engine = "Mots-clés"
        signature = hashlib.sha256((workspace + "|" + "|".join(sorted(documents))
                                    + str(semantic_enabled)).encode()).hexdigest()
        if st.session_state.get("index_signature") != signature:
            encoder = None
            if semantic_enabled:
                try:
                    with st.spinner("Chargement de la recherche par le sens…"):
                        encoder = load_encoder()
                except Exception:
                    st.warning("Recherche par le sens indisponible. Les mots-clés restent actifs.")
            try:
                index = SearchIndex(passages, encoder)
            except Exception:
                st.warning("Calcul des embeddings indisponible. Les mots-clés sont utilisés.")
                index = SearchIndex(passages)
            st.session_state.search_index = index
            st.session_state.index_signature = signature
        index = st.session_state.search_index
        if index.encoder is not None:
            engine = "Sens + mots-clés"
        query = expand_aliases(question, catalog)
        eq = None if equipment == "Tous" else equipment
        try:
            hits = search_reports(index, query, records, top_k=top_k, equipment=eq)
        except Exception:
            st.warning("Recherche par le sens indisponible pour cette question ; mots-clés utilisés.")
            hits = search_reports(SearchIndex(passages), query, records, top_k=top_k, equipment=eq)
            engine = "Mots-clés"
        with st.spinner("Lecture des rapports et de leurs suivis…"):
            try:
                answer = generate_answer(question, hits, local=llm_enabled and local_ready, records=records)
            except Exception:
                answer = Answer(source_extracts(hits), notice="La synthèse locale est indisponible. Les sources restent consultables ; aucun service payant n'est utilisé.")
        exchange = (question, answer, hits, engine)
        st.session_state.history.append(exchange)
        st.session_state.history = st.session_state.history[-10:]
        render_exchange(exchange, "new")
