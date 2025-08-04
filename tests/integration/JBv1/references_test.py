import bs4
import pytest

from src.wordprocessor.constants import DEFAULT_SFS_DIR
from src.wordprocessor.keys import KeyPath

JB_BUILD_DIR = KeyPath(DEFAULT_SFS_DIR) / "a_book" / "_build" / "html"


class TestReferencesInJupyterBookV1:
    key_a = JB_BUILD_DIR / "01_a.html"
    key_b = JB_BUILD_DIR / "02_b.html"

    @classmethod
    def setup_class(cls):
        cls.soup: dict[str, bs4.BeautifulSoup] = {}
        for key in [cls.key_a, cls.key_b]:
            assert key.exists(), f"Expected {key} to exist but it does not."
            with open(key, "r") as f:
                cls.soup[key.name] = bs4.BeautifulSoup(f.read(), "html.parser")

    @pytest.mark.parametrize(
        "expected_href, expected_text, tag",
        [
            (
                "https://web.archive.org/web/20250101004557/http:/example.com/",
                "link in caption to an external source",
                "Ref in caption",
            ),
            (
                "http://example.com/xxx/",
                "Link to external website without using https nor archived link",
                "Ref in paragraph",
            ),
            (
                "https://web.archive.org/web/20250101004557/http:/example.com/",
                "Footnote link to an external website",
                "Ref in footnote (whole)",
            ),
            (
                "https://web.archive.org/web/20250101004557/http:/example.com/",
                "footnote link",
                "Ref in footnote (beginning)",
            ),
            (
                "https://web.archive.org/web/20250101004557/http:/example.com/",
                "end of the footnote.",
                "Ref in footnote (end)",
            ),
        ],
    )
    def test_ref_external(self, expected_href: str, expected_text: str, tag: str):
        links: bs4.element.ResultSet[bs4.element.Tag] = self.soup[
            self.key_a.name
        ].find_all("a")
        try:
            link = next(a for a in links if a.text == expected_text)
        except StopIteration:
            pytest.fail(f"Link with text '{expected_text}' was not found for '{tag}'.")
        assert (
            link.attrs["href"] == expected_href
        ), f"Hyperlink to an external source in caption is incorrect for '{tag}'."
        assert "reference" in link.attrs["class"]
        assert "external" in link.attrs["class"]
        assert "internal" not in link.attrs["class"]

    def _find_next_heading(self, target: bs4.element.Tag) -> bs4.element.Tag | None:
        """
        For links, the target is inserted before the heading as a separate element.
        Example: `(heading-target)=\n`.
        """
        count = 0
        while count < 5:  # don't look further than 5 siblings
            if isinstance(target, bs4.element.Tag) and target.name.startswith("h"):
                return target
            target = target.next_sibling
            count += 1
        return None

    def _find_paragraph(self, target: bs4.element.Tag) -> bs4.element.Tag:
        """
        For cross-references, id is given either directly to a target paragraph or,
        in case of multiple references to the same target, to a span child-element
        of that paragraph.
        Example: `[link-text](#link-target)`
        """
        if target.name != "p":
            target = target.find_parent("p")
        return target

    @pytest.mark.parametrize(
        "exp_text, exp_fragment, target_text, tag",
        [
            ("direct heading", "#f-01-a-heading", "Heading", "Link to a heading"),
            ("bookmark heading", "#f-01-a-a-heading", "Heading", "Link to a bookmark"),
            ("Figure 1.1", "#f-01-a-ref", "Figure 1.1: Image.", "Cross-ref to figure"),
            ("Table 1.1", "#f-01-a-ref", "Table 1.1. Look", "Cross-ref to table"),
        ],
    )
    def test_ref_internal_infile(
        self, exp_text: str, exp_fragment: str, target_text: str, tag: str
    ):
        links: bs4.element.ResultSet[bs4.element.Tag] = self.soup[
            self.key_a.name
        ].find_all("a")
        try:
            ref = next(a for a in links if a.text == exp_text)
        except StopIteration:
            pytest.fail(f'Reference with text "{exp_text}" was not found for "{tag}".')
        assert ref.attrs.get("href").startswith(
            exp_fragment
        ), 'Reference target is incorrect for "{tag}".'
        assert "reference" in ref.attrs["class"]
        assert "internal" in ref.attrs["class"]
        assert "external" not in ref.attrs["class"]

        # Test that the target exists and has the expected text
        href = ref.attrs["href"][1:]  # remove leading "#"
        target = self.soup[self.key_a.name].find(id=href)
        if tag.startswith("Cross-ref"):
            target = self._find_paragraph(target)
        elif tag.startswith("Link"):
            target = self._find_next_heading(target)
        assert target.text.startswith(
            target_text
        ), f'Could not find a target under id "{href}" for "{tag}".'

    @pytest.mark.parametrize(
        "exp_text, target_file, target_fragment, target_text",
        [
            ("Heading", "02_b.html", "f-02-b-h2subheading", "Heading#"),
            ("Figure 2.1", "02_b.html", "f-02-b-figredsquare", "Figure 2.1: Red"),
            ("Table 2.1", "02_b.html", "f-02-b-tblsimpletable", "Table 2.1: Table."),
        ],
    )
    def test_ref_internal_f2f(
        self,
        exp_text: str,
        target_file: str,
        target_fragment: str,
        target_text: str,
    ):
        links: bs4.element.ResultSet[bs4.element.Tag] = self.soup[
            self.key_a.name
        ].find_all("a")
        target_href = f"{target_file}#{target_fragment}"
        try:
            ref = next(
                a
                for a in links
                if a.text == exp_text and a.attrs.get("href") == target_href
            )
        except StopIteration:
            pytest.fail(
                f'Reference with text "{exp_text}" to "{target_file}#{target_fragment}" was not found.'
            )
        assert (
            ref.parent.text
            == "In a separate file: Links to Heading, Figure 2.1, and to Table 2.1."
        ), "Found references are not in the expected paragraph."
        assert "reference" in ref.attrs["class"]
        assert "internal" in ref.attrs["class"]
        assert "external" not in ref.attrs["class"]
        assert self.key_b.name == target_file, 'Target should be located in "02_b.html"'

        # Test that the target exists and has the expected text
        target = self.soup[self.key_b.name].find(id=target_fragment)
        if not isinstance(target, bs4.element.Tag):
            pytest.fail(
                f'Target with id "{target_fragment}" was not found in "{self.key_b.name}".'
            )
        if exp_text == "Heading":
            target = self._find_next_heading(target)
        else:
            target = self._find_paragraph(target)
        assert target.text.startswith(
            target_text
        ), f'Expected target text to start with "{target_text}", but got "{target.text}"'


