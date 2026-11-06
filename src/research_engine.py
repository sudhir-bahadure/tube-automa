"""Free scholarly-source lookup using the Europe PMC public REST API."""
import html
import logging
import re
import requests

logger = logging.getLogger(__name__)


class ResearchEngine:
    API_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

    def search(self, topic, limit=3):
        """Return a few relevant abstracts and stable source links; never block production."""
        if not topic:
            return {"notes": "", "sources": []}
        try:
            response = requests.get(
                self.API_URL,
                params={
                    "query": f'({topic}) AND (SRC:MED OR SRC:PMC)',
                    "format": "json",
                    "pageSize": max(1, min(int(limit), 5)),
                    "resultType": "core",
                    "sort": "RELEVANCE",
                },
                timeout=15,
                headers={"User-Agent": "TubeAutoma/2.0 educational-video-research"},
            )
            response.raise_for_status()
            results = response.json().get("resultList", {}).get("result", [])
        except Exception as exc:
            logger.warning("Free research lookup unavailable: %s", exc)
            return {"notes": "", "sources": []}

        sources = []
        notes = []
        for item in results:
            title = html.unescape(re.sub(r"<[^>]+>", "", item.get("title", ""))).strip()
            abstract = item.get("abstractText", "")
            abstract = html.unescape(re.sub(r"<[^>]+>", " ", abstract))
            abstract = re.sub(r"\s+", " ", abstract).strip()
            if not title or len(abstract) < 120:
                continue

            year = item.get("firstPublicationDate", "")[:4] or str(item.get("pubYear", ""))
            journal = item.get("journalTitle", "")
            doi = item.get("doi", "")
            pmid = item.get("pmid", "")
            pmcid = item.get("pmcid", "")

            if doi:
                url = "https://doi.org/" + doi
            elif pmcid:
                url = "https://europepmc.org/articles/" + pmcid
            elif pmid:
                url = "https://europepmc.org/article/MED/" + pmid
            else:
                continue

            source = {
                "title": title,
                "year": year,
                "journal": journal,
                "url": url,
                "abstract": abstract[:1100],
            }
            sources.append(source)
            notes.append(
                f"Source: {title} ({journal}, {year}). Abstract: {abstract[:850]}"
            )
            if len(sources) >= limit:
                break

        return {"notes": "\n\n".join(notes), "sources": sources}
