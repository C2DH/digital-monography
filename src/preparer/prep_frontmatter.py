import bs4
import yaml
import typing as t

from src._common.state import DocumentState
from src._common.constants import CLS_FRONTMATTER_TABLE
from src._common.models import Chapter, ChapterService


class FrontmatterBlob:
    # TODO: Make Frontmatter model. Maybe first with only necessary fields?

    def __init__(self, data: dict[str, t.Any]):
        self.all_data: dict[str, t.Any] = data
        self.myst_data: dict[str, t.Any] = {}
        self.dgtmon_data: dict[str, t.Any] = {}
        for k, v in data.items():
            if k in MYSTMD_FRONTMATTER_FIELDS:
                self.myst_data[k] = v  # if necessary, init Frontmatter model
                continue
            field = next((f for f in CUSTOM_FRONTMATTER_FIELDS if f["key"] == k), None)
            if field is None:
                self.dgtmon_data[k] = v
            else:
                self.dgtmon_data[k] = field["fun"](v)

    def dump_yamlstr(self) -> str:
        """
        Returns a YAML string that will be
        1. put on top of a markdown file and,
        2. ingested to Jupyter Book v2 as frontmatter (https://mystmd.org/guide/frontmatter).
        """
        body = yaml.dump(self.myst_data, sort_keys=False, allow_unicode=True, indent=2)
        return f"---\n{body}---\n\n\n\n"

    def should_be_splitted(self) -> bool:
        return self.dgtmon_data["_split"] if "_split" in self.dgtmon_data else False


def prepare_frontmatter(
    html_soup: bs4.BeautifulSoup,
) -> tuple[bs4.BeautifulSoup, FrontmatterBlob | None]:
    # html_soup: bs4.BeautifulSoup, tables: list[bs4.Tag]
    """
    Iterate over every table in a document and check if it is a frontmatter table.
    Extract data from the first frontmatter table found and replace the table
    element with yaml string representation, which will later used by Jupyter Book v2.

    A document must not have more than one frontmatter table.
    It is ok if a document has no frontmatter table.
    """
    table = _find_frontmatter_table(html_soup)
    if not table:
        return html_soup, None
    # if not tables:
    #     return html_soup, None
    # for table in tables:
    rows: bs4.ResultSet[bs4.Tag] = table.find_all("tr")
    # if _is_not_frontmatter_table(rows):
    #     continue
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
    frontmatter = FrontmatterBlob(all_data)
    # myst_data={k: v for k, v in all_data.items() if k in mystmd_frontmatter_fields},
    # _replace_table_with_yamlstr(html_soup, table, frontmatter)
    new_tag = html_soup.new_tag("span")
    new_tag["class"] = CLS_FRONTMATTER_TABLE
    new_tag.string = frontmatter.dump_yamlstr()
    table.replace_with(new_tag)
    return html_soup, frontmatter
    # return html_soup, None


def _find_frontmatter_table(html_soup: bs4.BeautifulSoup) -> bs4.Tag | None:
    """
    The first table that includes a cell with a "Frontmatter" string in it,
    is considered a frontmatter table with all frontmatter information.
    """
    td = html_soup.find("td", string="Frontmatter")
    if td is None:
        return None
    return td.find_parent("table")


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


# def _replace_table_with_yamlstr(
#     html_soup: bs4.BeautifulSoup, table: bs4.Tag, frontmatter: FrontmatterBlob
# ) -> None:
#     new_tag = html_soup.new_tag("span")
#     new_tag["class"] = CLS_FRONTMATTER_TABLE
#     new_tag.string = frontmatter.dump_yamlstr()
#     table.replace_with(new_tag)


def to_bool(val: str) -> bool:
    val = val.lower()
    if val in ["true", "yes", "1"]:
        return True
    elif val in ["false", "no", "0"]:
        return False
    else:
        raise ValueError(f"Cannot convert '{val}' to bool.")


T = t.TypeVar("T")
# Type annotation for a custom frontmatter field
CustomFrontmatterFieldType = t.TypedDict(
    "CustomFrontmatterFieldType",
    {
        "key": str,
        # "field": str, # again, what was the purpose of this?
        "type": T,
        "fun": t.Callable[[str], T],
        "desc": str,
    },
)
# For now this is just for documentation.
CUSTOM_FRONTMATTER_FIELDS = [
    {
        "key": "_split",
        "type": bool,
        "fun": to_bool,
        "desc": "Indicates whether the file contains multiple chapters that should be split into separate parts. Each part will be a separate page in the digital version.",
    },
    {
        "key": "_toc",
        "type": list[Chapter],
        "fun": ChapterService.parse_toc,
        "desc": "",
    },
]


# https://mystmd.org/guide/frontmatter#available-frontmatter-fields
MYSTMD_FRONTMATTER_FIELDS = [
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
