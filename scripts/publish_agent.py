import argparse
import json
import re
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def slugify(value):
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value or "").strip("-").lower()
    return value[:70] or "untitled"


def to_website_candidate(record, issue="next"):
    section = record.get("section", "academic")
    title = record.get("title", "")
    return {
        "id": f"{issue}-{section}-{slugify(title)}",
        "channel": section,
        "group": record.get("priority_reason") or record.get("article_type") or "待分类",
        "publishedAt": record.get("published_date", ""),
        "contentType": "current",
        "title": title,
        "summaryDraft": "",
        "opportunityDraft": "",
        "auditStatus": record.get("audit_status"),
        "auditIssues": record.get("audit_issues", []),
        "sourceName": record.get("source", ""),
        "displayType": record.get("article_type", ""),
        "evidenceLevel": "A-direct source" if record.get("audit_status") == "passed" else "needs human review",
        "sources": [
            {
                "name": record.get("source", "source"),
                "url": record.get("url", ""),
                "type": record.get("source_type", ""),
                "titleEn": title,
            }
        ],
        "rawCandidate": record,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DATA_DIR / "audit_report.json"))
    parser.add_argument("--issue", default="next")
    parser.add_argument("--include-needs-review", action="store_true")
    args = parser.parse_args()

    audited = json.loads(Path(args.input).read_text(encoding="utf-8"))
    allowed = {"passed"}
    if args.include_needs_review:
        allowed.add("needs_review")
    output = [to_website_candidate(item, args.issue) for item in audited if item.get("audit_status") in allowed]
    package = {
        "generatedAt": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "issue": args.issue,
        "records": output,
    }
    output_path = DATA_DIR / "website_candidates.json"
    output_path.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Publishing Agent wrote {len(output)} website candidate records to {output_path}")


if __name__ == "__main__":
    main()
