"""Installation de référence Python 3.12, sans téléchargement de modèle par défaut."""

from __future__ import annotations

import argparse
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def environment_python(folder: Path) -> Path:
    return folder / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--venv", type=Path, default=ROOT / ".venv")
    parser.add_argument("--dev", action="store_true", help="Installer aussi les outils de test")
    parser.add_argument("--semantic", action="store_true", help="Installer la recherche par embeddings")
    parser.add_argument("--model", action="store_true", help="Préparer Ollama et Qwen (environ 2,5 Go)")
    parser.add_argument("--run", action="store_true", help="Ouvrir le serveur local après installation")
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 12):
        parser.error("L'installation verrouillée utilise Python 3.12. Lance ce script avec Python 3.12.")
    folder = args.venv.expanduser().resolve()
    python = environment_python(folder)
    if not python.exists():
        venv.EnvBuilder(with_pip=True).create(folder)
    subprocess.run([str(python), "-c", "import sys; raise SystemExit(sys.version_info[:2] != (3, 12))"], check=True)
    locks = ["requirements-dev.lock" if args.dev else "requirements.lock"]
    if args.semantic:
        locks.append("requirements-semantic.lock")
    install = [str(python), "-m", "pip", "install", "--require-hashes"]
    for lock in locks:
        install.extend(["-r", str(ROOT / lock)])
    subprocess.run(install, cwd=ROOT, check=True)
    subprocess.run([str(python), "-m", "pip", "check"], cwd=ROOT, check=True)
    if args.model:
        subprocess.run([str(python), "-m", "scripts.local_runtime"], cwd=ROOT, check=True)
    print("Installation prête. Aucun service d'API payant n'est utilisé.", flush=True)
    if args.run:
        subprocess.run([str(python), "-m", "streamlit", "run", "app.py", "--server.address", "127.0.0.1"], cwd=ROOT, check=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"Installation interrompue : {exc}. Les documents existants sont conservés.") from exc
