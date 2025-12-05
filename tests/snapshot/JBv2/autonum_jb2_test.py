import pytest

from src._common.constants import DEFAULT_SFS_DIR, JB_DIR
from src._common.keys import KeyPath

JB_DIR = KeyPath(DEFAULT_SFS_DIR) / JB_DIR


class TestAutomaticNumberingInJupyterBookV2_MultipleDocsExample:
    key_a = JB_DIR / "a_book" / "01_a.md"
    key_b = JB_DIR / "a_book" / "02_b.md"
    key_cr = JB_DIR / "a_book" / "05_conditional_rendering.md"

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
                "Link to 1<sup>st</sup> asset (NOT on paper, 1<sup>st</sup> in digital): cross-ref **[Figure 5.1](#",
                True,
                "key_cr",
            ),
            (
                "Link to 2<sup>nd</sup> asset (1<sup>st</sup> on paper, NOT in digital)",
                False,
                "key_cr",
            ),
            (
                "Link to 3<sup>rd</sup> asset (2<sup>nd</sup> on paper, 2<sup>nd</sup> in digital): cross-ref **[Figure 5.2](#",
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


class TestAutomaticNumberingInJupyterBookV2_SplitDocExample:
    key_idx = JB_DIR / "split-to-multiple-chapters" / "00_index.md"
    key_inf = JB_DIR / "split-to-multiple-chapters" / "01_infile.md"
    key_uni = (
        JB_DIR / "split-to-multiple-chapters" / "02_is_unicode_with_custom_file_name.md"
    )

    @classmethod
    def setup_class(cls):
        cls.md: dict[str, str] = {}
        for key in [cls.key_idx, cls.key_inf, cls.key_uni]:
            assert key.exists(), f"Expected {key} to exist but it does not."
            with open(key, "r") as f:
                cls.md[key] = f.read()

    def test_complex_numbering(self):
        """Test that `2.A` and `[auto]` was correctly replaced with `1.2.1`."""
        ref1 = "see equation 1.2.1"
        ref2 = "cross-ref to [Equation 1.2.1]"
        caption = "**Equation 1.2.1:** Caption "
        assert ref1 in self.md[self.key_inf]
        assert ref2 in self.md[self.key_inf]
        assert caption in self.md[self.key_inf]

    @pytest.mark.parametrize(
        "exp_text, key, msg",  # note in this context msg is just a hint
        [
            (
                "**Figure 1.1:** Image.",
                "key_inf",
                "Autonumbering does not consist of a valid '<prefix>.<num>'.",
            ),
            (
                "**Table 1.1:** Look out ",
                "key_inf",
                "Autonumbering does not consist of a valid '<prefix>.<num>'.",
            ),
            (
                "**Figure 2.1:** Fig.",
                "key_uni",
                "Autonumbering should start at 1 with every new file.",
            ),
            (
                "**Table 2.1:** A table.",
                "key_uni",
                "Autonumbering should start at 1 with every new file.",
            ),
        ],
    )
    def test_autonum_in_target_captions(self, exp_text: str, key: str, msg: str | None):
        if msg is not None:
            assert exp_text in self.md[getattr(self, key)], msg
        else:
            assert exp_text not in self.md[getattr(self, key)]

    @pytest.mark.parametrize(
        "exp_text, key, msg",  # note in this context msg is just a hint
        [
            (
                "[see equation 1.2.1](#",
                "key_inf",
                "'[auto]' was not replaced correctly with complex autonumbering.",
            ),
            (
                "Cross-reference to [Figure 1.1](#",
                "key_inf",
                "Autonumbering does not consist of a valid '<prefix>.<num>'.",
            ),
            (
                "and to [Table 1.1](#",
                "key_inf",
                "Autonumbering does not consist of a valid '<prefix>.<num>'.",
            ),
            # (
            #     "section [3.2](#",
            #     "key_inf",
            #     "Fix issue #19",
            # ),
            # (
            #     "to section [3.2](#",
            #     "key_inf",
            #     "Fix issue #19",
            # ),
            (
                ", to [Figure 2.2](#",
                "key_inf",
                "Autonumbering should start at 1 with every new file.",
            ),
            (
                "and to [Table 2.1](#",
                "key_inf",
                "Autonumbering should start at 1 with every new file.",
            ),
            # ...
            (
                "cross-ref to the [Table 2.1](#",
                "key_inf",
                (
                    "Correct ref should include a valid file-prefix "
                    "and autonumbering should start at 1 with every new file."
                ),
            ),
        ],
    )
    def test_autonum_in_references(self, exp_text: str, key: str, msg: str | None):
        if msg is not None:
            assert exp_text in self.md[getattr(self, key)], msg
        else:
            assert exp_text not in self.md[getattr(self, key)]
