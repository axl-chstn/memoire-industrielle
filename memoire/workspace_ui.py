"""Export et restauration explicites de l'espace actif."""

import hashlib

import streamlit as st

from memoire.storage import Snapshot, StorageError, decode, encode, merge


def backup_view(documents, overrides, invalidate):
    name = st.session_state.workspace
    current = Snapshot(name, documents, overrides, st.session_state.storage_revisions[name])
    st.caption("La sauvegarde automatique est active. Cet export contient les textes extraits, leurs pages et les fiches corrigées. Il ne contient pas les PDF originaux, les modèles ni les questions.")
    try:
        st.download_button("Exporter cet espace", encode(current),
            "memoire-atelier.json" if name == "Atelier fictif" else "memoire-personnelle.json",
            "application/json", key=f"backup_{name}", width="stretch")
    except StorageError as exc:
        st.error(str(exc))
    upload = st.file_uploader("Restaurer une sauvegarde JSON", type=["json"],
                              max_upload_size=100, key=f"restore_{name}")
    if upload is None:
        return
    try:
        content = upload.getvalue()
        restored = decode(content, imported=True)
        combined, added, duplicates = merge(current, restored)
        st.caption(f"{len(restored.documents)} rapport(s) · {added} à ajouter · {duplicates} déjà présent(s), conservés sans modification.")
        st.info("Les fiches ajoutées seront à vérifier. Les validations conservées dans un fichier importé ne sont pas reprises automatiquement.")
        token = hashlib.sha256(content).hexdigest()
        if st.button("Fusionner la sauvegarde", disabled=not added, key=f"merge_{name}_{token}"):
            documents.update(combined.documents)
            overrides.update(combined.overrides)
            invalidate()
            st.session_state.flash = f"{added} rapport(s) restauré(s) et sauvegardé(s) sur ce Mac. Fiches à vérifier dans Documents."
            st.rerun()
    except StorageError as exc:
        st.error(str(exc))
