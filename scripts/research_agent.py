import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
USER_AGENT = "anti-aging-briefing-research-agent/0.2"

ACADEMIC_TERMS = [
    "aging", "ageing", "longevity", "healthspan", "senescence", "senolytic",
    "mitochondrial aging", "epigenetic clock", "DNA methylation aging",
    "NAD", "stem cell aging", "telomere", "SASP", "geroscience",
    "caloric restriction", "rapamycin", "metformin aging"
]

AI_TERMS = [
    "artificial intelligence aging", "machine learning biological age",
    "deep learning senescence", "AI drug discovery longevity",
    "digital twin aging", "aging clock deep learning",
    "large language model aging"
]

INF_SOURCE_TERMS = [
    "botanical", "herbal", "polyphenol", "traditional Chinese medicine",
    "nutrition", "functional food", "NAD", "mitochondrial", "skin aging",
    "gut microbiome", "inflammation", "metabolism"
]

TOP_JOURNALS = {
    "Nature", "Science", "Cell", "Nature Aging", "Nature Medicine",
    "Nature Metabolism", "Cell Metabolism", "Science Translational Medicine",
    "Nature Communications", "Science Advances", "PNAS"
}

SECTION_KEYWORDS = {
    "academic": ACADEMIC_TERMS + INF_SOURCE_TERMS,
    "ai-aging": AI_TERMS + ACADEMIC_TERMS,
    "industry": [
        "clinical trial", "phase", "FDA", "IND", "NMPA", "partnership",
        "funding", "financing", "acquisition", "longevity", "senolytic",
        "NAD", "cellular reprogramming", "aging"
    ],
    "ai-apps": [
        "AI", "artificial intelligence", "wearable", "digital health",
        "biological age", "health assessment", "longevity clinic",
        "personalized nutrition", "sleep", "exercise", "cognitive screening"
    ],
}

CLINICAL_QUERIES = {
    "industry": [
        "longevity OR aging OR senolytic OR NAD OR idiopathic pulmonary fibrosis",
        "cellular reprogramming OR age-related disease OR frailty",
        "NMN OR nicotinamide riboside OR rapamycin OR metformin aging",
    ],
    "ai-apps": [
        "artificial intelligence aging OR wearable older adults",
        "digital health aging OR personalized nutrition older adults",
        "machine learning cognitive screening older adults",
    ],
}

