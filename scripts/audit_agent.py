import argparse
import hashlib
import json
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
)

DIRECT_SOURCE_TYPES = {
    "pubmed", "doi", "journal_article", "preprint", "clinical_trial",
    "company_news", "company_site", "official_product_page", "regulator",
    "market_research", "professional_media", "credible_media",
    "clinical_trial_database",
}

DISALLOWED_DOMAINS = {
    "wikipedia.org", "zhihu.com", "xiaohongshu.com", "reddit.com",
    "medium.com", "substack.com"
}

BLOCKED_MEDIA_DOMAINS = {
    "businessinsider.com", "www.businessinsider.com",
    "wired.com", "www.wired.com",
    "theatlantic.com", "www.theatlantic.com",
}

DEAD_PAGE_PATTERNS = [
    r"\bno longer operating\b", r"\bdomain (?:is )?for sale\b",
    r"\bpage not found\b", r"\b404\b", r"\bwhoops\b",
    r"\baccount suspended\b", r"\bwebsite coming soon\b",
    r"\bunder construction\b",
]

PAYWALL_PATTERNS = [
    r"\byou'?ve read your last free article\b",
    r"\byour last free article\b", r"\bsubscribe to (?:read|listen|continue)\b",
    r"\bsubscribe now\b", r"\bstart your free trial\b",
    r"\balready a subscriber\b", r"\bpremium newsletters\b",
]

STOPWORDS = {
    "the", "and", "for", "with", "from", "into", "that", "this",
    "official", "company", "platform", "health", "aging", "ageing",
    "anti", "study", "article", "trial"
}

MIN_RELEVANCE_SCORE = 1


class PageTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_ignored = False
        self.in_title = False
        self.title = []
        self.text = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self.in_ignored = True
        if tag == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"}:
            self.in_ignored = False
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_ignored:
            return
        cleaned = re.sub(r"\s+", " ", data).strip()
        if not cleaned:
            return
        if self.in_title:
            self.title.append(cleaned)
        self.text.append(cleaned)


def canonical_key(record):
    for field in ("doi", "pmid", "nct_id", "arxiv_id", "url"):
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


def parse_date(value):
    if not value:
        return None
    value = str(value).strip()
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


def tokens(value):
    value = re.sub(r"[^A-Za-z0-9]+", " ", value or "").lower()
    return {item for item in value.split() if len(item) >= 4 and item not in STOPWORDS}


