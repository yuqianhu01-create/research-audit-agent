import argparse
import json
from pathlib import Path

from audit_agent import audit_record, canonical_key, load_registry
from publish_agent import to_website_candidate
from research_agent import collect_section, dedupe


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SECTIONS = ["academic", "industry", "ai-aging", "ai-apps"]


def count_passed_by_section(audited):
    counts = {section: 0 for section in SECTIONS}
    for item in audited:
        if item.get("audit_status") == "passed" and item.get("section") in counts:
            counts[item["section"]] += 1
    return counts


def select_balanced_passed(audited, minimum_per_section):
    selected = []
    for section in SECTIONS:
        section_items = [
            item for item in audited
            if item.get("section") == section and item.get("audit_status") == "passed"
        ]
        section_items.sort(key=lambda item: item.get("relevance_score", 0), reverse=True)
        selected.extend(section_items[:minimum_per_section])
    return selected


def write_outputs(candidates, audited, selected, issue):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "candidates.json").write_text(json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA_DIR / "audit_report.json").write_text(json.dumps(audited, ensure_ascii=False, indent=2), encoding="utf-8")
    website_records = [to_website_candidate(item, issue=issue) for item in selected]
    package = {"issue": issue, "records": website_records}
    (DATA_DIR / "website_candidates.json").write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--section", default="all", choices=["all"] + SECTIONS)
    parser.add_argument("--minimum-per-section", type=int, default=5)
    parser.add_argument("--initial-limit", type=int, default=8)
    parser.add_argument("--max-rounds", type=int, default=4)
    parser.add_argument("--days-back", type=int, default=365)
    parser.add_argument("--issue", default="next")
    args = parser.parse_args()

    sections = SECTIONS if args.section == "all" else [args.section]
    registry = load_registry()
    candidates = []
    audited_by_key = {}

    for round_index in range(args.max_rounds):
        limit = args.initial_limit + round_index * args.initial_limit
        days_back = args.days_back + round_index * 180
        print(f"Pipeline round {round_index + 1}: limit={limit}, days_back={days_back}")

        for section in sections:
            existing_passed = [
                item for item in audited_by_key.values()
                if item.get("section") == section and item.get("audit_status") == "passed"
            ]
            if len(existing_passed) >= args.minimum_per_section:
                continue
            try:
                new_candidates = collect_section(section, limit=limit, days_back=days_back)
            except Exception as exc:
                print(f"Pipeline warning: collect failed for {section}: {exc}")
                continue
            candidates = dedupe(candidates + new_candidates)

        for candidate in candidates:
            key = canonical_key(candidate)
            if key in audited_by_key:
                continue
            audited_by_key[key] = audit_record(candidate, registry, days_back=args.days_back)

        counts = count_passed_by_section(audited_by_key.values())
        print(f"Passed counts: {counts}")
        if all(counts.get(section, 0) >= args.minimum_per_section for section in sections):
            break

    audited = list(audited_by_key.values())
    selected = select_balanced_passed(audited, args.minimum_per_section)
    write_outputs(candidates, audited, selected, args.issue)

    final_counts = count_passed_by_section(audited)
    print(f"Final passed counts: {final_counts}")
    print(f"Selected website records: {len(selected)}")
    missing = {section: args.minimum_per_section - final_counts.get(section, 0) for section in sections if final_counts.get(section, 0) < args.minimum_per_section}
    if missing:
        print(f"Warning: minimum not reached for {missing}; inspect audit_report.json failure reasons.")


if __name__ == "__main__":
    main()
