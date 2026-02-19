import bs4
import re

from src._common.state import DocumentState
from src._common.models import DOI, DOIService


DOI_PATTERN = re.compile(
    r"("
    r"(?:https?://)?"  # http(s)://
    r"(?:dx\.)?"  # doi archive dx subdomain
    r"doi\.org/|DOI:\s*)?"
    r"(10\.\d{4,9}/[-._;()/:A-Z0-9]+)",  # https://www.crossref.org/blog/dois-and-matching-regular-expressions/
    re.IGNORECASE,
)


def search_for_entities_in_text(
    html_soup: bs4.BeautifulSoup,
    docstate: DocumentState,
) -> bs4.BeautifulSoup:
    for elem in html_soup.find_all(string=DOI_PATTERN):
        # print("-" * 25)
        # print("> elem", elem)
        # print("type(elem)", type(elem))
        assert isinstance(elem, bs4.NavigableString)
        # print("elem.text", elem.text)
        # print("elem.parent", elem.parent)
        # print("elem.parent.name", elem.parent.name)
        # print("elem.parent.attrs", elem.parent.attrs)
        _match = re.search(DOI_PATTERN, elem.text)
        # print("_match", _match)
        # print("_match.group(0)", _match.group(0))  # The entire matched string
        # print(
        #     "_match.group(1)", _match.group(1)
        # )  # The optional prefix (e.g., "https://doi.org/" or "DOI: ")
        # print(
        #     "_match.group(2)", _match.group(2)
        # )  # The actual DOI (e.g., "10.1234/example")
        proxy_candidate = _match.group(1) if _match.group(1) else ""
        doi = DOI(
            proxy=proxy_candidate if DOIService.is_proxy(proxy_candidate) else None,
            doi=_match.group(2),
            parent=elem.parent.text if elem.parent else None,
        )
        # print("doi", doi)
        docstate.add(doi)

        # TODO: Currently DOI.doi can end with "."

    return html_soup


# test_cases = [
#     "https://doi.org/10.1234/example",
#     "https://dx.doi.org/10.1234/example",
#     "dx.doi.org/10.1234/example",
#     "doi.org/10.1234/example",
#     "DOI: 10.1234/example",
#     "DOI:10.1234/example",
#     "10.1234/example",  # Bare DOI
#     "Check this DOI: 10.5555/12345678 for reference",
# ]

# def test_doi_regex(doi_pattern):
#     for text in test_cases:
#         match = doi_pattern.search(text)
#         if match:
#             print(f"✓ Found: {match}")
#         else:
#             print(f"✗ No match: {text}")
