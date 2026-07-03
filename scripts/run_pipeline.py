import argparse
import json
from pathlib import Path

from audit_agent import audit_record, canonical_key, canonical_keys, load_registry
from publish_agent import source_allowed_for_section, to_website_candidate
from research_agent import collect_section, dedupe


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SECTIONS = ["academic", "industry", "ai-aging", "ai-apps"]

SEVERE_ISSUE_PREFIXES = ("http_error:", "bad_http_status:", "fetch_failed:", "unknown_or_generic_source_type:")
SEVERE_ISSUES = {
    "duplicate_previous_issue",
    "missing_title",
    "missing_source",
    "missing_url",
    "invalid_url",
    "missing_or_unparsed_date",
    "future_publication_date",
    "low_topic_relevance",
    "page_appears_dead_or_discontinued",
    "page_appears_paywalled_or_not_publicly_readable",
    "page_text_does_not_match_candidate_title",
    "disallowed_user_generated_or_blog_source",
    "blocked_media_domain_due_to_prior_404_paywall_or_subjective_source",
    "industry_requires_commercial_or_authoritative_source",
    "industry_clinical_trial_lacks_antiaging_or_pipeline_signal",
    "industry_item_lacks_healthy_aging_sector_signal",
    "ai_apps_clinical_trial_lacks_product_or_digital_health_signal",
    "ai_apps_requires_product_company_or_regulatory_source",
    "ai_aging_requires_ai_and_aging_signal",
}
SOFT_REVIEW_SECTIONS = {"industry", "ai-apps"}


def normalized_title(item):
    import re
    return re.sub(r"[^a-z0-9]+", " ", (item.get("title") or "").lower()).strip()


def is_publishable(item):
    if not source_allowed_for_section(item):
        return False
    if item.get("audit_status") == "passed":
        return True
    if item.get("section") not in SOFT_REVIEW_SECTIONS or item.get("audit_status") != "needs_review":
        return False
    issues = item.get("audit_issues", [])
    if any(issue in SEVERE_ISSUES or issue.startswith(SEVERE_ISSUE_PREFIXES) for issue in issues):
        return False
    return True


def count_publishable_by_section(audited):
    counts = {section: 0 for section in SECTIONS}
    for item in audited:
        if is_publishable(item) and item.get("section") in counts:
            counts[item["section"]] += 1
    return counts


def count_selected_by_section(selected):
    counts = {section: 0 for section in SECTIONS}
    for item in selected:
        if item.get("section") in counts:
            counts[item["section"]] += 1
    return counts


def select_balanced_publishable(audited, minimum_per_section, registry):
    selected = []
    selected_keys = set(registry)
    selected_titles = set()
    for section in SECTIONS:
        section_items = [
            item for item in audited
            if item.get("section") == section and is_publishable(item)
        ]
        section_items.sort(
            key=lambda item: (
                item.get("audit_status") == "passed",
                item.get("relevance_score", 0),
                item.get("published_date", ""),
            ),
            reverse=True,
        )
        for item in section_items:
            item_keys = set(canonical_keys(item))
            title_key = normalized_title(item)
            if item_keys & selected_keys or (title_key and title_key in selected_titles):
                continue
            selected.append(item)
            selected_keys.update(item_keys)
            if title_key:
                selected_titles.add(title_key)
            if sum(1 for selected_item in selected if selected_item.get("section") == section) >= minimum_per_section:
                break
    return selected


def write_outputs(candidates, audited, selected, issue, registry):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "candidates.json").write_text(json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA_DIR / "audit_report.json").write_text(json.dumps(audited, ensure_ascii=False, indent=2), encoding="utf-8")
    website_records = [to_website_candidate(item, issue=issue) for item in selected]
    package = {"issue": issue, "records": website_records}
    (DATA_DIR / "website_candidates.json").write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
    used_keys = set(registry)
    for item in selected:
        used_keys.update(canonical_keys(item))
    (DATA_DIR / "published_registry.json").write_text(
        json.dumps({"used_keys": sorted(used_keys)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--section", default="all", choices=["all"] + SECTIONS)
    parser.add_argument("--minimum-per-section", type=int, default=5)
    parser.add_argument("--initial-limit", type=int, default=8)
    parser.add_argument("--max-rounds", type=int, default=5)
    parser.add_argument("--days-back", type=int, default=365)
    parser.add_argument("--issue", default="next")
    args = parser.parse_args()

    sections = SECTIONS if args.section == "all" else [args.section]
    registry = load_registry()
    candidates = []
    audited_by_key = {}

    for round_index in range(args.max_rounds):
        limit = args.initial_limit + round_index * args.initial_limit
        days_back = args.days_back + round_index * 120
        print(f"Pipeline round {round_index + 1}: limit={limit}, days_back={days_back}")

        for section in sections:
            existing = [
                item for item in audited_by_key.values()
                if item.get("section") == section and is_publishable(item)
            ]
            if len(existing) >= args.minimum_per_section:
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

        counts = count_publishable_by_section(audited_by_key.values())
        preview_selected = select_balanced_publishable(audited_by_key.values(), args.minimum_per_section, registry)
        selected_counts = count_selected_by_section(preview_selected)
        print(f"Publishable counts: {counts}; selected distinct counts: {selected_counts}")
        if all(selected_counts.get(section, 0) >= args.minimum_per_section for section in sections):
            break

    audited = list(audited_by_key.values())
    selected = select_balanced_publishable(audited, args.minimum_per_section, registry)
    write_outputs(candidates, audited, selected, args.issue, registry)

    final_counts = count_publishable_by_section(audited)
    selected_counts = count_selected_by_section(selected)
    print(f"Final publishable counts: {final_counts}")
    print(f"Final selected distinct counts: {selected_counts}")
    print(f"Selected website records: {len(selected)}")
    missing = {
        section: args.minimum_per_section - selected_counts.get(section, 0)
        for section in sections
        if selected_counts.get(section, 0) < args.minimum_per_section
    }
    if missing:
        print(f"Warning: minimum not reached for {missing}; inspect audit_report.json failure reasons.")


if __name__ == "__main__":
    main()
