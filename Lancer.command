#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
task_python=""
for candidate in .venv/bin/python python3.12 python3; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(sys.version_info[:2] != (3, 12))' 2>/dev/null; then
    task_python="$candidate"
    break
  fi
done
if [ -z "$task_python" ]; then
  echo "Installe Python 3.12 depuis python.org, puis relance ce fichier."
  read -r -p "Appuie sur Entrée pour fermer."
  exit 1
fi
# La recherche fonctionne aussi sans modèle ; conserver un lancement utilisable en cas d'échec.
"$task_python" -m scripts.bootstrap
if ! .venv/bin/python -m scripts.local_runtime; then
  echo "Le modèle local n'est pas encore prêt. La recherche et les extraits restent disponibles."
fi
exec .venv/bin/python -m streamlit run app.py --server.address 127.0.0.1
