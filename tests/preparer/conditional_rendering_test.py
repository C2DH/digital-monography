import bs4
import mammoth

from src._common.constants import MAMMOTH_STYLE_MAP, INPUT_DIR, TEMP_FOOTNOTES_TABLE
from src._common.keys import KeyPath
from src._common.html2md import convert_to_md
from src._common.state import DocumentState
from src._common.models import ChapterService
from src.preparer.main import prepare_docx

# from src.preparer.conditional_prep import is_paper_only, remove_paper_only
# from src.preparer.ref_footnotes import (
#     extract_footnotes,
#     is_ref_footnote,
#     is_target_footnote,
#     prepare_refs_in_footnotes,
# )
# from src.preparer.refs import (
#     is_reference,
#     prepare_references,
# )
# from src.preparer.targets import (
#     is_header,
#     is_caption,
#     prepare_ref_targets_in_headers,
#     prepare_ref_targets_in_captions,
# )


class TestConditionalRendering:
    fp = (
        KeyPath("/tmp") / "efs" / INPUT_DIR / "a_book" / "05_conditional_rendering.docx"
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
        cls.dstate.add(ChapterService.generate_chapter_from_key(key))
        cls.after_soup, cls.dstate, _ = prepare_docx(cls.after_soup, cls.dstate)
        cls.after_md = convert_to_md(cls.after_soup, cls.dstate)

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
