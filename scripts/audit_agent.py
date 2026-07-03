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
    "market_research", "professional_media", "credible_media", "industry_media",
    "investor_relations", "sec_filing", "conference",
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
SOFT_DATE_SOURCE_TYPES = {
    "company_site",
    "company_news",
    "official_product_page",
    "regulator",
    "clinical_trial_database",
    "investor_relations",
    "sec_filing",
}
SOFT_DATE_SECTIONS = {"industry", "ai-apps"}


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


def canonical_keys(record):
    keys = []
    for field in ("doi", "pmid", "nct_id", "arxiv_id", "url"):
        value = (record.get(field) or "").strip().lower()
        if value:
            keys.append(f"{field}:{value}")
    title = re.sub(r"\s+", " ", (record.get("title") or "").strip().lower())
    if title:
        keys.append("title:" + hashlib.sha256(title.encode("utf-8")).hexdigest())
    return keys or [canonical_key(record)]


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
    if parsed.netloc not in {"clinicaltrials.gov", "www.clinicaltrials.gov"}:
        return None
    match = re.search(r"/study/(NCT\d+)", parsed.path, re.I)
    if not match:
        return None
    return f"https://clinicaltrials.gov/api/v2/studies/{match.group(1).upper()}"


def pubmed_api_url(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc != "pubmed.ncbi.nlm.nih.gov":
        return None
    match = re.search(r"/(\d+)/?", parsed.path)
    if not match:
        return None
    params = urllib.parse.urlencode({"db": "pubmed", "id": match.group(1), "retmode": "xml"})
    return f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?{params}"


def check_url_and_page(record):
    url = record.get("url", "")
    issues = []
    details = {"link_status": "not_checked"}
    if not url:
        return ["missing_url"], details

    if record.get("source_type") == "clinical_trial" and record.get("nct_id"):
        return [], {
            "link_status": "official_registry_api_metadata",
            "final_url": url,
            "page_title": record.get("title", "")[:300],
            "page_excerpt": (record.get("abstract") or record.get("why_candidate") or "")[:1200],
        }

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
        fetched = fetch(pubmed_api_url(url) or clinicaltrials_api_url(url) or url)
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
        details["page_excerpt"] = re.sub(r"\s+", " ", page_text)[:1200]
    else:
        title, text = extract_page_text(fetched["body"])
        details["page_title"] = title[:300]
        page_text = f"{title} {text}"
        details["page_excerpt"] = text[:1200]

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
    if expected and record.get("source_type") not in {"company_site", "official_product_page", "regulator", "clinical_trial_database", "doi"}:
        overlap = expected & page_tokens
        details["topic_overlap_count"] = len(overlap)
        if len(overlap) < 2:
            issues.append("page_text_does_not_match_candidate_title")

    return issues, details


def section_policy_issues(record):
    section = record.get("section", "")
    source_type = record.get("source_type", "")
    text = " ".join([
        record.get("title", ""),
        record.get("abstract", ""),
        record.get("why_candidate", ""),
        record.get("source", ""),
    ]).lower()
    issues = []

    if section == "industry":
        allowed_sources = {
            "company_site", "company_news", "investor_relations", "sec_filing",
            "regulator", "clinical_trial", "clinical_trial_database",
            "industry_media", "professional_media", "credible_media",
            "market_research", "conference", "official_product_page",
        }
        if source_type not in allowed_sources:
            issues.append("industry_requires_commercial_or_authoritative_source")
        sector_terms = [
            "healthy aging", "healthy ageing", "longevity", "functional food",
            "nutraceutical", "supplement", "cosmetics", "skincare", "skin aging",
            "beauty", "biotech", "medical device", "wearable", "biological age",
            "nad", "nmn", "nicotinamide riboside", "senolytic", "senescence",
            "cellular reprogramming", "epigenetic reprogramming", "collagen",
            "microbiome", "menopause", "cognitive health", "metabolic health",
            "anti-aging", "healthspan",
        ]
        event_terms = [
            "r&d", "launch", "partnership", "collaboration", "funding",
            "financing", "investment", "acquisition", "merger", "sec filing",
            "investor relations", "approval", "clearance", "guidance",
            "clinical trial", "phase", "pipeline", "manufacturing", "market",
            "conference", "regulatory", "fda", "ema", "hsa", "nmpa",
        ]
        has_sector_signal = any(term in text for term in sector_terms)
        has_event_signal = any(term in text for term in event_terms)
        if source_type in {"clinical_trial", "clinical_trial_database"} and not (has_sector_signal and has_event_signal):
            issues.append("industry_clinical_trial_lacks_antiaging_or_pipeline_signal")
        elif source_type not in {"company_site", "company_news", "regulator", "investor_relations", "sec_filing", "market_research"} and not has_sector_signal:
            issues.append("industry_item_lacks_healthy_aging_sector_signal")

    if section == "ai-apps":
        allowed_product_sources = {"official_product_page", "company_site", "company_news", "regulator"}
        if source_type == "clinical_trial":
            has_digital_health_signal = any(
                term in text
                for term in [
                    "digital health", "wearable", "artificial intelligence", "machine learning",
                    "mobile app", "remote monitoring", "personalized nutrition", "older adults",
                    "healthy ageing", "healthy aging",
                ]
            )
            if not has_digital_health_signal:
                issues.append("ai_apps_clinical_trial_lacks_product_or_digital_health_signal")
        elif source_type not in allowed_product_sources:
            issues.append("ai_apps_requires_product_company_or_regulatory_source")

    if section == "ai-aging":
        has_ai = any(term in text for term in ["ai", "artificial intelligence", "machine learning", "deep learning", "model"])
        has_aging = any(term in text for term in ["aging", "ageing", "age-related", "longevity", "senescence", "biological age"])
        if not (has_ai and has_aging):
            issues.append("ai_aging_requires_ai_and_aging_signal")

    return issues


def audit_record(record, registry, days_back):
    issues = []
    verified = dict(record)
    key = canonical_key(record)
    verified["canonical_key"] = key
    issues.extend(section_policy_issues(record))

    if any(item_key in registry for item_key in canonical_keys(record)):
        issues.append("duplicate_previous_issue")
    if not record.get("title"):
        issues.append("missing_title")
    elif " " not in record.get("title", "").strip() and len(record.get("title", "")) > 30:
        issues.append("title_parse_suspicious")
    if not record.get("source"):
        issues.append("missing_source")
    if int(record.get("relevance_score", 0)) < MIN_RELEVANCE_SCORE and record.get("source_type") not in {
        "company_site", "company_news", "official_product_page", "regulator",
        "investor_relations", "sec_filing", "clinical_trial", "clinical_trial_database",
        "industry_media", "professional_media", "credible_media", "market_research",
        "conference",
    }:
        issues.append("low_topic_relevance")

    link_issues, link_details = check_url_and_page(record)
    issues.extend(link_issues)
    verified.update(link_details)

    if record.get("source_type") in {"pubmed", "doi", "journal_article", "preprint"}:
        page_title = (verified.get("page_title") or "").lower()
        source = (record.get("source") or "").lower()
        final_url = str(verified.get("final_url", ""))
        if source and page_title and source not in page_title and "eutils.ncbi.nlm.nih.gov" not in final_url:
            issues.append("source_name_not_confirmed_on_page")

    published = parse_date(record.get("published_date", ""))
    verified["date_status"] = "parsed" if published else "missing_or_unparsed"
    soft_date_source = (
        record.get("section") in SOFT_DATE_SECTIONS
        and record.get("source_type") in SOFT_DATE_SOURCE_TYPES
    )
    if not published:
        if soft_date_source:
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
        "source_name_not_confirmed_on_page",
        "industry_requires_commercial_or_authoritative_source",
        "industry_clinical_trial_lacks_antiaging_or_pipeline_signal",
        "industry_item_lacks_healthy_aging_sector_signal",
        "ai_apps_clinical_trial_lacks_product_or_digital_health_signal",
        "ai_apps_requires_product_company_or_regulatory_source",
        "ai_aging_requires_ai_and_aging_signal",
    }
    if soft_date_source:
        hard_failures.discard("missing_or_unparsed_date")
        hard_failures.discard("outside_date_window")
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