OFFICIAL_WATCHLIST = {
    "industry": [
        {
            "title": "Life Biosciences official news and pipeline updates",
            "source": "Life Biosciences",
            "url": "https://www.lifebiosciences.com/news/",
            "source_type": "company_site",
            "why_candidate": "Official company source for cellular rejuvenation and age-related disease pipeline updates.",
        },
        {
            "title": "Insilico Medicine official pipeline and news updates",
            "source": "Insilico Medicine",
            "url": "https://insilico.com/news",
            "source_type": "company_site",
            "why_candidate": "Official company source for AI-discovered drug pipeline and clinical milestones.",
        },
        {
            "title": "ClinicalTrials.gov aging and longevity trial registry updates",
            "source": "ClinicalTrials.gov",
            "url": "https://clinicaltrials.gov/",
            "source_type": "clinical_trial_database",
            "why_candidate": "Official registry used to discover recent clinical-trial status changes.",
        },
        {
            "title": "FDA guidance and drug approval updates relevant to aging-related products",
            "source": "FDA",
            "url": "https://www.fda.gov/regulatory-information/search-fda-guidance-documents",
            "source_type": "regulator",
            "why_candidate": "Regulatory source for product development and approval milestones.",
        },
        {
            "title": "BioAge Labs official pipeline and company updates",
            "source": "BioAge Labs",
            "url": "https://bioagelabs.com/pipeline/",
            "source_type": "company_site",
            "why_candidate": "Official company source for aging-biology drug development and pipeline positioning.",
        },
        {
            "title": "Retro Biosciences official cellular reprogramming and longevity updates",
            "source": "Retro Biosciences",
            "url": "https://www.retrobio.com/",
            "source_type": "company_site",
            "why_candidate": "Official company source for cellular reprogramming and longevity platform updates.",
        },
        {
            "title": "Hevolution Foundation official longevity funding and program updates",
            "source": "Hevolution Foundation",
            "url": "https://hevolution.com/news/",
            "source_type": "company_site",
            "why_candidate": "Official foundation source for longevity funding programs and ecosystem signals.",
        },
    ],
    "ai-apps": [
        {
            "title": "Oura official cardiovascular age and health feature updates",
            "source": "Oura",
            "url": "https://support.ouraring.com/hc/en-us/articles/28451456013715-Cardiovascular-Age",
            "source_type": "official_product_page",
            "why_candidate": "Official product page for consumer wearable biological-age style features.",
        },
        {
            "title": "InsideTracker official AI health platform updates",
            "source": "InsideTracker",
            "url": "https://www.insidetracker.com/",
            "source_type": "official_product_page",
            "why_candidate": "Official source for AI-assisted biomarker and health recommendation product positioning.",
        },
        {
            "title": "Function Health official biomarker platform updates",
            "source": "Function Health",
            "url": "https://www.functionhealth.com/",
            "source_type": "official_product_page",
            "why_candidate": "Official source for consumer biomarker platform and AI-enabled health interpretation.",
        },
        {
            "title": "Apple Watch health feature updates",
            "source": "Apple",
            "url": "https://www.apple.com/watch/health/",
            "source_type": "official_product_page",
            "why_candidate": "Official product source for wearable health monitoring features.",
        },
        {
            "title": "Garmin official health science and wellness feature updates",
            "source": "Garmin",
            "url": "https://www.garmin.com/en-US/garmin-technology/health-science/",
            "source_type": "official_product_page",
            "why_candidate": "Official wearable source for health metrics, recovery, sleep, and fitness monitoring features.",
        },
        {
            "title": "ZOE official personalized nutrition platform updates",
            "source": "ZOE",
            "url": "https://zoe.com/",
            "source_type": "official_product_page",
            "why_candidate": "Official source for microbiome and personalized nutrition product positioning.",
        },
        {
            "title": "Viome official AI-powered health intelligence platform updates",
            "source": "Viome",
            "url": "https://www.viome.com/",
            "source_type": "official_product_page",
            "why_candidate": "Official source for AI-assisted microbiome and biomarker-based health recommendations.",
        },
        {
            "title": "Levels official metabolic health platform updates",
            "source": "Levels",
            "url": "https://www.levels.com/",
            "source_type": "official_product_page",
            "why_candidate": "Official source for glucose-monitoring and personalized metabolic health product design.",
        },
    ],
}


