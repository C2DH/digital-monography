import bs4
import pytest

from src.wordprocessor.constants import DEFAULT_SFS_DIR
from src.wordprocessor.keys import KeyPath

JB_BUILD_DIR = KeyPath(DEFAULT_SFS_DIR) / "a_book" / "_build" / "html"


class TestAutomaticNumberingInJupyterBookV1:
    key_a = JB_BUILD_DIR / "01_a.html"
    key_cr = JB_BUILD_DIR / "05_conditional_rendering.html"

    @classmethod
    def setup_class(cls):
        cls.soup: dict[str, bs4.BeautifulSoup] = {}
        for key in [cls.key_a, cls.key_cr]:
            assert key.exists(), f"Expected {key} to exist but it does not."
            with open(key, "r") as f:
                cls.soup[key.name] = bs4.BeautifulSoup(f.read(), "html.parser")

    def test_complex_numbering(self):
        """Test that `I.A` and `[auto]` was correctly replaced with `1.I.1`."""
        ref = self.soup[self.key_a.name].find(id="f-01-a-equationwithcomplexnumbering")
        assert (
            ref.text
            == "Equation 1.I.1: Caption with chapter number and non-digit item number."
        )
        target = self.soup[self.key_a.name].find(
            "a", href="#f-01-a-equationwithcomplexnumbering"
        )
        assert target.text == "see equation 1.I.1"

    @pytest.mark.parametrize(
        "target_fragment, exp_text",
        [
            (
                "f-05-conditional-rendering-figfordigital",
                "link to fig 5.1 (digital only)",
            ),
            ("f-05-conditional-rendering-figforpaper", "link to fig  (paper only)"),
            (
                "f-05-conditional-rendering-figfordigitalandpaper",
                "link to fig 5.2 (digital and paper)",
            ),
        ],
    )
    def test_num_in_ref_internal_f2f(self, target_fragment: str, exp_text: str):
        href = f"05_conditional_rendering.html#{target_fragment}"
        ref = self.soup[self.key_a.name].find("a", href=href)
        assert ref is not None, f'Reference to "{href}" not found.'
        assert ref.text == exp_text
        assert "reference" in ref.attrs["class"]
        assert "internal" in ref.attrs["class"]
        assert "external" not in ref.attrs["class"]

    @pytest.mark.parametrize(
        "crossref_text, paragraph_text, link_href, link_text",
        [
            (
                "Figure 5.1",
                "Link to 1st asset (NOT on paper, 1st in digital)",
                "#f-05-conditional-rendering-figfordigital",
                "link to figForDigital bookmark",
            ),
            (
                "Figure 5.2",
                "Link to 3rd asset (2nd on paper, 2nd in digital)",
                "#f-05-conditional-rendering-figfordigitalandpaper",
                "link to figForDigitalAndPaper bookmark",
            ),
        ],
    )
    def test_num_in_ref_internal_infile(
        self, crossref_text: str, paragraph_text: str, link_href: str, link_text: str
    ):
        link = self.soup[self.key_cr.name].find("a", href=link_href)
        assert link is not None, f'Link to "{link_href}" was not found.'
        assert link.text == link_text
        assert "reference" in link.attrs["class"]
        assert "internal" in link.attrs["class"]
        assert "external" not in link.attrs["class"]
        crossref = link.parent.find("strong")
        assert crossref is not None, f'Cross-reference "{crossref_text}" was not found.'
        assert (
            crossref.text == crossref_text
        ), f'Cross-ref numbering should be updated to "{crossref_text}" but got "{crossref.text}".'
        a = crossref.find("a")
        assert "reference" in a.attrs["class"]
        assert "internal" in a.attrs["class"]
        assert "external" not in a.attrs["class"]
        assert crossref.parent.text.startswith(paragraph_text)

    def test_num_in_unref(self):
        unref_text = (
            " Target without references. Make sure the numbering is updated as well."
        )
        paragraphs: bs4.ResultSet[bs4.element.Tag] = self.soup[
            self.key_cr.name
        ].find_all("p")
        p = next((p for p in paragraphs if unref_text in p.text), None)
        assert p is not None, f'Paragraph with text "{unref_text}" was not found.'
        assert p.attrs["id"].startswith("f-05-conditional-rendering-unref")
        strong = p.find("strong")
        assert strong is not None, (
            f'No bolded number found in paragraph "{p.string}". '
            "Couldn't test correctness of numbering."
        )
        assert strong.text == "Figure 5.3:", (
            f'Expected "Figure 5.3:" but got "{strong.text}". Note that '
            "paper-only parts of a manuscript must not be included in the digital version."
        )
