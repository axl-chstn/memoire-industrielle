"""Évaluation reproductible : python -m scripts.evaluate [--semantic]."""

import argparse
import json
import os
from pathlib import Path

from memoire.demo import load_demo
from memoire.documents import chunk_document
from memoire.retrieval import MODEL_NAME, SearchIndex

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description="Évalue les passages retrouvés sur le corpus fictif.")
    parser.add_argument("--semantic", action="store_true")
    args = parser.parse_args()
    encoder = None
    if args.semantic:
        os.environ.setdefault("HF_HOME", str(ROOT / ".cache" / "huggingface"))
        from sentence_transformers import SentenceTransformer

        encoder = SentenceTransformer(MODEL_NAME, device="cpu", trust_remote_code=False)
    index = SearchIndex([p for d in load_demo() for p in chunk_document(d)], encoder)
    cases = json.loads((ROOT / "data/evaluation.json").read_text())
    successes = 0
    for case in cases:
        hits = index.search(case["question"], top_k=3)
        actual = {hit.passage.source.split("_")[0] for hit in hits}
        expected = set(case["expected_sources"])
        success = expected <= actual if expected else not actual
        successes += success
        print(f"{'OK' if success else 'ÉCHEC'} | {case['question']} | {', '.join(sorted(actual)) or 'aucun extrait'}")
    print(f"\n{successes}/{len(cases)} cas réussis. Ce jeu fictif ne mesure pas la qualité sur des documents réels ni celle des réponses du LLM.")
    raise SystemExit(0 if successes == len(cases) else 1)


if __name__ == "__main__":
    main()
