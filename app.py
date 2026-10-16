"""Interface de la maquette : python -m streamlit run app.py."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from memoire.answers import Answer, generate_answer, source_extracts
from memoire.demo import load_demo
from memoire.documents import chunk_document, read_document
from memoire.retrieval import MODEL_NAME, SearchIndex

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
os.environ.setdefault("HF_HOME", str(ROOT / ".cache" / "huggingface"))
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

st.set_page_config(page_title="Mémoire Industrielle", page_icon="⚙️", layout="wide")
st.markdown("""<style>
.block-container {max-width:1180px;padding-top:2.4rem;padding-bottom:3rem;}
h1 {letter-spacing:-1.7px;line-height:1.08 !important;font-weight:750 !important;}
h2,h3 {letter-spacing:-.5px;}
[data-testid="stMetric"] {background:white;border:1px solid #e1e8e9;border-radius:14px;padding:16px 20px;}
[data-testid="stSidebar"] {border-right:1px solid #dee6e7;}
[data-testid="stChatMessage"] {background:white;border:1px solid #e1e8e9;border-radius:14px;}
.eyebrow {color:#087f75;font-size:.75rem;letter-spacing:.15em;font-weight:700;margin-bottom:14px;}
.hero-copy {color:#60747c;font-size:1.1rem;max-width:680px;line-height:1.6;}
.brand {font-size:1.1rem;font-weight:750;color:#142b34;margin-bottom:3px;}
.brand-sub {color:#60747c;font-size:.8rem;margin-bottom:24px;}
div.stButton > button {border-radius:9px;}
</style>""", unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def load_encoder():
    # Seul le modèle public est partagé ; aucun corpus ni embedding utilisateur n'est mis en cache global.
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME, device="cpu", trust_remote_code=False)


def configured_key() -> str:
    key = os.getenv("OPENAI_API_KEY", "")
    if not key:
        try:
            key = st.secrets.get("OPENAI_API_KEY", "")
        except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
            pass
    return key


def invalidate():
    st.session_state.pop("search_index", None)
    st.session_state.pop("index_signature", None)
    st.session_state["history"] = []


def export_exchange(question, answer, hits, engine) -> str:
    lines = ["# Mémoire Industrielle — résultat documentaire", "", f"Question : {question}",
             f"Recherche : {engine}",
             f"Réponse : {'synthèse LLM' if answer.generated else 'lecture des sources'}", "",
             answer.text, "", "## Passages sources"]
    for i, hit in enumerate(hits, 1):
        p = hit.passage
        lines.extend(["", f"### [S{i}] {p.source} — {p.location}", "", p.text])
    if answer.notice:
        lines.extend(["", answer.notice])
    return "\n".join(lines)


def render_exchange(exchange, position):
    question, answer, hits, engine = exchange
    with st.chat_message("user"):
        st.text(question)
    with st.chat_message("assistant"):
        st.caption(f"{'Synthèse avec sources' if answer.generated else 'Lecture des sources'} · {engine}")
        if answer.generated or not hits:
            # Le texte généré ne peut pas charger d'images ou de liens externes.
            st.text(answer.text)
        else:
            st.write("Voici les passages retrouvés. Ouvre les sources pour consulter les faits exacts.")
        if answer.notice:
            st.caption(answer.notice)
        for i, hit in enumerate(hits, 1):
            p = hit.passage
            with st.expander(f"[S{i}] {p.source} · {p.location}", expanded=(i == 1)):
                st.code(p.text, language=None, wrap_lines=True)
        st.download_button("Exporter ce résultat", export_exchange(question, answer, hits, engine),
                           file_name="recherche-maintenance.md", mime="text/markdown",
                           key=f"export_{position}")


if "documents" not in st.session_state:
    st.session_state.documents = {d.id: d for d in load_demo()}
    st.session_state.history = []

with st.sidebar:
    st.markdown('<div class="brand">◈ Mémoire Industrielle</div>'
                '<div class="brand-sub">Votre expérience, accessible.</div>', unsafe_allow_html=True)
    st.subheader("Votre base documentaire")
    st.caption("PDF avec texte, TXT ou Markdown · 10 Mo par fichier")
    uploads = st.file_uploader("Ajouter des rapports", type=["pdf", "txt", "md"],
                               accept_multiple_files=True)
    if st.button("Importer les fichiers", type="primary", disabled=not uploads,
                 width="stretch"):
        if len(uploads) > 30 or sum(f.size for f in uploads) > 30 * 1024 * 1024:
            st.error("Importe au maximum 30 fichiers et 30 Mo à la fois.")
        else:
            count = 0
            for upload in uploads:
                try:
                    document = read_document(upload.name, upload.getvalue())
                    if document.id not in st.session_state.documents:
                        if len(st.session_state.documents) >= 50:
                            st.warning("Limite de la maquette : 50 documents. Retire des documents avant de poursuivre.")
                            break
                        st.session_state.documents[document.id] = document
                        count += 1
                    for warning in document.warnings:
                        st.warning(f"{document.name} : {warning}")
                except ValueError as exc:
                    st.error(f"{upload.name} : {exc}")
            if count:
                invalidate()
                st.success(f"{count} document(s) ajouté(s).")
            else:
                st.info("Aucun nouveau document ajouté ; les doublons sont ignorés.")

    st.divider()
    with st.expander("Rédiger les réponses avec une IA"):
        st.caption("La recherche fonctionne déjà sans clé. Pour une synthèse, la question et les extraits sélectionnés seront envoyés à OpenAI.")
        user_key = st.text_input("Clé API OpenAI", type="password", key="user_api_key",
                                 placeholder="Facultative")
        api_key = user_key.strip() or configured_key()
        llm_enabled = st.checkbox("Activer les synthèses OpenAI", value=False)
        model_name = st.text_input("Modèle", value=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"))
        if llm_enabled and not api_key:
            st.info("Ajoute une clé API pour activer les synthèses. Un abonnement ChatGPT ne fournit pas de crédits API.")
    with st.expander("Réglages de recherche"):
        semantic_enabled = st.checkbox("Chercher aussi par le sens", value=False,
            help="Nécessite requirements-semantic.txt. Le modèle public est téléchargé au premier usage ; les rapports restent sur la machine qui exécute l'application.")
        top_k = st.slider("Nombre de passages à consulter", 1, 8, 4)
        st.caption("Les références d'équipement présentes dans la question sont respectées comme filtres exacts.")
    st.caption("Les documents importés restent en mémoire pendant cette session. Ils ne sont pas envoyés sur GitHub.")

documents = list(st.session_state.documents.values())
equipment_options = sorted({e for d in documents for e in d.equipment})
passages = [p for d in documents for p in chunk_document(d)]
demo_count = sum(d.demo for d in documents)

st.markdown('<div class="eyebrow">CAPITALISER · RETROUVER · TRANSMETTRE</div>', unsafe_allow_html=True)
st.markdown("<h1>Les bons rapports.<br>Au bon moment.</h1>", unsafe_allow_html=True)
st.markdown('<p class="hero-copy">Retrouvez ce qui a déjà été observé, tenté et résolu sur vos équipements. Chaque recherche vous ramène aux documents.</p>', unsafe_allow_html=True)
cols = st.columns(3)
cols[0].metric("Rapports disponibles", len(documents))
cols[1].metric("Équipements repérés", len(equipment_options))
cols[2].metric("Passages consultables", len(passages))
if demo_count:
    st.caption(f"Démonstration : {demo_count} rapport(s) fictif(s) du TD sont présents dans la base.")

search_tab, documents_tab, guide_tab = st.tabs(["Interroger la mémoire", "Documents", "Prise en main"])
with documents_tab:
    st.subheader("Les documents de votre session")
    if documents:
        st.dataframe([{"Document": d.name, "Origine": "Fictif · TD" if d.demo else "Importé",
                       "Équipements": ", ".join(d.equipment) or "Non repérés",
                       "Pages ou textes": len(d.pages)} for d in documents],
                      width="stretch", hide_index=True)
        selected_to_remove = st.multiselect("Documents à retirer", options=[d.id for d in documents],
            format_func=lambda document_id: st.session_state.documents[document_id].name)
        if st.button("Retirer la sélection", disabled=not selected_to_remove):
            for document_id in selected_to_remove:
                st.session_state.documents.pop(document_id, None)
            invalidate()
            st.rerun()
    else:
        st.info("Ajoute tes rapports ou charge les exemples pour commencer.")
    if st.button("Charger les 12 rapports de démonstration"):
        demo_documents = load_demo()
        new_demo_count = sum(d.id not in st.session_state.documents for d in demo_documents)
        if len(st.session_state.documents) + new_demo_count > 50:
            st.warning("Retire quelques documents pour respecter la limite de 50.")
        else:
            st.session_state.documents.update({d.id: d for d in demo_documents})
            invalidate()
            st.rerun()
    st.caption("Les imports et les résultats ne sont pas conservés après la fin de la session. Les réglages de recherche n'altèrent jamais les fichiers d'origine.")

with guide_tab:
    st.subheader("Un premier essai en trois étapes")
    st.write("1. Utilise les exemples ou ajoute tes rapports dans la colonne de gauche.")
    st.write("2. Pose une question précise : équipement, symptôme, intervention ou résultat.")
    st.write("3. Ouvre les sources, vérifie les faits et exporte le résultat si nécessaire.")
    st.info("Sans clé API, tu consultes les extraits retrouvés. Avec les synthèses activées, une IA rédige une réponse à partir de ces extraits.")
    st.write("Une intervention réalisée ne prouve pas qu'une panne est résolue. Une information absente reste inconnue.")
    st.caption("Maquette documentaire : pas d'OCR, de connexion à une GMAO ni de diagnostic automatique. Les questions sont indépendantes : reformule l'équipement à chaque fois.")

with search_tab:
    st.subheader("Que cherchez-vous dans l'historique ?")
    equipment = st.selectbox("Limiter à un équipement", ["Tous les équipements"] + equipment_options)
    suggested = ["Qu'a-t-on fait pour les vibrations du compresseur C01 ?",
                 "L'incident INC07 sur la pompe P01 est-il résolu ?",
                 "Quelle intervention a été réalisée sur M01_RA ?"]
    if not st.session_state.history:
        st.caption("Essaie une de ces questions :")
        for n, label in enumerate(suggested):
            if st.button(label, key=f"suggestion_{n}"):
                st.session_state.pending_question = label
    for position, exchange in enumerate(st.session_state.history):
        render_exchange(exchange, position)
    question = st.chat_input("Ex. : qu'a-t-on essayé pour les vibrations sur C01 ?",
                             disabled=not documents, max_chars=2000)
    question = question or st.session_state.pop("pending_question", None)
    if question:
        engine = "Mots-clés"
        signature = hashlib.sha256(("|".join(sorted(d.id for d in documents))
                                    + str(semantic_enabled)).encode()).hexdigest()
        if st.session_state.get("index_signature") != signature:
            encoder = None
            if semantic_enabled:
                try:
                    with st.spinner("Préparation de la recherche par le sens. Le premier chargement peut prendre quelques minutes…"):
                        encoder = load_encoder()
                except Exception:
                    st.warning("La recherche par le sens est indisponible. La recherche par mots-clés reste active. Consulte le guide d'installation pour activer les embeddings.")
            with st.spinner("Préparation des documents…"):
                try:
                    index = SearchIndex(passages, encoder)
                except Exception:
                    st.warning("Le calcul des embeddings a échoué. Recherche par mots-clés utilisée.")
                    index = SearchIndex(passages)
            st.session_state.search_index = index
            st.session_state.index_signature = signature
        index = st.session_state.search_index
        if index.encoder is not None:
            engine = "Sens + mots-clés"
        try:
            hits = index.search(question, top_k=top_k,
                equipment=None if equipment == "Tous les équipements" else equipment)
        except Exception:
            st.warning("La recherche par le sens a échoué. Recherche par mots-clés utilisée pour cette question.")
            hits = SearchIndex(passages).search(question, top_k=top_k,
                equipment=None if equipment == "Tous les équipements" else equipment)
            engine = "Mots-clés"
        with st.spinner("Lecture des passages…"):
            try:
                answer = generate_answer(question, hits,
                    api_key=api_key if llm_enabled else "", model=model_name.strip())
            except Exception:
                answer = Answer(source_extracts(hits), notice=(
                    "La synthèse IA est indisponible. Vérifie la clé API, les crédits, le modèle et la connexion. Les sources restent consultables."))
        exchange = (question, answer, hits, engine)
        st.session_state.history.append(exchange)
        st.session_state.history = st.session_state.history[-10:]
        render_exchange(exchange, "new")