def fetch_text(url, timeout=30):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def normalize_text(value):
    if hasattr(value, "itertext"):
        value = " ".join(value.itertext())
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_key(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def parse_date_parts(parts):
    if not parts:
        return ""
    if isinstance(parts, list) and parts and isinstance(parts[0], list):
        parts = parts[0]
    year = str(parts[0]) if len(parts) >= 1 else ""
    month = str(parts[1]).zfill(2) if len(parts) >= 2 else "01"
    day = str(parts[2]).zfill(2) if len(parts) >= 3 else "01"
    return f"{year}-{month}-{day}" if year else ""


def score_record(record):
    text = normalize_key(f"{record.get('title')} {record.get('abstract')} {record.get('source')} {record.get('why_candidate')}")
    section = record.get("section", "academic")
    score = sum(1 for keyword in SECTION_KEYWORDS.get(section, []) if normalize_key(keyword) in text)
    if record.get("source_type") in {"company_site", "official_product_page", "regulator", "clinical_trial_database"}:
        score += 5
        record["priority_reason"] = "Authoritative official source for industry or product monitoring."
    journal = record.get("source", "")
    if journal in TOP_JOURNALS:
        score += 8
        record["priority_reason"] = "Top journal or major subjournal."
    elif any(term.lower() in text for term in ["clinical", "human", "trial", "translation"]):
        score += 3
        record["priority_reason"] = "Clinical or translational signal."
    elif any(normalize_key(term) in text for term in INF_SOURCE_TERMS):
        score += 2
        record["priority_reason"] = "Relevant to nutrition, botanical, metabolism, skin, gut, NAD, mitochondria, or inflammation."
    elif any(term in text for term in ["clock", "biomarker", "method", "model"]):
        score += 2
        record["priority_reason"] = "Methodology or biomarker innovation."
    record["relevance_score"] = score
    return score


def dedupe(records):
    seen = set()
    output = []
    for record in sorted(records, key=lambda item: item.get("relevance_score", 0), reverse=True):
        key = record.get("doi") or record.get("pmid") or record.get("nct_id") or record.get("arxiv_id") or record.get("url") or record.get("title")
        key = normalize_key(key)
        if key in seen:
            continue
        seen.add(key)
        output.append(record)
    return output


def pubmed_search(section, limit, days_back):
    terms = AI_TERMS if section == "ai-aging" else ACADEMIC_TERMS
    term_query = " OR ".join(f'"{term}"[Title/Abstract]' if " " in term else f'{term}[Title/Abstract]' for term in terms)
    min_date = date.today() - timedelta(days=days_back)
    query = f"({term_query}) AND (\"{min_date.isoformat()}\"[Date - Publication] : \"{date.today().isoformat()}\"[Date - Publication])"
    params = urllib.parse.urlencode({
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": str(max(limit * 2, 20)),
        "sort": "pub+date",
    })
    data = json.loads(fetch_text(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{params}"))
    ids = data.get("esearchresult", {}).get("idlist", [])
    return pubmed_fetch(ids, section)


def pubmed_fetch(pmids, section):
    if not pmids:
        return []
    params = urllib.parse.urlencode({"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"})
    root = ElementTree.fromstring(fetch_text(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?{params}"))
    records = []
    for article in root.findall(".//PubmedArticle"):
        medline = article.find("MedlineCitation")
        article_node = medline.find("Article") if medline is not None else None
        if article_node is None:
            continue
        pmid = medline.findtext("PMID", default="")
        title = normalize_text(article_node.find("ArticleTitle"))
        abstract = normalize_text(article_node.find("Abstract"))
        journal = article_node.findtext("Journal/Title", default="PubMed")
        doi = ""
        for article_id in article.findall(".//ArticleId"):
            if article_id.attrib.get("IdType") == "doi":
                doi = article_id.text or ""
                break
        record = {
            "section": section,
            "title": title,
            "abstract": abstract[:1200],
            "published_date": extract_pubmed_date(article_node),
            "source": journal,
            "source_type": "pubmed",
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
            "doi": doi,
            "pmid": pmid,
            "article_type": "academic_article",
            "status": "staging",
            "why_candidate": f"PubMed recent search match for {section}.",
        }
        score_record(record)
        records.append(record)
    return records


def extract_pubmed_date(article_node):
    pub_date = article_node.find("Journal/JournalIssue/PubDate")
    if pub_date is None:
        return ""
    year = pub_date.findtext("Year", default="")
    month = pub_date.findtext("Month", default="01")
    day = pub_date.findtext("Day", default="01")
    month_map = {
        "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06",
        "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
    }
    month = month_map.get(month[:3], month)
    return f"{year}-{str(month).zfill(2)}-{str(day).zfill(2)}" if year else ""


def crossref_search(section, limit, days_back):
    if section not in {"academic", "ai-aging"}:
        return []
    terms = " ".join(AI_TERMS[:3] if section == "ai-aging" else ACADEMIC_TERMS[:8])
    min_date = date.today() - timedelta(days=days_back)
    params = urllib.parse.urlencode({
        "query.title": terms,
        "filter": f"from-pub-date:{min_date.isoformat()},until-pub-date:{date.today().isoformat()},type:journal-article",
        "sort": "published",
        "order": "desc",
        "rows": str(max(limit, 10)),
        "mailto": "example@example.com",
    })
    data = json.loads(fetch_text(f"https://api.crossref.org/works?{params}"))
    records = []
    for item in data.get("message", {}).get("items", []):
        title = normalize_text((item.get("title") or [""])[0])
        if not title:
            continue
        doi = item.get("DOI", "")
        record = {
            "section": section,
            "title": title,
            "abstract": normalize_text(item.get("abstract", ""))[:1200],
            "published_date": parse_date_parts((item.get("published-print") or item.get("published-online") or item.get("published") or {}).get("date-parts")),
            "source": normalize_text((item.get("container-title") or ["Crossref"])[0]),
            "source_type": "doi",
            "url": f"https://doi.org/{doi}" if doi else item.get("URL", ""),
            "doi": doi,
            "article_type": "academic_article",
            "status": "staging",
            "why_candidate": f"Crossref recent journal search match for {section}.",
        }
        score_record(record)
        records.append(record)
    return records


def clinicaltrials_search(section, limit):
    records = []
    for query in CLINICAL_QUERIES.get(section, []):
        params = urllib.parse.urlencode({"query.term": query, "pageSize": str(limit), "format": "json"})
        data = json.loads(fetch_text(f"https://clinicaltrials.gov/api/v2/studies?{params}"))
        for study in data.get("studies", []):
            protocol = study.get("protocolSection", {})
            ident = protocol.get("identificationModule", {})
            status = protocol.get("statusModule", {})
            sponsor = protocol.get("sponsorCollaboratorsModule", {})
            design = protocol.get("designModule", {})
            nct = ident.get("nctId", "")
            title = ident.get("briefTitle") or ident.get("officialTitle") or nct
            record = {
                "section": section,
                "title": title,
                "published_date": status.get("studyFirstPostDateStruct", {}).get("date") or status.get("lastUpdatePostDateStruct", {}).get("date") or "",
                "source": "ClinicalTrials.gov",
                "source_type": "clinical_trial",
                "url": f"https://clinicaltrials.gov/study/{nct}" if nct else "",
                "nct_id": nct,
                "article_type": "clinical_trial_record",
                "status": "staging",
                "why_candidate": f"ClinicalTrials.gov match: {query}",
                "organization": normalize_text((sponsor.get("leadSponsor") or {}).get("name", "")),
                "phase": ", ".join(design.get("phases", []) or []),
            }
            score_record(record)
            records.append(record)
    return records


def arxiv_search(section, limit, days_back):
    if section not in {"ai-aging", "ai-apps"}:
        return []
    query = " OR ".join(f'all:"{term}"' for term in (AI_TERMS if section == "ai-aging" else ["wearable artificial intelligence health", "digital health aging", "biological age wearable"]))
    params = urllib.parse.urlencode({"search_query": query, "start": 0, "max_results": limit, "sortBy": "submittedDate", "sortOrder": "descending"})
    root = ElementTree.fromstring(fetch_text(f"https://export.arxiv.org/api/query?{params}"))
    ns = {"a": "http://www.w3.org/2005/Atom"}
    records = []
    min_date = date.today() - timedelta(days=days_back)
    for entry in root.findall("a:entry", ns):
        published = (entry.findtext("a:published", default="", namespaces=ns) or "")[:10]
        if published and published < min_date.isoformat():
            continue
        url = entry.findtext("a:id", default="", namespaces=ns)
        record = {
            "section": section,
            "title": normalize_text(entry.findtext("a:title", default="", namespaces=ns)),
            "abstract": normalize_text(entry.findtext("a:summary", default="", namespaces=ns))[:1200],
            "published_date": published,
            "source": "arXiv",
            "source_type": "preprint",
            "url": url,
            "arxiv_id": url.rsplit("/", 1)[-1] if url else "",
            "article_type": "preprint",
            "status": "staging",
            "why_candidate": f"arXiv search match for {section}.",
        }
        score_record(record)
        records.append(record)
    return records


def watchlist_candidates(section):
    records = []
    for item in OFFICIAL_WATCHLIST.get(section, []):
        record = {
            "section": section,
            "title": item["title"],
            "published_date": "",
            "source": item["source"],
            "source_type": item["source_type"],
            "url": item["url"],
            "article_type": "official_source_watch",
            "status": "staging",
            "why_candidate": item["why_candidate"],
            "requires_human_date_check": True,
        }
        score_record(record)
        records.append(record)
    return records


def collect_section(section, limit, days_back):
    records = []
    if section in {"academic", "ai-aging"}:
        records.extend(pubmed_search(section, limit, days_back))
        time.sleep(0.4)
        records.extend(crossref_search(section, limit, days_back))
    if section in {"industry", "ai-apps"}:
        records.extend(clinicaltrials_search(section, limit))
        time.sleep(0.4)
        records.extend(watchlist_candidates(section))
    if section in {"ai-aging", "ai-apps"}:
        records.extend(arxiv_search(section, limit, days_back))
    records = [record for record in records if record.get("relevance_score", 0) > 0 or record.get("source_type") in {"company_site", "official_product_page", "regulator"}]
    return dedupe(records)[:limit]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--section", default="all", choices=["all", "academic", "industry", "ai-aging", "ai-apps"])
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--days-back", type=int, default=365)
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    sections = ["academic", "industry", "ai-aging", "ai-apps"] if args.section == "all" else [args.section]
    records = []
    for section in sections:
        try:
            section_records = collect_section(section, args.limit, args.days_back)
            print(f"Research Agent collected {len(section_records)} candidates for {section}")
            records.extend(section_records)
        except Exception as exc:
            print(f"Research Agent warning: {section} failed: {exc}")
    output_path = DATA_DIR / "candidates.json"
    output_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Research Agent wrote {len(records)} candidates to {output_path}")


if __name__ == "__main__":
    main()
