import pytest

from src._common.constants import DEFAULT_SFS_DIR, JB_DIR
from src._common.keys import KeyPath

JB_DIR = KeyPath(DEFAULT_SFS_DIR) / JB_DIR


class TestFootnotesInJBv2:
    key_multi = JB_DIR / "a_book" / "01_a.md"
    key_split = JB_DIR / "split-to-multiple-chapters" / "00_index.md"

    @classmethod
    def setup_class(cls):
        cls.md: dict[str, str] = {}
        for key in [cls.key_multi, cls.key_split]:
            assert key.exists(), f"Expected {key} to exist but it does not."
            with open(key, "r") as f:
                cls.md[key] = f.read()

    @pytest.mark.parametrize(
        "ref, target, key",
        [
            (
                "Footnote[^footnote-ref-fn-01-a-1] without links.",
                "\n[^footnote-ref-fn-01-a-1]:  Standard footnote without links. \n",
                "key_multi",
            ),
            (
                "Start footnote[^footnote-ref-fn-01-a-2].",
                "\n[^footnote-ref-fn-01-a-2]:  [Footnote link to an external website](https://web.archive.org/web/20250101004557/http:/example.com/) \n",
                "key_multi",
            ),
            (
                "Middle footnote[^footnote-ref-fn-01-a-3].",
                "\n[^footnote-ref-fn-01-a-3]:  There is a [footnote link](https://web.archive.org/web/20250101004557/http:/example.com/) in the middle. \n",
                "key_multi",
            ),
            (
                "dolore magna aliqua[^footnote-ref-fn-00-index-1].\n",
                "\n[^footnote-ref-fn-00-index-1]:  Footnote in index. \n",
                "key_split",
            ),
        ],
    )
    def test_footnotes_in_md(self, ref: str, target: str, key: str):
        assert ref in self.md[getattr(self, key)], "Footnote reference not found."
        assert target in self.md[getattr(self, key)], "Footnote target not found."
