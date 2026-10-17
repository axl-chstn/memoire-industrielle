"""Prépare le modèle local sans compte, clé API ni service payant."""

from __future__ import annotations

import http.client
import os
import platform
import shutil
import subprocess
import tarfile
import time
import urllib.request
from pathlib import Path

from memoire.local_llm import (
    LOCAL_HOST,
    LOCAL_MODEL,
    LOCAL_PORT,
    LocalModelError,
    require_local_model,
)

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".local" / "ollama"
DOWNLOAD = "https://ollama.com/download/ollama-darwin.tgz"


def find_binary() -> Path:
    bundled = RUNTIME / "ollama"
    if bundled.is_file():
        return bundled
    installed = shutil.which("ollama")
    if installed:
        return Path(installed)
    mac_app = Path("/Applications/Ollama.app/Contents/Resources/ollama")
    if mac_app.is_file():
        return mac_app
    if platform.system() != "Darwin":
        raise RuntimeError("Installe Ollama depuis https://ollama.com/download puis relance cette commande.")
    print("Téléchargement d'Ollama depuis sa source officielle…", flush=True)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    archive = ROOT / ".local" / "ollama-darwin.tgz"
    if not hasattr(tarfile, "data_filter"):
        raise RuntimeError("Utilise Python 3.12 ou une version de Python 3.11 à jour pour installer Ollama automatiquement.")
    urllib.request.urlretrieve(DOWNLOAD, archive)
    # Le filtre data refuse les chemins et liens sortant du dossier d'installation.
    with tarfile.open(archive) as bundle:
        bundle.extractall(RUNTIME, filter="data")
    if not bundled.is_file():
        raise RuntimeError("Archive Ollama incomplète ; consulte le téléchargement officiel.")
    return bundled


def server_available() -> bool:
    connection = http.client.HTTPConnection(LOCAL_HOST, LOCAL_PORT, timeout=1)
    try:
        connection.request("GET", "/api/version")
        return connection.getresponse().status == 200
    except (OSError, http.client.HTTPException):
        return False
    finally:
        connection.close()


def ensure_runtime() -> None:
    binary = find_binary()
    cache = ROOT / ".cache"
    cache.mkdir(exist_ok=True)
    environment = dict(os.environ)
    environment.update({
        "OLLAMA_HOST": f"{LOCAL_HOST}:{LOCAL_PORT}",
        "OLLAMA_MODELS": str(cache / "ollama-models"),
        "OLLAMA_NO_CLOUD": "1",
        "OLLAMA_CONTEXT_LENGTH": "4096",
        "OLLAMA_MAX_LOADED_MODELS": "1",
        "OLLAMA_NUM_PARALLEL": "1",
    })
    if not server_available():
        with (cache / "ollama.log").open("ab") as logs:
            process = subprocess.Popen([str(binary), "serve"], env=environment,
                                       stdout=logs, stderr=logs, start_new_session=True)
        (cache / "ollama.pid").write_text(str(process.pid))
        for _ in range(40):
            if server_available():
                break
            if process.poll() is not None:
                raise RuntimeError("Le moteur local n'a pas démarré ; consulte .cache/ollama.log.")
            time.sleep(0.25)
        else:
            raise RuntimeError("Le moteur local met trop de temps à démarrer. Relance la commande.")
    try:
        require_local_model()
    except LocalModelError:
        print(f"Téléchargement initial du modèle {LOCAL_MODEL} (environ 2,5 Go)…", flush=True)
        subprocess.run([str(binary), "pull", LOCAL_MODEL], env=environment, check=True)
        require_local_model()
    print("Modèle local prêt. Aucune clé API, aucun appel payant.", flush=True)


if __name__ == "__main__":
    try:
        ensure_runtime()
    except (RuntimeError, OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"Préparation locale impossible : {exc}") from exc
