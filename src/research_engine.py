"""Research lookups for MARROW Psychology scripts.

Europe PMC is the preferred source. PubMed E-utilities is a free fallback
when Europe PMC is unavailable or returns no usable abstracts. Both sources
are metadata/abstract discovery services; retrieved text is treated as
untrusted evidence, not as instructions or proof of causation.
"""
import html
import logging
import re
import xml.etree.ElementTree as ET

import requests

logger = logging.getLogger(__name__)


class ResearchEngine:
    EUROPE_PMC_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    PUBMED_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    PUBMED_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    USER_AGENT = "TubeAutoma/2.1 educational-psychology-video-research"

    @staticmethod
    def _clean_text(value):
        value = html.unescape(re.sub(r"<[^>]+>", " ", str(value or "")))
        return re.sub(r"\s+", " ", value).strip()

    @staticmethod
    def _pubmed_query(topic):
        stop_words = {
            "the", "and", "for", "with", "from", "why", "how", "what", "when",
            "where", "who", "you", "your", "our", "their", "about", "into",
            "over", "under", "that", "this", "these", "those", "nobody",
            "people", "noticed", "panicking", "because", "does", "do", "are",
            "was", "were", "can", "will", "could", "would", "should",
        }
        tokens = []
        for token in re.findall(r"[a-zA-Z]{3,}", str(topic or "").lower()):
            if token not in stop_words and token not in tokens:
                tokens.append(token)
        if not tokens:
            return ""
        # Lead with the named concept rather than framing words such as "why".
        lead = tokens[:2]
        if len(lead) == 1:
            return f'{lead[0]}[Title/Abstract]'
        first, second = lead
        return (
            f'"{first} {second}"[Title/Abstract] OR '
            f'({first}[Title/Abstract] AND {second}[Title/Abstract])'
        )

    def _europe_pmc_search(self, topic, limit):
        response = requests.get(
            self.EUROPE_PMC_URL,
            params={
                "query": f'({topic}) AND (SRC:MED OR SRC:PMC)',
                "format": "json",
                "pageSize": max(1, min(int(limit), 5)),
                "resultType": "core",
                "sort": "RELEVANCE",
            },
            timeout=15,
            headers={"User-Agent": self.USER_AGENT},
        )
        response.raise_for_status()
        results = response.json().get("resultList", {}).get("result", [])

        sources = []
        notes = []
        for item in results:
            title = self._clean_text(item.get("title", ""))
            abstract = self._clean_text(item.get("abstractText", ""))
            if not title or len(abstract) < 120:
                continue

            year = (
                str(item.get("firstPublicationDate", ""))[:4]
                or str(item.get("pubYear", ""))
            )
            journal = self._clean_text(item.get("journalTitle", ""))
            doi = str(item.get("doi", "") or "").strip()
            pmid = str(item.get("pmid", "") or "").strip()
            pmcid = str(item.get("pmcid", "") or "").strip()

            if doi:
                url = "https://doi.org/" + doi
            elif pmcid:
                url = "https://europepmc.org/articles/" + pmcid
            elif pmid:
                url = "https://europepmc.org/article/MED/" + pmid
            else:
                continue

            sources.append({
                "provider": "Europe PMC",
                "title": title,
                "year": year,
                "journal": journal,
                "url": url,
                "abstract": abstract[:1100],
            })
            notes.append(
                f"Source: {title} ({journal}, {year}). Abstract: {abstract[:850]}"
            )
            if len(sources) >= limit:
                break

        return {"notes": "\n\n".join(notes), "sources": sources}

    def _pubmed_search(self, topic, limit):
        query = self._pubmed_query(topic)
        if not query:
            return {"notes": "", "sources": []}

        search_response = requests.get(
            self.PUBMED_SEARCH_URL,
            params={
                "db": "pubmed",
                "term": query,
                "retmode": "json",
                "retmax": max(1, min(int(limit), 5)),
                "sort": "relevance",
                "tool": "TubeAutoma",
            },
            timeout=15,
            headers={"User-Agent": self.USER_AGENT},
        )
        search_response.raise_for_status()
        id_list = (
            search_response.json()
            .get("esearchresult", {})
            .get("idlist", [])
        )
        ids = [str(value) for value in id_list if str(value).isdigit()]
        if not ids:
            return {"notes": "", "sources": []}

        fetch_response = requests.get(
            self.PUBMED_FETCH_URL,
            params={
                "db": "pubmed",
                "id": ",".join(ids),
                "retmode": "xml",
                "tool": "TubeAutoma",
            },
            timeout=20,
            headers={"User-Agent": self.USER_AGENT},
        )
        fetch_response.raise_for_status()
        root = ET.fromstring(fetch_response.content)

        sources = []
        notes = []
        for article in root.findall(".//PubmedArticle"):
            citation = article.find("./MedlineCitation")
            if citation is None:
                continue
            article_node = citation.find("./Article")
            if article_node is None:
                continue

            title_node = article_node.find("./ArticleTitle")
            title = self._clean_text(
                "".join(title_node.itertext()) if title_node is not None else ""
            )
            abstract_parts = []
            for node in article_node.findall("./Abstract/AbstractText"):
                text = self._clean_text("".join(node.itertext()))
                if text:
                    label = str(node.attrib.get("Label", "")).strip()
                    abstract_parts.append(f"{label}: {text}" if label else text)
            abstract = " ".join(abstract_parts)
            if not title or len(abstract) < 120:
                continue

            journal_node = article_node.find("./Journal/Title")
            journal = self._clean_text(
                "".join(journal_node.itertext()) if journal_node is not None else ""
            )
            year = ""
            pub_date = article_node.find("./Journal/JournalIssue/PubDate")
            if pub_date is not None:
                year_node = pub_date.find("./Year")
                medline_date = pub_date.find("./MedlineDate")
                if year_node is not None and year_node.text:
                    year = year_node.text.strip()
                elif medline_date is not None and medline_date.text:
                    match = re.search(r"\b(19|20)\d{2}\b", medline_date.text)
                    year = match.group(0) if match else ""

            pmid_node = citation.find("./PMID")
            pmid = (pmid_node.text or "").strip() if pmid_node is not None else ""
            if not pmid:
                continue

            doi = ""
            for article_id in article.findall(".//ArticleId"):
                if article_id.attrib.get("IdType") == "doi":
                    doi = (article_id.text or "").strip()
                    break
            url = "https://doi.org/" + doi if doi else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

            sources.append({
                "provider": "PubMed",
                "title": title,
                "year": year,
                "journal": journal,
                "url": url,
                "abstract": abstract[:1100],
            })
            notes.append(
                f"Source: {title} ({journal}, {year}). Abstract: {abstract[:850]}"
            )
            if len(sources) >= limit:
                break

        return {"notes": "\n\n".join(notes), "sources": sources}

    def search(self, topic, limit=3):
        """Return source abstracts; fall back to PubMed on outage/empty results."""
        if not topic:
            return {"notes": "", "sources": []}

        safe_limit = max(1, min(int(limit), 5))
        try:
            result = self._europe_pmc_search(topic, safe_limit)
            if result.get("sources"):
                return result
            logger.warning(
                "Europe PMC returned no usable abstracts for '%s'; trying PubMed.",
                topic,
            )
        except Exception as exc:
            logger.warning(
                "Europe PMC lookup unavailable for '%s': %s; trying PubMed.",
                topic, exc,
            )

        try:
            result = self._pubmed_search(topic, safe_limit)
            if result.get("sources"):
                logger.info(
                    "Retrieved %s scholarly source(s) from PubMed fallback.",
                    len(result["sources"]),
                )
                return result
            logger.warning("PubMed returned no usable abstracts for '%s'.", topic)
        except Exception as exc:
            logger.warning("PubMed fallback unavailable for '%s': %s", topic, exc)

        # No references are invented. The caller's prompts are instructed to avoid
        # precise empirical claims when source retrieval fails.
        return {"notes": "", "sources": []}
