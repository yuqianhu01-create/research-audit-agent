import argparse
import hashlib
import json
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DISALLOWED_DOMAINS = ["wikipedia.org", "zhihu.com", "xiaohongshu.com", "reddit.com", "medium.com"]


def canonical_key(record):
    for field in ("doi", "pmid", "url"):
        value = (record.get(field) or "").strip().lower()
        if value:
            return f"{field}:{value}"
    title = (record.get("title") or "").strip().lower()
    return "title:" + hashlib.sha256(title.encode("utf-8")).hexdigest()


def load_registry():
    path = DATA_DIR / "published_registry.json"
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    return set(data.get("used_keys", []))


def check_url(url):
    if not url:
        return False, "missing_url"
    lowered = url.lower()
    if any(domain in lowered for domain in DISALLOWED_DOMAINS):
        return False, "disallowed_source"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "anti-aging-briefing-demo-audit-agent/0.1"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status = getattr(response, "status", 0)
            if 200 <= status < 400:
                return True, f"http_{status}"
            return False, f"http_{status}"
    except urllib.error.HTTPError as exc:
        return False, f"http_{exc.code}"
    except Exception as exc:
        return False, type(exc).__name__


def parse_date(value):
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            parsed = datetime.strptime(value, fmt).date()
            if fmt == "%Y":
                return parsed.replace(month=1, day=1)
            if fmt == "%Y-%m":
                return parsed.replace(day=1)
            return parsed
        except ValueError:
            pass
    return None


def audit_record(record, registry, days_back):
    issues = []
    verified = dict(record)
    key = canonical_key(record)
    verified["canonical_key"] = key

    if key in registry:
        issues.append("duplicate_previous_issue")
    if not record.get("title"):
        issues.append("missing_title")
    if not record.get("source"):
        issues.append("missing_source")

    link_ok, link_status = check_url(record.get("url", ""))
    verified["link_status"] = link_status
    if not link_ok:
        issues.append("link_not_accessible")

    published = parse_date(record.get("published_date", ""))
    verified["date_status"] = "parsed" if published else "missing_or_unparsed"
    if not published:
        issues.append("missing_or_unparsed_date")
    else:
        if published < date.today() - timedelta(days=days_back):
            issues.append("outside_date_window")

    if issues:
        verified["audit_status"] = "failed" if any(i in issues for i in ["duplicate_previous_issue", "link_not_accessible", "missing_or_unparsed_date"]) else "needs_review"
    else:
        verified["audit_status"] = "passed"
    verified["audit_issues"] = issues
    verified["audited_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    return verified


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DATA_DIR / "candidates.json"))
    parser.add_argument("--days-back", type=int, default=365)
    args = parser.parse_args()

    candidates = json.loads(Path(args.input).read_text(encoding="utf-8"))
    registry = load_registry()
    audited = [audit_record(record, registry, args.days_back) for record in candidates]
    output_path = DATA_DIR / "audit_report.json"
    output_path.write_text(json.dumps(audited, ensure_ascii=False, indent=2), encoding="utf-8")
    passed = sum(1 for item in audited if item["audit_status"] == "passed")
    print(f"Audit Agent wrote {len(audited)} records to {output_path}; passed={passed}")


if __name__ == "__main__":
    main()
