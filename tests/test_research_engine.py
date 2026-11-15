import unittest
from unittest.mock import Mock, patch

import requests

from src.research_engine import ResearchEngine


EUROPE_ARTICLE = {
    "title": "Spotlight Effect in Social Perception",
    "abstractText": (
        "This abstract describes how people estimate the degree to which others "
        "notice their appearance and behaviour in everyday social situations. "
        "The research examines estimates made by participants and observed attention."
    ),
    "firstPublicationDate": "2020-01-01",
    "journalTitle": "Journal of Social Psychology",
    "doi": "10.1000/example-doi",
}


PUBMED_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>12345678</PMID>
      <Article>
        <ArticleTitle>Spotlight effect and social attention</ArticleTitle>
        <Journal>
          <Title>Journal of Experimental Social Science</Title>
          <JournalIssue><PubDate><Year>2022</Year></PubDate></JournalIssue>
        </Journal>
        <Abstract>
          <AbstractText Label="BACKGROUND">This abstract gives background on social attention and self-focused perception in everyday interactions.</AbstractText>
          <AbstractText Label="METHODS">The study describes a method and findings without claiming that every person behaves the same way.</AbstractText>
        </Abstract>
      </Article>
      <ArticleIdList>
        <ArticleId IdType="doi">10.1000/pubmed-example</ArticleId>
      </ArticleIdList>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
"""


def response(json_data=None, content=b""):
    mock = Mock()
    mock.raise_for_status.return_value = None
    mock.json.return_value = json_data or {}
    mock.content = content
    return mock


class ResearchEngineTests(unittest.TestCase):
    def test_prefers_europe_pmc_when_usable_sources_exist(self):
        engine = ResearchEngine()
        payload = {"resultList": {"result": [EUROPE_ARTICLE]}}
        with patch("src.research_engine.requests.get", return_value=response(payload)) as get:
            result = engine.search("The Spotlight Effect", limit=3)

        self.assertEqual(len(result["sources"]), 1)
        self.assertEqual(result["sources"][0]["provider"], "Europe PMC")
        self.assertIn("10.1000/example-doi", result["sources"][0]["url"])
        self.assertIn("Spotlight Effect", result["notes"])
        self.assertEqual(get.call_count, 1)

    def test_falls_back_to_pubmed_after_europe_pmc_http_503(self):
        engine = ResearchEngine()
        unavailable = requests.exceptions.HTTPError("503 Server Error")
        search_response = response({"esearchresult": {"idlist": ["12345678"]}})
        fetch_response = response(content=PUBMED_XML)

        with patch(
            "src.research_engine.requests.get",
            side_effect=[unavailable, search_response, fetch_response],
        ) as get:
            result = engine.search("The Spotlight Effect: Why Nobody Noticed", limit=3)

        self.assertEqual(len(result["sources"]), 1)
        source = result["sources"][0]
        self.assertEqual(source["provider"], "PubMed")
        self.assertEqual(source["year"], "2022")
        self.assertEqual(source["journal"], "Journal of Experimental Social Science")
        self.assertEqual(source["url"], "https://doi.org/10.1000/pubmed-example")
        self.assertIn("BACKGROUND", result["notes"])
        self.assertEqual(get.call_count, 3)

    def test_returns_empty_sources_instead_of_inventing_citations(self):
        engine = ResearchEngine()
        unavailable = requests.exceptions.HTTPError("503 Server Error")
        with patch(
            "src.research_engine.requests.get",
            side_effect=[unavailable, requests.exceptions.Timeout("timeout")],
        ):
            result = engine.search("a concept with no available references")

        self.assertEqual(result, {"notes": "", "sources": []})

    def test_empty_topic_does_not_make_network_request(self):
        engine = ResearchEngine()
        with patch("src.research_engine.requests.get") as get:
            result = engine.search("")

        self.assertEqual(result, {"notes": "", "sources": []})
        get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
