import bs4
import dataclasses

from src._common.state import DocumentState


@dataclasses.dataclass
class FrontmatterBlob:
    # TODO: Make Frontmatter model. Maybe first with only necessary fields?
    all_data: dict = dataclasses.field(default_factory=dict)
    myst_data: dict = dataclasses.field(default_factory=dict)


def extract_frontmatter(
    html_soup: bs4.BeautifulSoup, dstate: DocumentState, tables: list[bs4.Tag]
) -> FrontmatterBlob | None:
    """
    Iterate over every table in a document and check if it is a frontmatter table.
    Extract data from the first frontmatter table found.
    A document must not have more than one frontmatter table.
    It is ok if a document has no frontmatter table.
    """
    if not tables:
        return None
    for table in tables:
        rows: bs4.ResultSet[bs4.Tag] = table.find_all("tr")
        if _is_not_frontmatter_table(rows):
            continue
        all_data = {}
        for row in rows:
            cells: bs4.ResultSet[bs4.Tag] = row.find_all("td")
            key = cells[0].text
            val_cells = list(cells[1].children)
            # dictionary as a value
            if _is_value_a_dict(val_cells):
                all_data[_key(key)] = _parse_dict(val_cells[0].text)
            # simple value
            elif _is_value_a_paragraph(val_cells):
                all_data[_key(key)] = _val(val_cells[0].text)
            # list of values
            elif _is_value_a_list(val_cells):
                assert isinstance(val_cells[0], bs4.Tag)  # confirmed in check above
                lis = list(val_cells[0].find_all("li"))
                vals = []
                for li in lis:
                    # list of dictionaries
                    if _is_value_in_li_dict(li):
                        assert isinstance(li, bs4.Tag)  # confirmed in check above
                        vals.append(_parse_dict(li.text))
                    # list of simple values
                    elif isinstance(li, bs4.Tag):
                        vals.append(_val(li.text))
                all_data[_key(key)] = vals
        return FrontmatterBlob(
            all_data=all_data,
            myst_data={
                k: v for k, v in all_data.items() if k in mystmd_frontmatter_fields
            },
        )
    return None


def _is_not_frontmatter_table(rows: bs4.ResultSet[bs4.Tag]) -> bool:
    """
    To be a frontmatter table, the first row must include a "Frontmatter" string.
    """
    frontmatter_row = rows[0].findChild("td", string="Frontmatter")
    return frontmatter_row is None


def _is_value_a_dict(val_cells: list[bs4.PageElement]) -> bool:
    return (
        len(val_cells) == 1
        and isinstance(val_cells[0], bs4.Tag)
        and val_cells[0].name == "p"
        and val_cells[0].text.startswith("{")
        and val_cells[0].text.endswith("}")
    )


def _is_value_a_paragraph(val_cells: list[bs4.PageElement]) -> bool:
    return (
        len(val_cells) == 1
        and isinstance(val_cells[0], bs4.Tag)
        and val_cells[0].name == "p"
    )


def _is_value_a_list(val_cells: list[bs4.PageElement]) -> bool:
    return (
        len(val_cells) == 1
        and isinstance(val_cells[0], bs4.Tag)
        and val_cells[0].name == "ul"
    )


def _is_value_in_li_dict(li: bs4.PageElement) -> bool:
    return isinstance(li, bs4.Tag) and li.text.startswith("{") and li.text.endswith("}")


def _key(key: str) -> str:
    return key.strip().lower().replace(" ", "_")


def _val(val: str) -> str:
    return val.strip()


def _parse_dict(txt: str) -> dict[str, str]:
    """
    Parse incoming strings
       '{key1: Some value, key2: Some other value}'
    to
       {'key1': 'Some value', 'key2': 'Some other value'}
    """
    res = {}
    txt = txt.strip("{} ")
    items = txt.split(",")
    for item in items:
        key, val = item.split(":", 1)
        res[_key(key)] = _val(val)
    return res


# https://mystmd.org/guide/frontmatter#available-frontmatter-fields
mystmd_frontmatter_fields = [
    "title",
    "subtitle",
    "short_title",
    "description",
    "exports",
    "downloads",
    "label",
    "tags",
    "thumbnail",
    "banner",
    "parts",
    "bibliography",
    "date",
    "keywords",
    "authors",
    "reviewers",
    "editors",
    "affiliations",
    "doi",
    "arxiv",
    "pmid",
    "pmcid",
    "open_access",
    "license",
    "copyright",
    "funding",
    "github",
    "edit_url",
    "source_url",
    "binder",
    "subject",
    "venue",
    "volume",
    "issue",
    "first_page",
    "last_page",
    "math",
    "abbreviations",
    "numbering",
    "options",
    "id",
    "references",
    "requirements",
    "resources",
    "social",
    "jupyter",
    "thebe",
    "kernelspec",
    "skip_execution",
]
