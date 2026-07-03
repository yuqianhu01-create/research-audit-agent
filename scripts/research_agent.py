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
    "industry": [],
    "ai-apps": [
        "AI", "artificial intelligence", "wearable", "digital health",
        "biological age", "health assessment", "longevity clinic",
        "personalized nutrition", "sleep", "exercise", "cognitive screening"
    ],
}

ACADEMIC_CORE_TERMS = [
    "aging", "ageing", "age-related", "longevity", "healthspan",
    "senescence", "senolytic", "sasp", "rejuvenation", "geroscience",
    "mitochondrial aging", "telomere", "epigenetic clock", "dna methylation",
    "nad", "nmn", "nicotinamide riboside", "stem cell aging",
    "caloric restriction", "rapamycin", "metformin aging"
]

INDUSTRY_SECTOR_TERMS = [
    "healthy aging", "healthy ageing", "longevity", "functional food",
    "functional foods", "nutraceutical", "nutraceuticals", "dietary supplement",
    "supplement", "cosmetics", "cosmetic", "skincare", "skin aging",
    "beauty", "biotechnology", "biotech", "medical device", "wearable",
    "biological age", "nad", "nmn", "nicotinamide riboside", "senolytic",
    "senescence", "cellular reprogramming", "epigenetic reprogramming",
    "collagen", "microbiome", "menopause", "cognitive health",
    "metabolic health", "anti-aging", "anti ageing", "healthspan",
]

INDUSTRY_EVENT_TERMS = [
    "r&d", "research and development", "launch", "launches", "new product",
    "partnership", "collaboration", "collaborates", "funding", "financing",
    "investment", "raises", "acquisition", "merger", "m&a",
    "sec filing", "investor relations", "approval", "clearance", "guidance",
    "clinical trial", "phase", "pipeline", "manufacturing", "market trend",
    "market trends", "conference", "presentation", "commercial technology",
    "regulatory", "fda", "ema", "hsa", "nmpa",
]

SECTION_KEYWORDS["industry"] = INDUSTRY_SECTOR_TERMS + INDUSTRY_EVENT_TERMS

INDUSTRY_SOURCE_TYPES = {
    "company_site", "company_news", "investor_relations", "sec_filing",
    "regulator", "clinical_trial", "clinical_trial_database",
    "industry_media", "professional_media", "credible_media",
    "market_research", "conference", "official_product_page",
}

