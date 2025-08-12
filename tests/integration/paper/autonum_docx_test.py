import bs4
import mammoth

from src.wordprocessor.constants import (
    AUTONUMBER_PLACEHOLDER,
    DEFAULT_SFS_DIR,
    MAMMOTH_STYLE_MAP,
)
from src.wordprocessor.keys import KeyPath
from src.preparer.html2md import convert_to_md

DOCX_OUTPUT_DIR = KeyPath(DEFAULT_SFS_DIR) / "a_book" / "_paper"


class TestWordprocessorOutput:
    """
    This sets of tests is similar to, but not identical, to the tests in
    `tests/wordprocessor/wordprocessor_test.py`. Unlike the unit tests in the
    `tests/wordprocessor` directory, this class leaves the process and checks
    the output of this microservice.

    Here, we can only check for the output. When syncing with `wordprocessor_test.py`,
    you need to remove checking the state before transformations (we only check the
    "after_soup" and "after_md" state).
    """

    key_i = KeyPath(DOCX_OUTPUT_DIR / "00_index.docx")
    key_a = KeyPath(DOCX_OUTPUT_DIR / "01_a.docx")
    key_b = KeyPath(DOCX_OUTPUT_DIR / "02_b.docx")
    key_cr = KeyPath(DOCX_OUTPUT_DIR / "05_conditional_rendering.docx")

    @classmethod
    def setup_class(cls):
        cls.after_soup: dict[str, bs4.BeautifulSoup] = {}
        cls.after_md: dict[str, str] = {}
        for key in [cls.key_i, cls.key_a, cls.key_b, cls.key_cr]:
            assert key.exists(), f"Expected {key} to exist but it does not."
            with open(key, "rb") as f:
                html = mammoth.convert_to_html(f, style_map=MAMMOTH_STYLE_MAP)
                soup = bs4.BeautifulSoup(html.value, "html.parser")
                md = convert_to_md(soup)
                cls.after_soup[key.stem] = soup
                cls.after_md[key.stem] = md

    def test_removal_of_whole_highlighted_paragraph(self):
        after_headings = [
            tag.text for tag in self.after_soup[self.key_cr.stem].find_all("h3")
        ]
        assert "Asset for digital" not in after_headings

    def test_clearance_of_highlighted_run(self):
        before_txt = "This paragraph contains an example of a run (part of a paragraph) that is only visible in the digitalpaper"
        after_text = "This paragraph contains an example of a run (part of a paragraph) that is only visible in the paper version."
        assert before_txt not in self.after_md[self.key_cr.stem]
        assert after_text in self.after_md[self.key_cr.stem]

    def test_clearance_of_highlighted_hyperlink(self):
        before_txt = "hyperlinks to e.g. [ebook](https://en.wikipedia.org/wiki/Ebook)[book](https://en.wikipedia.org/wiki/Book)."
        after_text = "hyperlinks to e.g. [book](https://en.wikipedia.org/wiki/Book)."
        assert before_txt not in self.after_md[self.key_cr.stem]
        assert after_text in self.after_md[self.key_cr.stem]

    def test_removal_of_highlight_from_run(self):
        after_soup_str = str(self.after_soup[self.key_cr.stem])
        before_txt = (
            "is only visible in the "
            '<span class="dgt-mon-digital-only">digital</span>'
            '<span class="dgt-mon-paper-only">paper</span>'
            " version."
        )
        after_text = "is only visible in the paper version."
        assert after_text in after_soup_str
        assert before_txt not in after_soup_str

    def test_removal_of_highlight_from_hyperlink(self):
        after_link = next(
            (
                a
                for a in self.after_soup[self.key_cr.stem].find_all("a", href=True)
                if a.text == "book"
            ),
            None,
        )
        assert after_link is not None
        assert after_link.name == "a"
        assert after_link.span is None

    def test_targets_in_captions_with_added_chapter_numbers(self):
        # Figure 1 removed during conditional rendering
        assert "**Figure 5.1:** Drawing" not in self.after_md[self.key_cr.stem]
        assert "**Figure 1:** Drawing" not in self.after_md[self.key_cr.stem]
        assert "**Figure 5.2:** Image" in self.after_md[self.key_cr.stem]
        assert "**Figure 2:** Image" not in self.after_md[self.key_cr.stem]
        assert "**Figure 5.3:** An example" in self.after_md[self.key_cr.stem]
        assert "**Figure 3:** An example" not in self.after_md[self.key_cr.stem]
        assert "**Figure 5.4:** Target" in self.after_md[self.key_cr.stem]
        assert "**Figure 4:** Target" not in self.after_md[self.key_cr.stem]

    def test_prepare_refs__placeholder_f2f(self):
        before = (
            "In a separate file: Links to "
            "[Heading](02_b.docx#h2Subheading), "
            f"[Figure {AUTONUMBER_PLACEHOLDER}](02_b.docx#figRedSquare), and to "
            f"[Table {AUTONUMBER_PLACEHOLDER}](02_b.docx#tblSimpleTable)."
        )
        after = (
            "In a separate file: Links to "
            "[Heading](02_b.docx#h2Subheading), "
            "[Figure 2.1](02_b.docx#figRedSquare), and to "
            "[Table 2.1](02_b.docx#tblSimpleTable)."
        )
        assert before not in self.after_md[self.key_a.stem]
        assert after in self.after_md[self.key_a.stem]

    def test_prepare_refs__placeholder_infile(self):
        before = f"Complex numbering: [see equation {AUTONUMBER_PLACEHOLDER}](#equationWithComplexNumbering)."
        after = (
            "Complex numbering: [see equation 1.I.1](#equationWithComplexNumbering)."
        )
        assert before not in self.after_md[self.key_a.stem]
        assert after in self.after_md[self.key_a.stem]

    def test_prepare_refs__placeholder_with_conditional_rendering(self):
        before = (
            "Conditional rendering: "
            f"[link to fig {AUTONUMBER_PLACEHOLDER} (digital only)](05_conditional_rendering.docx#figForDigital), "
            f"[link to fig {AUTONUMBER_PLACEHOLDER} (paper only)](05_conditional_rendering.docx#figForPaper), "
            f"[link to fig {AUTONUMBER_PLACEHOLDER} (digital and paper)](05_conditional_rendering.docx#figForDigitalAndPaper)."
        )
        after = (
            "Conditional rendering: "
            "[link to fig (digital only)](05_conditional_rendering.docx#figForDigital), "
            "[link to fig 5.1 (paper only)](05_conditional_rendering.docx#figForPaper), "
            "[link to fig 5.2 (digital and paper)](05_conditional_rendering.docx#figForDigitalAndPaper)."
        )
        assert before not in self.after_md[self.key_a.stem]
        assert after in self.after_md[self.key_a.stem]

    def test_remove_images(self):
        imgs = self.after_soup[self.key_cr.stem].find_all("img")
        assert len(imgs) == 0
