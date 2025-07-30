import base64
import bs4
import json
import typing as t
import citeproc

try:
    from metadata import DocumentMetadata, CitationGroupDatapoint, CitationItemDatapoint
    from models import CitationGroup, CitationItem
    from state import DocumentState
except (ImportError, ModuleNotFoundError):
    from .metadata import (
        DocumentMetadata,
        CitationGroupDatapoint,
        CitationItemDatapoint,
    )
    from .models import CitationGroup, CitationItem
    from .state import DocumentState


class CitationItemTD(t.TypedDict):
    id: t.Union[int, str]
    itemData: dict[str, t.Any]  # TODO: extend itemData with explicit TypedDict
    uris: list[str]


class CitationItemProps(t.TypedDict):
    formattedCitation: str
    noteIndex: int
    plainCitation: str


class Citation(t.TypedDict):
    citationID: str
    citationItems: list[CitationItemTD]
    properties: CitationItemProps
    schema: str


def is_citation(tag: bs4.element.Tag) -> bool:
    return bool(tag.name == "span" and "citation" in tag.attrs.get("class", []))


def prepare_citations(
    html_soup: bs4.BeautifulSoup,
    metadata: DocumentMetadata,
    dstate: DocumentState,
    citation_tags: list[bs4.element.Tag],
) -> tuple[bs4.BeautifulSoup, citeproc.CitationStylesBibliography]:
    citation_style = "harvard1"  # TODO make it configurable
    citations = _extract_citations(citation_tags)
    citeproc_input = []

    for citation_group in citations:
        props = citation_group.get("properties", {})
        metadata.add_citation_group(
            CitationGroupDatapoint(
                pk=citation_group.get("citationID"),
                # id=citation_group.get("citationID"),
                file_name=metadata.filepath.name if metadata.filepath else "",
                citation_schema=citation_group.get("schema"),
                formattedCitation=props.get("formattedCitation"),
                noteIndex=props.get("noteIndex"),
                plainCitation=props.get("plainCitation"),
            )
        )
        dstate.add(
            CitationGroup(
                pk=citation_group.get("citationID"),
                loc=dstate.metadata.key,
                slug=dstate.metadata.slug,
                file_name=metadata.filepath.name if metadata.filepath else "",
                citation_schema=citation_group.get("schema"),
                formattedCitation=props.get("formattedCitation"),
                noteIndex=props.get("noteIndex"),
                plainCitation=props.get("plainCitation"),
            )
        )
        # TODO: link CGroup with CItem with a foreign key
        for citation_item in citation_group["citationItems"]:
            metadata.add_citation_item(
                CitationItemDatapoint(
                    # pk=citation_item.get("id"),
                    id=citation_item.get("id"),
                    file_name=metadata.filepath.name if metadata.filepath else "",
                    citationId=citation_group.get("citationID"),
                    itemData=citation_item.get("itemData"),
                    uris=citation_item.get("uris"),
                )
            )
            dstate.add(
                CitationItem(
                    loc=dstate.key,
                    id=citation_item.get("id"),
                    file_name=metadata.filepath.name if metadata.filepath else "",
                    citationId=citation_group.get("citationID"),
                    itemData=citation_item.get("itemData"),
                    uris=citation_item.get("uris"),
                )
            )
            citeproc_input.append(citation_item["itemData"])
    bib_source = citeproc.source.json.CiteProcJSON(citeproc_input)
    bib_style = citeproc.CitationStylesStyle(citation_style, validate=False)
    bibliography = citeproc.CitationStylesBibliography(
        bib_style, bib_source, citeproc.formatter.html
    )
    citeproc_citations = _create_citations_to_register(citations)  # ?
    html_soup = _add_citations(html_soup, citation_tags, citations)
    # html_soup = _add_citations(html_soup, citation_tags, citeproc_citations, citations, bibliography)
    for citproc_citation in citeproc_citations:
        bibliography.register(citproc_citation)
    return html_soup, bibliography


def _extract_citations(citation_tags: list[bs4.element.Tag]) -> list[Citation]:
    citations = []
    for span in citation_tags:
        if span.attrs.get("data-src", "").startswith("data:application/json;base64,"):
            data_src = span.attrs["data-src"]
            citations.append(
                json.loads(
                    base64.b64decode(data_src[len("data:application/json;base64,") :]),
                    strict=False,
                )
            )
    return citations


def _add_citations(
    html_soup: bs4.BeautifulSoup,
    citation_tags: list[bs4.element.Tag],
    # citeproc_citations: list[citeproc.Citation],
    citations: list[Citation],
    # bib: citeproc.CitationStylesBibliography,
) -> bs4.BeautifulSoup:
    i = 0

    def _warn(citation_item):
        print(
            "WARNING: Reference with key '{}' not found in the bibliography.".format(
                citation_item.key
            )
        )

    for span in citation_tags:
        if span.attrs.get("data-src", "").startswith("data:application/json;base64,"):
            citation = citations[i]
            citation_str = citation["properties"]["plainCitation"]
            GENERATE_CITATION_USING_CITEPROC = (
                "citation = citeproc_citations[i]",
                "citation_str = bib.cite(citation, _warn)",
            )
            new_tag = html_soup.new_tag("cite")
            new_tag.string = citation_str
            span.replace_with(new_tag)
            i += 1
    return html_soup


def _create_citations_to_register(citations: list[Citation]) -> list[citeproc.Citation]:
    """
    Processing citations in a document needs to be done in two passes as for some
    CSL styles, a citation can depend on the order of citations in the
    bibliography and thus on citations following the current one.
    For this reason, we first need to register all citations with the
    CitationStylesBibliography.
    """
    citation_objects = []
    for citation_group in citations:
        citation_items = []
        for citation_item in citation_group["citationItems"]:
            cit_id = str(citation_item["itemData"]["id"])
            citation_items.append(citeproc.CitationItem(cit_id))
        citation_objects.append(citeproc.Citation(citation_items))
    return citation_objects


def add_bibliography(
    html_soup: bs4.BeautifulSoup,
    bib: citeproc.CitationStylesBibliography,
) -> bs4.BeautifulSoup:
    citations = bib.bibliography()
    if not citations:
        return html_soup
    div = html_soup.new_tag("div", {"class": "dgtmon-bibliography"})
    h2 = html_soup.new_tag("h2")
    h2.string = "Bibliography"  # maybe give ability to change that in config.yaml
    ol = html_soup.new_tag("ol")
    for citation in citations:
        citation: citeproc.string.MixedString
        li = html_soup.new_tag("li")
        small = html_soup.new_tag("small")
        cit = bs4.BeautifulSoup(str(citation), "html.parser")
        small.append(cit)
        li.append(small)
        ol.append(li)
    div.append(h2)
    div.append(ol)
    html_soup.append(div)
    return html_soup
