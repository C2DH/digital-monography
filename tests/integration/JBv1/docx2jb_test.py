import bs4

from src._common.constants import DEFAULT_SFS_DIR
from src._common.keys import KeyPath

JB_BUILD_DIR = KeyPath(DEFAULT_SFS_DIR) / "a_book" / "_build" / "html"


class TestWorkflowFromDocxToJupyterBookV1:
    key_i = JB_BUILD_DIR / "00_index.html"
    key_a = JB_BUILD_DIR / "01_a.html"
    key_b = JB_BUILD_DIR / "02_b.html"
    key_cr = JB_BUILD_DIR / "05_conditional_rendering.html"

    @classmethod
    def setup_class(cls):
        cls.soup: dict[str, bs4.BeautifulSoup] = {}
        for key in [cls.key_i, cls.key_a, cls.key_b, cls.key_cr]:
            assert key.exists(), f"Expected {key} to exist but it does not."
            with open(key, "r") as f:
                cls.soup[key.name] = bs4.BeautifulSoup(f.read(), "html.parser")

    def test_files_exist(self):
        assert self.key_i.exists()
        assert self.key_a.exists()
        assert self.key_b.exists()
        assert self.key_cr.exists()

    def test_heading1_to_h1(self):
        assert self.soup[self.key_i.name].find("h1").string == "Book Title"
        assert self.soup[self.key_a.name].find("h1").string == "Hyperlinks A"
        assert self.soup[self.key_b.name].find("h1").string == "Hyperlinks B"
        assert self.soup[self.key_cr.name].find("h1").string == "Assets and links"