# """
# // here iterate over siblings
# <span id="f-02-b-h2subheading"></span>
# <span id="f-02-b-heading"></span>
# <h2>
#     Heading
#     <a class="headerlink" href="#heading" title="Link to this heading">#</a>
# </h2>
# ...
# // here go to a parent
# <p id="f-02-b-figredsquare">
#     <span id="f-02-b-ref177053481"></span>
#     <strong>Figure 2.1:</strong>
#     Red square. See the video below.
# </p>
# ...
# // here go to a parent
# <p id="f-02-b-ref177044319">
#     <span id="f-02-b-ref177044323"></span>
#     <span id="f-02-b-tblsimpletable"></span>
#     <span id="f-02-b-ref177053494"></span>
#     <strong>Table 2.1:</strong>
#     Table.
# </p>
# """


# """
# <p>In a separate file: Links to
# <a class="reference internal" href="02_b.html#f-02-b-h2subheading">
#     <span class="std std-ref">
#         Heading
#     </span>
# </a>,
# <a class="reference internal" href="02_b.html#f-02-b-figredsquare">
#     <span class="std std-ref">
#         Figure 2.1
#     </span>
# </a>, and to
# <a class="reference internal" href="02_b.html#f-02-b-tblsimpletable">
#     <span class="std std-ref">
#         Table 2.1
#     </span>
# </a>.</p>
# """
