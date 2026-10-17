"""Contrôles de régression connus : python -m scripts.evaluate_rives [--local]."""

import argparse
import csv
import json
import time
from dataclasses import asdict
from pathlib import Path

from memoire.answers import generate_answer
from memoire.documents import chunk_document, read_document
from memoire.knowledge import extract_record, normalized, validate_record
from memoire.qa import search_reports
from memoire.retrieval import SearchIndex

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data/essais_rives"

# Repères de régression : ils ne sont jamais utilisés par le moteur de réponse.
REQUIRED = {
    1: ["resolu", "2026-09-07"],
    2: ["2026-09-02", "40 minutes", "non resolu", "2026-09-07", "50 minutes"],
    3: ["filtre d aspiration obstrue", "hypothese non confirmee"],
    4: ["40 minutes", "50 minutes"],
    5: ["2026-09-11", "non resolu"],
    6: ["hypothese non confirmee"],
    7: ["2026-09-11", "5 8", "7 1"],
    8: ["inconnu", "position", "inconnue"],
    9: ["non renseignee", "remplacement du ventilateur"],
    10: ["joint", "65 minutes"],
    11: ["diagnostic non renseigne"],
    12: ["intervention non renseigne", "inconnu", "ne prouve pas"],
    13: ["non confirme"],
    14: ["resolu", "40 minutes"],
    15: ["remplacement non realise", "non resolu"],
    16: ["INC501", "INC507", "2026-09-07", "2026-09-18"],
    17: ["INC507", "2026-09-18", "non resolu"],
}
FORBIDDEN = {
    7: ["aucune information sur les pressions"],
    8: ["est anterieur", "est posterieur", "est celui du rapport RAP508"],
    12: ["aucune intervention n a ete realisee", "explicitement non resolue"],
    14: ["aucune mesure vibratoire ou acoustique n a ete effectuee"],
}


def run(*, local=False):
    documents = [read_document(p.name, p.read_bytes()) for p in sorted((CORPUS / "rapports").glob("*.txt"))]
    records = [validate_record(extract_record(d), d) for d in documents]
    index = SearchIndex([p for d in documents for p in chunk_document(d)])
    with (CORPUS / "questions.csv").open(encoding="utf-8-sig") as f:
        cases = list(csv.DictReader(f, delimiter=";"))
    results = []
    for number, case in enumerate(cases, 1):
        start = time.monotonic()
        question = case["Question"]
        hits = search_reports(index, question, records, top_k=4)
        answer = generate_answer(question, hits, local=local, records=records)
        reports = {r.report for r in records if r.document_id in {h.passage.document_id for h in hits}}
        expected = set(case["Rapports à consulter"].split(";")) if case["Rapports à consulter"] else set()
        source_ok = expected <= reports if expected else not hits
        visible = normalized(answer.text + " " + " ".join(line for _, lines in answer.sections for line in lines))
        content_ok = all(normalized(t) in visible for t in REQUIRED.get(number, []))
        content_ok &= all(normalized(t) not in normalized(answer.text) for t in FORBIDDEN.get(number, []))
        # Pour les questions libres, vérifier les extraits littéraux affichés.
        # Leur pertinence et leur contexte doivent aussi être relus manuellement.
        if answer.generated:
            rendered_sources = [h for h in hits if h.passage.text in answer.text]
            content_ok &= bool(rendered_sources)
        result = {"numero": number, "question": question, **asdict(answer),
                  "sources": [{"id": f"S{i}", "rapport": h.passage.source,
                               "texte": h.passage.text} for i, h in enumerate(hits, 1)],
                  "rapports": sorted(reports), "attendu": case["Réponse attendue"],
                  "controle_sources": source_ok, "controle_reperes": content_ok,
                  "secondes": round(time.monotonic() - start, 2)}
        results.append(result)
        print(f"{'OK' if source_ok and content_ok else 'ÉCHEC'} | {number}/20 | {question}", flush=True)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", action="store_true", help="Appeler le modèle réellement installé pour les questions libres")
    args = parser.parse_args()
    results = run(local=args.local)
    successes = sum(r["controle_sources"] and r["controle_reperes"] for r in results)
    output = ROOT / ".cache/evaluation_rives_apres.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps({"local": args.local, "resultats": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{successes}/{len(results)} contrôles de régression connus réussis. Relire les réponses : ces repères ne prouvent pas leur fidélité complète et ne constituent pas une validation indépendante.")
    raise SystemExit(0 if successes == len(results) else 1)


if __name__ == "__main__":
    main()
