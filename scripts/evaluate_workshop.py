"""Évaluation de la V2 : python -m scripts.evaluate_workshop [--semantic]."""

import argparse
import json
import os
from pathlib import Path

from memoire.answers import generate_answer
from memoire.demo import load_workshop, workshop_catalog
from memoire.documents import chunk_document
from memoire.knowledge import extract_record, incidents
from memoire.qa import expand_aliases, search_reports
from memoire.retrieval import MODEL_NAME, SearchIndex

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--semantic", action="store_true")
    args = parser.parse_args()
    encoder = None
    if args.semantic:
        os.environ.setdefault("HF_HOME", str(ROOT / ".cache" / "huggingface"))
        from sentence_transformers import SentenceTransformer

        encoder = SentenceTransformer(MODEL_NAME, device="cpu", trust_remote_code=False)
    documents = load_workshop()
    records = [extract_record(d) for d in documents]
    items = incidents(records)
    catalog = {e["id"]: e for e in workshop_catalog()["equipment"]}
    index = SearchIndex([p for d in documents for p in chunk_document(d)], encoder)
    cases = json.loads((ROOT / "data" / "atelier_evaluation.json").read_text())
    successes = 0
    for case in cases:
        question = case["question"]
        hits = search_reports(index, expand_aliases(question, catalog), records)
        found = {h.passage.source.split("_")[0] for h in hits}
        if "expected_equipment" in case:
            success = bool(hits) and all(case["expected_equipment"] in h.passage.equipment for h in hits)
        else:
            expected = set(case["expected_sources"])
            success = expected <= found if expected else not found
        if "expected_status" in case:
            target = next(i for i in items if i.reference in question)
            answer = generate_answer(question, hits, records=records)
            success &= target.status == case["expected_status"] and answer.documented
            if case["expected_date"]:
                success &= case["expected_date"] in answer.text
        successes += bool(success)
        print(f"{'OK' if success else 'ÉCHEC'} | {question} | {', '.join(sorted(found)) or 'aucun passage'}")
    print(f"\n{successes}/{len(cases)} cas V2. Scénarios fictifs ; la sélection libre de passages par le LLM n'est pas évaluée par ce script.")
    raise SystemExit(0 if successes == len(cases) else 1)


if __name__ == "__main__":
    main()
