import pytest

from src._common.constants import DEFAULT_SFS_DIR, JB_DIR
from src._common.keys import KeyPath

JB_BUILD_DIR = KeyPath(DEFAULT_SFS_DIR) / JB_DIR / "a_book"


# TODO: Once some dashboard consumes Refs and Targets,
# add tests to check if they are correctly generated.


class TestRefsAndTargetsInJupyterBookV2:
    key_a = JB_BUILD_DIR / "01_a.md"
    key_b = JB_BUILD_DIR / "02_b.md"
    key_cr = JB_BUILD_DIR / "05_conditional_rendering.md"

    @classmethod
    def setup_class(cls):
        cls.md: dict[KeyPath, str] = {}
        for key in [cls.key_a, cls.key_b, cls.key_cr]:
            assert key.exists(), f"Expected {key} to exist but it does not."
            with open(key, "r") as f:
                cls.md[key] = f.read()

    @pytest.mark.parametrize(
        "exp_text, key",
        [
            (
                "See a [link in caption to an external source](https://web.archive.org/web/20250101004557/http:/example.com/)",
                "key_a",
            ),
            (
                "[Link to external website without using https nor archived link](http://example.com/xxx/).",
                "key_a",
            ),
            (
                "[Footnote link to an external website](https://web.archive.org/web/20250101004557/http:/example.com/)",
                "key_a",
            ),
            (
                "There is a [footnote link](https://web.archive.org/web/20250101004557/http:/example.com/) in the middle.",
                "key_a",
            ),
            (
                "Link at the [end of the footnote.](https://web.archive.org/web/20250101004557/http:/example.com/)",
                "key_a",
            ),
        ],
    )
    def test_ref_external(self, exp_text: str, key: str):
        assert exp_text in self.md[getattr(self, key)]

    @pytest.mark.parametrize(
        "ref_val, ref_key, tgt_val, tgt_key",
        [
            # infile
            (
                "Link to [direct heading](#80e6a4726eb7b446) and to [bookmark heading](#80e6a4726eb7b446).",
                "key_a",
                "(80e6a4726eb7b446)=\n## Heading",
                "key_a",
            ),
            (
                "Cross-reference to **[Figure 1.1](#8edfc0e04a18c2c0)** and",
                "key_a",
                "(8edfc0e04a18c2c0)=\n**Figure ",
                "key_a",
            ),
            (
                "(a4f96fb446ed2877)=\n**Table 1.1.** Look out",
                "key_a",
                "to [Table 1.1](#a4f96fb446ed2877).",
                "key_a",
            ),
            (
                "cross-ref **[Figure 5.1](#cad1981cd241e21a)** and",
                "key_cr",
                "(cad1981cd241e21a)=\n**Figure 5.1:** Drawing",
                "key_cr",
            ),
            (
                "and [link to figForDigital bookmark](#cad1981cd241e21a) ",
                "key_cr",
                "(cad1981cd241e21a)=\n**Figure 5.1:** Drawing",
                "key_cr",
            ),
            (
                "cross-ref **[Figure 5.2](#50c332fa0edff8a8)** and",
                "key_cr",
                "(50c332fa0edff8a8)=\n**Figure 5.2:** An example",
                "key_cr",
            ),
            (
                "and [link to figForDigitalAndPaper bookmark](#50c332fa0edff8a8) ",
                "key_cr",
                "(50c332fa0edff8a8)=\n**Figure 5.2:** An example",
                "key_cr",
            ),
            # f2f
            (
                "In a separate file: Links to [Heading](#5cafe92e61b687b7)",
                "key_a",
                "(5cafe92e61b687b7)=\n## Heading",
                "key_b",
            ),
            (
                ", [Figure 2.1](#b8a8d8f455fe9d01), and",
                "key_a",
                "(b8a8d8f455fe9d01)=\n**Figure 2.1:** Red square.",
                "key_b",
            ),
            (
                "to [Table 2.1](#de476b0c0bfbc457).",
                "key_a",
                "(de476b0c0bfbc457)=\n**Table 2.1:** Table.",
                "key_b",
            ),
        ],
    )
    def test_ref_and_target_link(
        self,
        ref_val: str,
        ref_key: str,
        tgt_val: str,
        tgt_key: str,
    ):
        assert (
            ref_val in self.md[getattr(self, ref_key)]
        ), f'Reference "{ref_val}" was not found.'
        assert (
            tgt_val in self.md[getattr(self, tgt_key)]
        ), f'Target "{tgt_val}" was not found.'
