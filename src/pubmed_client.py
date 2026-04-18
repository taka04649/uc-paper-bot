"""PubMed E-utilities API クライアント。"""
import time
import xml.etree.ElementTree as ET
from typing import Dict, List

import requests

from config import PUBMED_API_KEY, PUBMED_EMAIL

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# 優先的に表示したい Publication Type（順序は表示優先度）
PRIORITY_PTYPES = [
    "Randomized Controlled Trial",
    "Meta-Analysis",
    "Systematic Review",
    "Clinical Trial, Phase III",
    "Clinical Trial, Phase II",
    "Clinical Trial",
    "Multicenter Study",
    "Observational Study",
    "Review",
    "Case Reports",
]


def _common_params() -> Dict[str, str]:
    params: Dict[str, str] = {}
    if PUBMED_API_KEY:
        params["api_key"] = PUBMED_API_KEY
    if PUBMED_EMAIL:
        params["email"] = PUBMED_EMAIL
        params["tool"] = "uc-paper-bot"
    return params


def search_pubmed(query: str, max_results: int = 20) -> List[str]:
    """PubMed 検索で PMID リストを取得する。"""
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": str(max_results),
        "sort": "date",
        "retmode": "json",
        **_common_params(),
    }
    r = requests.get(f"{BASE_URL}/esearch.fcgi", params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("esearchresult", {}).get("idlist", [])


def fetch_paper_details(pmids: List[str]) -> List[Dict]:
    """PMID リストから論文詳細（タイトル・abstract・雑誌名・論文タイプ）を取得する。"""
    if not pmids:
        return []

    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        **_common_params(),
    }
    r = requests.get(f"{BASE_URL}/efetch.fcgi", params=params, timeout=60)
    r.raise_for_status()

    root = ET.fromstring(r.content)
    papers: List[Dict] = []

    for article in root.findall(".//PubmedArticle"):
        try:
            paper = _parse_article(article)
            if paper and paper.get("abstract"):
                papers.append(paper)
        except Exception as e:
            print(f"[warn] Parse error for one article: {e}")
            continue
        time.sleep(0.1)  # rate limit 配慮

    return papers


def _parse_article(article: ET.Element) -> Dict:
    """<PubmedArticle> 要素をパースして dict を返す。"""
    pmid = article.findtext(".//PMID", "") or ""
    title = article.findtext(".//ArticleTitle", "") or ""
    journal = article.findtext(".//Journal/Title", "") or ""
    journal_iso = article.findtext(".//Journal/ISOAbbreviation", "") or journal

    # Abstract（複数 <AbstractText> を結合）
    abstract_parts: List[str] = []
    for el in article.findall(".//Abstract/AbstractText"):
        label = el.get("Label", "")
        text = el.text or ""
        if label:
            abstract_parts.append(f"{label}: {text}")
        else:
            abstract_parts.append(text)
    abstract = "\n".join(p for p in abstract_parts if p).strip()

    # 著者（最大3名 + et al.）
    all_authors = article.findall(".//Author")
    authors: List[str] = []
    for au in all_authors[:3]:
        last = au.findtext("LastName", "") or ""
        init = au.findtext("Initials", "") or ""
        name = f"{last} {init}".strip()
        if name:
            authors.append(name)
    author_str = ", ".join(authors)
    if len(all_authors) > 3:
        author_str += ", et al."

    # 出版年
    year = article.findtext(".//PubDate/Year", "") or ""
    if not year:
        medline_date = article.findtext(".//PubDate/MedlineDate", "") or ""
        year = medline_date[:4]

    # DOI
    doi = ""
    for aid in article.findall(".//ArticleId"):
        if aid.get("IdType") == "doi":
            doi = (aid.text or "").strip()
            break

    # Publication Types
    ptypes = [
        (el.text or "").strip()
        for el in article.findall(".//PublicationTypeList/PublicationType")
        if el.text
    ]
    primary_ptype = _select_primary_ptype(ptypes)

    return {
        "pmid": pmid,
        "title": title,
        "abstract": abstract,
        "journal": journal,
        "journal_iso": journal_iso,
        "authors": author_str,
        "year": year,
        "doi": doi,
        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        "publication_types": ptypes,
        "primary_ptype": primary_ptype,
    }


def _select_primary_ptype(ptypes: List[str]) -> str:
    """複数の Publication Type から、表示用に最も重要なものを 1 つ選ぶ。"""
    for priority in PRIORITY_PTYPES:
        if priority in ptypes:
            return priority
    # どれも該当しなければ、Journal Article 以外で最初のもの
    for pt in ptypes:
        if pt and pt != "Journal Article":
            return pt
    return "Journal Article"
