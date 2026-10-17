#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  task_python=""
  for candidate in python3.13 python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(sys.version_info < (3, 11))' 2>/dev/null; then
      task_python="$candidate"
      break
    fi
  done
  if [ -z "$task_python" ]; then
    echo "Installe Python 3.11 ou supérieur depuis python.org, puis relance ce fichier."
    read -r -p "Appuie sur Entrée pour fermer."
    exit 1
  fi
  "$task_python" -m venv .venv
fi
if ! .venv/bin/python -c 'import streamlit, numpy, pypdf' >/dev/null 2>&1; then
  .venv/bin/python -m pip install -r requirements.txt
fi
if ! .venv/bin/python -m scripts.local_runtime; then
  echo "Le modèle local n'est pas encore prêt. La recherche et les extraits restent disponibles."
fi
exec .venv/bin/python -m streamlit run app.py --server.address 127.0.0.1
