"""Reproducible retrieval regression evaluation; does not grade agent judgment."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def evaluate(search, data):
    report = []
    for case in data["cases"]:
        payload = search(case["query"], data["manifest"])
        names = [skill["name"] for skill in payload.get("results", [])]
        expected = case["acceptable"]
        decision = payload.get("routing", {}).get("decision")
        top_hit = bool(names) and names[0] in expected
        hit = top_hit if expected else decision in case.get("decisions", [case.get("decision")])
        hit = hit and decision not in case.get("forbidden_decisions", [])
        reciprocal_rank = next((1 / (i + 1) for i, name in enumerate(names) if name in expected), 0)
        report.append({"id": case["id"], "passed": hit, "top": names[0] if names else None,
                       "top_1_match": top_hit if expected else None,
                       "decision": decision, "reciprocal_rank": reciprocal_rank,
                       "recall_at_5": any(name in expected for name in names[:5]) if expected else None})
    retrieval = [item for item in report if item["recall_at_5"] is not None]
    return {"cases": len(report), "passed": sum(item["passed"] for item in report),
            "retrieval_cases": len(retrieval),
            "top_1": sum(item["top_1_match"] for item in retrieval) / max(1, len(retrieval)),
            "recall_at_5": sum(item["recall_at_5"] for item in retrieval) / max(1, len(retrieval)),
            "mrr": sum(item["reciprocal_rank"] for item in retrieval) / max(1, len(retrieval)),
            "scope": "curated regression set; not production accuracy or agent selection confidence",
            "results": report}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", type=Path, default=ROOT / "skills/maestro/scripts")
    parser.add_argument("--cases", type=Path, default=ROOT / "tests/fixtures/routing-benchmark.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(args.engine.resolve()))
    from search_skills import search_skills
    result = evaluate(search_skills, json.loads(args.cases.read_text(encoding="utf-8")))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] == result["cases"] else 1)