def fetch(url, timeout=30):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/json,*/*"})
    context = ssl.create_default_context()
    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        raw = response.read(900_000)
        content_type = response.headers.get("Content-Type", "")
        charset_match = re.search(r"charset=([\w-]+)", content_type, re.I)
        charset = charset_match.group(1) if charset_match else "utf-8"
        try:
            body = raw.decode(charset, errors="replace")
        except LookupError:
            body = raw.decode("utf-8", errors="replace")
        return {
            "status": getattr(response, "status", 200),
            "final_url": response.geturl(),
            "content_type": content_type,
            "body": body,
        }


def extract_page_text(html):
    parser = PageTextParser()
    parser.feed(html)
    title = " ".join(parser.title)
    body = " ".join(parser.text)
    return title, re.sub(r"\s+", " ", body)[:120_000]


def clinicaltrials_api_url(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc != "clinicaltrials.gov":
        return None
    match = re.search(r"/study/(NCT\d+)", parsed.path, re.I)
    if not match:
        return None
    return f"https://clinicaltrials.gov/api/v2/studies/{match.group(1).upper()}"


def check_url_and_page(record):
    url = record.get("url", "")
    issues = []
    details = {"link_status": "not_checked"}
    if not url:
        return ["missing_url"], details

    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc.lower()
    if not parsed.scheme.startswith("http") or not domain:
        issues.append("invalid_url")
    if any(domain.endswith(bad) for bad in DISALLOWED_DOMAINS):
        issues.append("disallowed_user_generated_or_blog_source")
    if domain in BLOCKED_MEDIA_DOMAINS:
        issues.append("blocked_media_domain_due_to_prior_404_paywall_or_subjective_source")
    if record.get("source_type") not in DIRECT_SOURCE_TYPES:
        issues.append(f"unknown_or_generic_source_type:{record.get('source_type')}")
    if issues:
        return issues, details

    try:
        fetched = fetch(clinicaltrials_api_url(url) or url)
    except urllib.error.HTTPError as exc:
        return [f"http_error:{exc.code}"], {"link_status": f"http_{exc.code}"}
    except Exception as exc:
        return [f"fetch_failed:{exc.__class__.__name__}"], {"link_status": exc.__class__.__name__}

    status = fetched["status"]
    details["link_status"] = f"http_{status}"
    details["final_url"] = fetched["final_url"]
    if status < 200 or status >= 400:
        issues.append(f"bad_http_status:{status}")

    if "json" in fetched.get("content_type", "").lower() or fetched["final_url"].endswith(".json"):
        page_text = fetched["body"][:120_000]
    else:
        title, text = extract_page_text(fetched["body"])
        details["page_title"] = title[:300]
        page_text = f"{title} {text}"

    lowered = page_text.lower()
    dead = [pattern for pattern in DEAD_PAGE_PATTERNS if re.search(pattern, lowered)]
    paywall = [pattern for pattern in PAYWALL_PATTERNS if re.search(pattern, lowered)]
    if dead:
        issues.append("page_appears_dead_or_discontinued")
    if paywall:
        issues.append("page_appears_paywalled_or_not_publicly_readable")

    expected = tokens(" ".join([
        record.get("title", ""), record.get("source", ""),
        record.get("doi", ""), record.get("pmid", ""), record.get("nct_id", ""),
    ]))
    page_tokens = tokens(page_text)
    if expected and record.get("source_type") not in {"company_site", "official_product_page", "regulator", "clinical_trial_database"}:
        overlap = expected & page_tokens
        details["topic_overlap_count"] = len(overlap)
        if len(overlap) < 2:
            issues.append("page_text_does_not_match_candidate_title")

    return issues, details


def audit_record(record, registry, days_back):
    issues = []
    verified = dict(record)
    key = canonical_key(record)
    verified["canonical_key"] = key

    if key in registry:
        issues.append("duplicate_previous_issue")
    if not record.get("title"):
        issues.append("missing_title")
    elif " " not in record.get("title", "").strip() and len(record.get("title", "")) > 30:
        issues.append("title_parse_suspicious")
    if not record.get("source"):
        issues.append("missing_source")
    if int(record.get("relevance_score", 0)) < MIN_RELEVANCE_SCORE and record.get("source_type") not in {"company_site", "official_product_page", "regulator"}:
        issues.append("low_topic_relevance")

    link_issues, link_details = check_url_and_page(record)
    issues.extend(link_issues)
    verified.update(link_details)

    published = parse_date(record.get("published_date", ""))
    verified["date_status"] = "parsed" if published else "missing_or_unparsed"
    if not published:
        if record.get("source_type") in {"company_site", "official_product_page", "regulator", "clinical_trial_database"}:
            issues.append("needs_human_date_check")
        else:
            issues.append("missing_or_unparsed_date")
    else:
        if published > date.today():
            issues.append("future_publication_date")
        if published < date.today() - timedelta(days=days_back):
            issues.append("outside_date_window")

    hard_failures = {
        "duplicate_previous_issue",
        "missing_or_unparsed_date",
        "future_publication_date",
        "low_topic_relevance",
        "page_appears_dead_or_discontinued",
        "page_appears_paywalled_or_not_publicly_readable",
        "page_text_does_not_match_candidate_title",
    }
    hard_prefixes = ("http_error:", "bad_http_status:", "fetch_failed:", "unknown_or_generic_source_type:")
    if any(issue in hard_failures or issue.startswith(hard_prefixes) for issue in issues):
        verified["audit_status"] = "failed"
    elif issues:
        verified["audit_status"] = "needs_review"
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
    counts = {}
    for item in audited:
        counts[item["audit_status"]] = counts.get(item["audit_status"], 0) + 1
    print(f"Audit Agent wrote {len(audited)} records to {output_path}; counts={counts}")


if __name__ == "__main__":
    main()
