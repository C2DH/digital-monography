import bs4
import pathlib
import mammoth

from src.preparer.constants import MAMMOTH_STYLE_MAP
from src.preparer.conditional_rendering import is_paper_only, remove_paper_only
from src.preparer.keys import KeyPath
from src.preparer.html2md import convert_to_md
from src.preparer.metadata import DocumentMetadata
from src.preparer.refs import (
    is_header,
    is_caption,
    is_footnote,
    is_reference,
    prepare_ref_targets_in_headers,
    prepare_ref_targets_in_captions,
    prepare_ref_targets_in_footnotes,
    prepare_references,
)
from src.preparer.state import DocumentState


class TestConditionalRendering:
    fp = KeyPath(
        pathlib.Path("/tmp") / "efs" / "a_book" / "05_conditional_rendering.docx"
    )

    @classmethod
    def setup_class(cls):
        assert (
            cls.fp.exists()
        ), "Make sure to run `make test/prep` to prepare the tests before running `make test`."
        with open(cls.fp, "rb") as f:
            result = mammoth.convert_to_html(f, style_map=MAMMOTH_STYLE_MAP)
        cls.before_soup = bs4.BeautifulSoup(result.value, "html.parser")
        cls.before_md = convert_to_md(cls.before_soup)
        cls.after_soup = bs4.BeautifulSoup(result.value, "html.parser")
        key = cls.fp.relative_to(cls.fp.parent.parent)
        cls.dstate = DocumentState(key)
        cls.metadata = DocumentMetadata(key)
        headers = []
        captions = []
        footnotes = []
        references = []
        paper_only = []
        classifiers = [
            (is_header, headers),
            (is_caption, captions),
            (is_footnote, footnotes),
            (is_reference, references),
            (is_paper_only, paper_only),
        ]
        for node in cls.after_soup.descendants:
            for check_if_meets_criteria, container in classifiers:
                if isinstance(node, bs4.element.Tag) and check_if_meets_criteria(node):
                    container.append(node)
        cls.after_soup = prepare_ref_targets_in_headers(
            cls.after_soup, cls.metadata, cls.dstate, headers
        )
        cls.after_soup = prepare_ref_targets_in_captions(
            cls.after_soup, cls.metadata, cls.dstate, captions
        )
        cls.after_soup = prepare_ref_targets_in_footnotes(
            cls.after_soup, cls.metadata, cls.dstate, footnotes
        )
        cls.after_soup = prepare_references(
            cls.after_soup, cls.metadata, cls.dstate, references
        )
        # html_soup = prepare_metadata_tables(html_soup, metadata, tables)
        cls.after_soup = remove_paper_only(
            cls.after_soup, cls.metadata, cls.dstate, paper_only
        )
        # html_soup = remove_empty_tables(html_soup, metadata, tables)
        cls.after_md = convert_to_md(cls.after_soup, cls.metadata, cls.dstate)

    def test_removal_of_parts_of_paragraph(self):
        expected_before = (
            "This paragraph contains an example of a run (part of a paragraph) "
            "that is only visible in the digitalpaper\n\n version. "
            "Same for hyperlinks to e.g. [ebook](https://en.wikipedia.org/wiki/Ebook)"
            "[book](https://en.wikipedia.org/wiki/Book)."
        )
        expected_after = (
            "This paragraph contains an example of a run (part of a paragraph) "
            "that is only visible in the digital version. "
            "Same for hyperlinks to e.g. [ebook](https://en.wikipedia.org/wiki/Ebook)."
        )
        assert expected_before in self.before_md
        assert expected_after not in self.before_md
        assert expected_after in self.after_md
        assert expected_before not in self.after_md

    def test_heading_removed(self):
        before_headings = [tag.text for tag in self.before_soup.find_all("h3")]
        after_headings = [tag.text for tag in self.after_soup.find_all("h3")]
        assert "Asset for digital" in before_headings
        assert "Asset for digital" in after_headings
        assert "Asset for paper" in before_headings
        assert "Asset for paper" not in after_headings

    def test_removal_of_whole_highlighted_paragraph(self):
        in_digital = "a text relevant only to a publication available online should not necessarily appear in a paper version"
        in_paper = "an author may wish that some content was published on paper only"
        assert in_digital in self.before_md
        assert in_digital in self.after_md
        assert in_paper in self.before_md
        assert in_paper not in self.after_md

    def test_removal_of_caption(self):
        in_digital = "Drawing of an orange by Franz Eugen Köhler, 1887."
        in_paper = "Image of an orange. Author unknown."
        assert in_digital in self.before_md
        assert in_digital in self.after_md
        assert in_paper in self.before_md
        assert in_paper not in self.after_md

    def test_removal_of_hyperlink(self):
        should_exist = self.before_soup.find("a", href="#figForPaper")
        should_not_exist = self.after_soup.find(
            "a",
            href="#f-05-conditional-rendering-figforpaper",
        )
        assert should_exist is not None
        assert should_exist.text == "link to figForPaper bookmark"
        assert should_not_exist is None
