import bs4
import pathlib
import pytest


from src._common.state import DocumentState
from src.preparer.main import is_table, _convert_to_html
from src.preparer.frontmatter import extract_frontmatter, FrontmatterBlob


SLUG = "book-content-examples"


@pytest.fixture
def frontmatter_data():
    fp = pathlib.Path("tests") / "_fixtures" / SLUG / "frontmatter_extraction.docx"
    tables = []
    html_str = _convert_to_html(fp)
    html_soup = bs4.BeautifulSoup(html_str, "html.parser")
    classifiers = [
        (is_table, tables),
    ]
    dstate = DocumentState(fp)
    for node in html_soup.descendants:
        for check_if_meets_criteria, container in classifiers:
            if isinstance(node, bs4.element.Tag) and check_if_meets_criteria(node):
                container.append(node)
    return extract_frontmatter(html_soup, dstate, tables)


def test_frontmatter_extraction(frontmatter_data: FrontmatterBlob | None):
    assert isinstance(frontmatter_data, FrontmatterBlob)
    assert len(frontmatter_data.all_data.keys()) > 0
    assert len(frontmatter_data.myst_data.keys()) > 0
    assert frontmatter_data.all_data["title"] == "Just a book"


def test_simple_value_extraction(frontmatter_data: FrontmatterBlob | None):
    assert frontmatter_data.all_data["title"] == "Just a book"
    assert frontmatter_data.all_data["license"] == "CC-BY-NC-ND-4.0"
    assert (
        frontmatter_data.all_data["github"]
        == "https://github.com/monograph-prototypes/split-to-multiple-chapters"
    )


def test_list_extraction(frontmatter_data: FrontmatterBlob | None):
    assert isinstance(frontmatter_data.all_data["keywords"], list)
    assert frontmatter_data.all_data["keywords"][0] == "test"
    assert frontmatter_data.all_data["keywords"][1] == "e2e"


def test_dict_as_value_extraction(frontmatter_data: FrontmatterBlob | None):
    assert isinstance(frontmatter_data.all_data["isbn"], dict)
    assert len(frontmatter_data.all_data["isbn"].keys()) == 3
    assert "ebook" in frontmatter_data.all_data["isbn"]
    assert "hardcover" in frontmatter_data.all_data["isbn"]
    assert "paperback" in frontmatter_data.all_data["isbn"]
    assert frontmatter_data.all_data["isbn"]["ebook"] == "9876543210123"
    assert frontmatter_data.all_data["isbn"]["hardcover"] == "9876543210123"
    assert frontmatter_data.all_data["isbn"]["paperback"] == "9876543210123"


def test_list_of_dicts_extraction(frontmatter_data: FrontmatterBlob | None):
    assert len(frontmatter_data.all_data["authors"]) == 2
    assert frontmatter_data.all_data["authors"][0] == {
        "name": "Pawel Kaminski",
        "affiliations": "University of Luxembourg",
    }
    assert frontmatter_data.all_data["authors"][1] == {
        "name": "Elisabeth Guerard",
        "affiliations": "Luxembourg Centre for Contemporary and Digital History (C²DH)",
    }


def test_boolean_value_extraction(frontmatter_data: FrontmatterBlob | None):
    # TODO: should this be converted to True?
    assert frontmatter_data.all_data["open_access"] == "True"