CLINICAL_QUERIES = {
    "industry": [
        "senolytic OR cellular senescence",
        "NAD OR nicotinamide riboside OR NMN",
        "skin aging OR photoaging",
        "biological age OR longevity",
        "healthy aging supplement OR nutraceutical",
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
        {
            "title": "Cambrian Bio official longevity therapeutics pipeline updates",
            "source": "Cambrian Bio",
            "url": "https://www.cambrianbio.com/pipeline",
            "source_type": "company_site",
            "why_candidate": "Official company source for diversified longevity therapeutics pipeline positioning.",
        },
        {
            "title": "NewLimit official epigenetic reprogramming company updates",
            "source": "NewLimit",
            "url": "https://www.newlimit.com/",
            "source_type": "company_site",
            "why_candidate": "Official company source for epigenetic reprogramming and age-related cell biology platform updates.",
        },
        {
            "title": "Juvenescence official longevity company and portfolio updates",
            "source": "Juvenescence",
            "url": "https://juvenescence.ltd/",
            "source_type": "company_site",
            "why_candidate": "Official company source for longevity portfolio and commercialization signals.",
        },
        {
            "title": "Nestle Health Science official nutrition and healthy aging updates",
            "source": "Nestle Health Science",
            "url": "https://www.nestlehealthscience.com/newsroom",
            "source_type": "company_news",
            "why_candidate": "Official source for nutrition, medical nutrition, supplement, and healthy aging product updates.",
        },
        {
            "title": "Amway official nutrition and wellness product updates",
            "source": "Amway",
            "url": "https://www.amwayglobal.com/newsroom/",
            "source_type": "company_news",
            "why_candidate": "Official source for nutrition, supplement, wellness, and commercial product announcements.",
        },
        {
            "title": "Haleon official consumer health and wellness updates",
            "source": "Haleon",
            "url": "https://www.haleon.com/news",
            "source_type": "company_news",
            "why_candidate": "Official consumer health source for vitamins, supplements, oral health, and wellness portfolio updates.",
        },
        {
            "title": "L'Oreal official science, beauty, and skin aging product updates",
            "source": "L'Oreal",
            "url": "https://www.loreal.com/en/news/",
            "source_type": "company_news",
            "why_candidate": "Official cosmetics source for skincare, beauty science, longevity, and anti-aging product innovation.",
        },
        {
            "title": "The Estee Lauder Companies official skincare and longevity beauty updates",
            "source": "The Estee Lauder Companies",
            "url": "https://www.elcompanies.com/en/news-and-media/newsroom",
            "source_type": "company_news",
            "why_candidate": "Official cosmetics source for premium skincare, anti-aging product launches, R&D, and partnerships.",
        },
        {
            "title": "Shiseido official skincare science and anti-aging product updates",
            "source": "Shiseido",
            "url": "https://corp.shiseido.com/en/news/",
            "source_type": "company_news",
            "why_candidate": "Official cosmetics source for skin aging, ingredient science, and beauty technology updates.",
        },
        {
            "title": "Fierce Biotech longevity and aging biotechnology industry updates",
            "source": "Fierce Biotech",
            "url": "https://www.fiercebiotech.com/",
            "source_type": "industry_media",
            "why_candidate": "Professional biotech media for funding, partnerships, pipeline, and clinical development signals.",
        },
        {
            "title": "Endpoints News biotech financing, partnership, and clinical pipeline updates",
            "source": "Endpoints News",
            "url": "https://endpts.com/",
            "source_type": "industry_media",
            "why_candidate": "Professional biotech media for investment, strategic deals, and pipeline development signals.",
        },
        {
            "title": "BioSpace aging biotechnology company and market updates",
            "source": "BioSpace",
            "url": "https://www.biospace.com/",
            "source_type": "industry_media",
            "why_candidate": "Professional life-science media for company, funding, clinical, and market updates.",
        },
        {
            "title": "STAT biotechnology and health industry updates relevant to longevity",
            "source": "STAT",
            "url": "https://www.statnews.com/",
            "source_type": "professional_media",
            "why_candidate": "Professional health and biotechnology journalism for industry, policy, and market signals.",
        },
        {
            "title": "Pharmaceutical Technology clinical pipeline and medical technology updates",
            "source": "Pharmaceutical Technology",
            "url": "https://www.pharmaceutical-technology.com/",
            "source_type": "industry_media",
            "why_candidate": "Professional source for pharmaceutical pipeline, regulatory, manufacturing, and medical technology updates.",
        },
        {
            "title": "CosmeticsDesign skincare, beauty science, and anti-aging industry updates",
            "source": "CosmeticsDesign",
            "url": "https://www.cosmeticsdesign.com/",
            "source_type": "industry_media",
            "why_candidate": "Professional cosmetics source for skincare launches, ingredient innovation, regulation, and market trends.",
        },
        {
            "title": "NutraIngredients supplements, nutraceuticals, and healthy aging market updates",
            "source": "NutraIngredients",
            "url": "https://www.nutraingredients.com/",
            "source_type": "industry_media",
            "why_candidate": "Professional nutrition source for supplements, nutraceuticals, functional ingredients, and healthy aging trends.",
        },
        {
            "title": "Nutrition Insight functional nutrition and healthy aging industry updates",
            "source": "Nutrition Insight",
            "url": "https://www.nutritioninsight.com/",
            "source_type": "industry_media",
            "why_candidate": "Professional nutrition source for product launches, ingredient innovation, and health-positioning trends.",
        },
        {
            "title": "FoodNavigator functional food and healthy aging market updates",
            "source": "FoodNavigator",
            "url": "https://www.foodnavigator.com/",
            "source_type": "industry_media",
            "why_candidate": "Professional food industry source for functional foods, ingredients, regulation, and consumer trends.",
        },
        {
            "title": "Longevity.Technology longevity company, funding, and commercial technology updates",
            "source": "Longevity.Technology",
            "url": "https://longevity.technology/news/",
            "source_type": "industry_media",
            "why_candidate": "Specialized longevity industry source for company, funding, product, and market updates.",
        },
        {
            "title": "McKinsey life sciences and consumer health market trend insights",
            "source": "McKinsey",
            "url": "https://www.mckinsey.com/industries/life-sciences/our-insights",
            "source_type": "market_research",
            "why_candidate": "Consulting source for life-science, consumer health, commercial strategy, and market trend analysis.",
        },
        {
            "title": "Deloitte life sciences and health care industry insights",
            "source": "Deloitte",
            "url": "https://www2.deloitte.com/us/en/insights/industry/life-sciences.html",
            "source_type": "market_research",
            "why_candidate": "Consulting source for life-science, health care, manufacturing, market, and investment trends.",
        },
    ],
    "ai-apps": [
        {
            "title": "Oura official cardiovascular age and health feature updates",
            "source": "Oura",
            "url": "https://ouraring.com/blog/cardiovascular-age/",
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


def contains_phrase(text, phrase):
    phrase = normalize_key(phrase)
    if not phrase:
        return False
    return re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", text) is not None


def candidate_relevant_to_section(record):
    section = record.get("section", "")
    text = normalize_key(f"{record.get('title')} {record.get('abstract')} {record.get('why_candidate')} {record.get('source')}")
    if section == "academic":
        return any(contains_phrase(text, term) for term in ACADEMIC_CORE_TERMS)
    if section == "ai-aging":
        has_ai = any(contains_phrase(text, term) for term in ["ai", "artificial intelligence", "machine learning", "deep learning", "model"])
        has_aging = any(contains_phrase(text, term) for term in ACADEMIC_CORE_TERMS)
        return has_ai and has_aging
    if section == "industry":
        source_type = record.get("source_type", "")
        has_sector_signal = any(contains_phrase(text, term) for term in INDUSTRY_SECTOR_TERMS)
        has_event_signal = any(contains_phrase(text, term) for term in INDUSTRY_EVENT_TERMS)
        trusted_industry_source = source_type in INDUSTRY_SOURCE_TYPES
        if source_type in {"clinical_trial", "clinical_trial_database"}:
            return has_sector_signal and any(
                contains_phrase(text, term)
                for term in [
                    "senolytic", "senescence", "nad", "nmn", "nicotinamide riboside",
                    "skin aging", "photoaging", "biological age", "longevity",
                    "healthy aging", "nutraceutical", "supplement", "menopause",
                    "cognitive health", "metabolic health",
                ]
            )
        return trusted_industry_source and (has_sector_signal or has_event_signal)
    return True


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
    score = sum(1 for keyword in SECTION_KEYWORDS.get(section, []) if contains_phrase(text, keyword))
    if record.get("source_type") in {
        "company_site", "company_news", "official_product_page", "regulator",
        "clinical_trial_database", "clinical_trial", "investor_relations",
        "sec_filing", "industry_media", "professional_media", "credible_media",
        "market_research", "conference",
    }:
        score += 5
        record["priority_reason"] = "Authoritative official source for industry or product monitoring."
    journal = record.get("source", "")
    if journal in TOP_JOURNALS:
        score += 8
        record["priority_reason"] = "Top journal or major subjournal."
    elif any(term.lower() in text for term in ["clinical", "human", "trial", "translation"]):
        score += 3
        record["priority_reason"] = "Clinical or translational signal."
    elif any(contains_phrase(text, term) for term in INF_SOURCE_TERMS):
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
            description = protocol.get("descriptionModule", {})
            nct = ident.get("nctId", "")
            title = ident.get("briefTitle") or ident.get("officialTitle") or nct
            record = {
                "section": section,
                "title": title,
                "abstract": normalize_text(description.get("briefSummary") or description.get("detailedDescription") or "")[:1200],
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


def safe_collect(label, func, *args):
    try:
        return func(*args)
    except Exception as exc:
        print(f"Research Agent warning: {label} failed: {exc}")
        return []


def collect_section(section, limit, days_back):
    records = []
    if section in {"academic", "ai-aging"}:
        records.extend(safe_collect(f"{section} PubMed search", pubmed_search, section, limit, days_back))
        time.sleep(0.4)
        records.extend(safe_collect(f"{section} Crossref search", crossref_search, section, limit, days_back))
    if section == "industry":
        records.extend(watchlist_candidates(section))
        records.extend(safe_collect("industry ClinicalTrials search", clinicaltrials_search, section, limit))
    if section == "ai-apps":
        records.extend(safe_collect("ai-apps ClinicalTrials search", clinicaltrials_search, section, limit))
        time.sleep(0.4)
        records.extend(watchlist_candidates(section))
    if section in {"ai-aging", "ai-apps"}:
        records.extend(safe_collect(f"{section} arXiv search", arxiv_search, section, limit, days_back))
    records = [
        record for record in records
        if candidate_relevant_to_section(record)
        and (record.get("relevance_score", 0) > 0 or record.get("source_type") in INDUSTRY_SOURCE_TYPES)
    ]
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
