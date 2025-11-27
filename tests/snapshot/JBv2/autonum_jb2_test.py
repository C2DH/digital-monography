import bs4
import pytest

from src._common.constants import DEFAULT_SFS_DIR, JB_DIR
from src._common.keys import KeyPath

JB_DIR = KeyPath(DEFAULT_SFS_DIR) / JB_DIR / "a_book"


class TestAutomaticNumberingInJupyterBookV2:
    key_a = JB_DIR / "01_a.md"
    key_b = JB_DIR / "02_b.md"
    key_cr = JB_DIR / "05_conditional_rendering.md"

    @classmethod
    def setup_class(cls):
        cls.md: dict[str, str] = {}
        for key in [cls.key_a, cls.key_b, cls.key_cr]:
            assert key.exists(), f"Expected {key} to exist but it does not."
            with open(key, "r") as f:
                cls.md[key] = f.read()

    def test_complex_numbering(self):
        """Test that `I.A` and `[auto]` was correctly replaced with `1.I.1`."""
        ref = "see equation 1.I.1"
        caption = (
            "**Equation 1.I.1:** Caption with chapter number and non-digit item number."
        )
        assert ref in self.md[self.key_a]
        assert caption in self.md[self.key_a]

    @pytest.mark.parametrize(
        "exp_text, is_digital, fn",
        [
            (
                "**Figure 1.1:** Image.",
                True,
                "key_a",
            ),
            (
                "**Table 1.1.** Look out ",
                True,
                "key_a",
            ),
            (
                "**Figure 2.1:** Red square.",
                True,
                "key_b",
            ),
            (
                "**Table 2.1:** Table.",
                True,
                "key_b",
            ),
            (
                "**Figure 5.1:** Drawing of an orange by Franz Eugen Köhler, 1887.",
                True,
                "key_cr",
            ),  # Figure 1
            ("Image of an orange. Author unknown.", False, "key_cr"),  # Figure 2
            ("**Figure 5.2:** An example of an image.", True, "key_cr"),  # Figure 3
            (
                "**Figure 5.3:** Target without references. Make sure the numbering is updated as well.",
                True,
                "key_cr",
            ),  # Figure 4
        ],
    )
    def test_autonum_in_target_captions(self, exp_text: str, is_digital: bool, fn: str):
        if is_digital:
            assert exp_text in self.md[getattr(self, fn)]
        else:
            assert exp_text not in self.md[getattr(self, fn)]

    @pytest.mark.parametrize(
        "ref, is_digital, fn",
        [
            ("[link to fig 5.1 (digital only)](#", True, "key_a"),
            ("[link to fig (paper only)](#", True, "key_a"),
            ("[link to fig 5.2 (digital and paper)](#", True, "key_a"),
            (
                # "Link to 1{sup}`st` asset (NOT on paper, 1{sup}`st` in digital): cross-ref **[Figure 5.1](#cad1981cd241e21a)** and [link to figForDigital bookmark](#cad1981cd241e21a)",
                "Link to 1{sup}`st` asset (NOT on paper, 1{sup}`st` in digital): cross-ref **[Figure 5.1](#",
                True,
                "key_cr",
            ),
            (
                "Link to 2{sup}`nd` asset (1{sup}`st` on paper, NOT in digital)",
                False,
                "key_cr",
            ),
            (
                # "Link to 3{sup}`rd` asset (2{sup}`nd` on paper, 2{sup}`nd` in digital): cross-ref **[Figure 5.2](#50c332fa0edff8a8)** and [link to figForDigitalAndPaper bookmark](#50c332fa0edff8a8)",
                "Link to 3{sup}`rd` asset (2{sup}`nd` on paper, 2{sup}`nd` in digital): cross-ref **[Figure 5.2](#",
                True,
                "key_cr",
            ),
        ],
    )
    def test_autonum_in_references(self, ref: str, is_digital: bool, fn: str):
        if is_digital:
            assert ref in self.md[getattr(self, fn)]
        else:
            assert ref not in self.md[getattr(self, fn)]
