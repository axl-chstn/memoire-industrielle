"""Essai réel de la sélection locale de passages : python -m scripts.validate_local."""

import json
from pathlib import Path

from memoire.answers import generate_answer
from memoire.demo import load_demo
from memoire.documents import chunk_document
from memoire.retrieval import SearchIndex


def main():
    index = SearchIndex([p for d in load_demo() for p in chunk_document(d)])
    questions = ["L'incident INC05 est-il résolu ?",
                 "L'incident INC04 est-il résolu ?",
                 "L'incident INC07 est-il résolu ?"]
    results = []
    for question in questions:
        hits = index.search(question)
        answer = generate_answer(question, hits, local=True)
        result = {"question": question, "generated": answer.generated,
                  "sources": [h.passage.source for h in hits], "answer": answer.text,
                  "notice": answer.notice}
        results.append(result)
        print(json.dumps(result, ensure_ascii=False), flush=True)
    output = Path(__file__).resolve().parents[1] / ".cache" / "validation-locale.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    if not all(item["generated"] for item in results):
        print("Une sélection au moins a été remplacée par le mode de lecture des sources. Relire les notices et les passages ; ce test ne valide pas toute leur pertinence.")


if __name__ == "__main__":
    main()
