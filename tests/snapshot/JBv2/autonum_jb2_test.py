import bs4
import pytest

from src._common.constants import DEFAULT_SFS_DIR, JB_DIR
from src._common.keys import KeyPath

JB_DIR = KeyPath(DEFAULT_SFS_DIR) / JB_DIR / "a_book"


class TestAutomaticNumberingInJupyterBookV2:
    key_a = JB_DIR / "01_a.md"
    key_cr = JB_DIR / "05_conditional_rendering.md"

    @classmethod
    def setup_class(cls):
        cls.md: dict[str, str] = {}
        for key in [cls.key_a, cls.key_cr]:
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
        "exp_text",
        [
            ("[link to fig 5.1 (digital only)](#"),
            ("[link to fig (paper only)](#"),  # this passes
            ("[link to fig 5.2 (digital and paper)](#"),
        ],
    )
    def test_num_in_ref_internal_f2f(self, exp_text: str):
        assert exp_text in self.md[self.key_a]

    @pytest.mark.parametrize(
        "is_digital, ref",
        [
            (
                True,
                "Link to 1{sup}`st` asset (NOT on paper, 1{sup}`st` in digital): cross-ref **[Figure 5.1](#cad1981cd241e21a)** and [link to figForDigital bookmark](#cad1981cd241e21a)",
            ),
            (False, "Link to 2{sup}`nd` asset (1{sup}`st` on paper, NOT in digital)"),
            (
                True,
                "Link to 3{sup}`rd` asset (2{sup}`nd` on paper, 2{sup}`nd` in digital): cross-ref **[Figure 5.2](#50c332fa0edff8a8)** and [link to figForDigitalAndPaper bookmark](#50c332fa0edff8a8)",
            ),
        ],
    )
    def test_num_in_ref_internal_infile(self, is_digital: bool, ref: str):
        if is_digital:
            assert ref in self.md[self.key_cr]
        else:
            assert ref not in self.md[self.key_cr]
