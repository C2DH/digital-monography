from weakref import ref
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
        """Test that `[auto]` was correctly replaced with `1.I.1`."""
        ref = self.soup[self.key_a.name].find(id="f-01-a-equationwithcomplexnumbering")
        assert (
            ref.text
            == "Equation 1.I.1: Caption with chapter number and non-digit item number."
        )
        target = self.soup[self.key_a.name].find(
            "a", href="#f-01-a-equationwithcomplexnumbering"
        )
        assert target.text == "see equation 1.I.1"

    # @pytest.mark.parametrize(
    #     "",
    #     [
    #         (),
    #     ],
    # )
    # def test_num_in_ref_external_f2f(self):
    #     pass


# Conditional rendering: link to fig 5.1 (digital only), link to fig (paper only), link to fig 5.2 (digital and paper).
