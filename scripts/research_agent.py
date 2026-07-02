import argparse
import json
import re
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


SEARCH_TERMS = {
    "academic": '(aging OR longevity OR healthspan OR senescence OR "mitochondrial aging" OR "epigenetic clock" OR senolytic OR NAD OR "stem cell aging")'
}


def fetch_text(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "anti-aging-briefing-demo-agent/0.1"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def pubmed_search(term, limit, days_back):
    min_date = date.today() - timedelta(days=days_back)
    query = f'({term}) AND ("{min_date.isoformat()}"[Date - Publication] : "3000"[Date - Publication])'
    params = urllib.parse.urlencode({
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": str(limit),
        "sort": "pub+date",
    })
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{params}"
    payload = json.loads(fetch_text(url))
    return payload.get("esearchresult", {}).get("idlist", [])


def pubmed_fetch(pmids):
    if not pmids:
        return []
    params = urllib.parse.urlencode({
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
    })
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?{params}"
    xml_text = fetch_text(url)
    root = ElementTree.fromstring(xml_text)
    records = []
    for article in root.findall(".//PubmedArticle"):
        medline = article.find("MedlineCitation")
        article_node = medline.find("Article") if medline is not None else None
        if article_node is None:
            continue
        pmid = medline.findtext("PMID", default="")
        title = "".join(article_node.findtext("ArticleTitle", default="").split())
        title = re.sub(r"\s+", " ", title).strip()
        journal = article_node.findtext("Journal/Title", default="PubMed")
        pub_date = extract_pub_date(article_node)
        doi = ""
        for article_id in article.findall(".//ArticleId"):
            if article_id.attrib.get("IdType") == "doi":
                doi = article_id.text or ""
                break
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""
        records.append({
            "section": "academic",
            "title": title,
            "published_date": pub_date,
            "source": journal,
            "url": url,
            "doi": doi,
            "pmid": pmid,
            "article_type": "academic_article",
            "status": "staging",
            "why_candidate": "PubMed recent search match for anti-aging academic frontier.",
        })
    return records


def extract_pub_date(article_node):
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
    if not year:
        return ""
    return f"{year}-{str(month).zfill(2)}-{str(day).zfill(2)}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--section", default="academic", choices=sorted(SEARCH_TERMS))
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--days-back", type=int, default=365)
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    term = SEARCH_TERMS[args.section]
    pmids = pubmed_search(term, args.limit, args.days_back)
    records = pubmed_fetch(pmids)
    output_path = DATA_DIR / "candidates.json"
    output_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Research Agent wrote {len(records)} candidates to {output_path}")


if __name__ == "__main__":
    main()
