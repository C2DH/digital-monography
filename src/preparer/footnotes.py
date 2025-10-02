import bs4
import docutils.nodes

from src._common.keys import KeyPath
from src._common.state import DocumentState


def is_target_footnote(tag: bs4.element.Tag) -> bool:
    """
    To be used while iterating over bs soup descendants, e.g. in `main.py`.
    This assumes that the iterating process made sure that isinstance(tag, bs4.Tag).
    """
    return bool(tag.name == "li" and tag.attrs.get("id", "").startswith("footnote-"))


def is_ref_footnote(tag: bs4.element.Tag) -> bool:
    """
    To be used while iterating over bs soup descendants, e.g. in `main.py`.
    This assumes that the iterating process made sure that isinstance(tag, bs4.Tag).
    While checking for other refs, make sure to exclude footnotes.
    """
    return bool(
        tag.name == "a"
        and "footnote" in tag.get("href", "")
        and tag.attrs.get("id", "").startswith("footnote-ref-")
    )


def prepare_targets_in_footnotes(
    html_soup: bs4.BeautifulSoup,
    docstate: DocumentState,
    footnotes: list[bs4.element.Tag],
) -> bs4.BeautifulSoup:
    """
    mammoth.convert_to_html function transform MS Word target footnotes to html:
    ```html
    <ol>
        <li id="footnote-fn-01-a-1">
            <p>Footnote text. <a href="#footnote-ref-fn-01-a-1">↑</a></p>
        </li>
        <!-- ... -->
    </ol>
    ```
    This should be transformed by to
    ```md
    [^footnote-ref-fn-01-a-1]:  Footnote text.
    ```
    # TODO: Consider creating Footnote model to store footnotes in the db.
    """
    for li_tag in footnotes:
        assert is_target_footnote(li_tag)  # TODO: remove after development
        li_tag: bs4.element.Tag
        footnote = Footnote(docstate.key)
        footnote.from_target(li_tag["id"])
        li_tag["id"] = footnote.id
        for tag in li_tag.descendants:
            if isinstance(tag, bs4.element.Tag) and tag.attrs.get(
                "href", ""
            ).startswith("#footnote-ref-"):
                tag["href"] = footnote.href
                break
    return html_soup


def prepare_refs_in_footnotes(
    html_soup: bs4.BeautifulSoup,
    docstate: DocumentState,
    references: list[bs4.element.Tag],
) -> bs4.BeautifulSoup:
    """
    mammoth.convert_to_html function transform MS Word ref footnotes to html:
    ```html
    <p>...<sup>
        <a href="#footnote-$ID" id="footnote-ref-$ID">[footnote-$ID]</a>
    </sup></p>
    ```
    This should be transformed by to
    ```md
    ...[^footnote-$ID].
    ```
    """
    for a_tag in references:
        a_tag: bs4.element.Tag
        assert is_ref_footnote(a_tag)  # TODO: remove after development
        footnote = Footnote(docstate.key)  # does it also works when splitting?
        footnote.from_ref(a_tag["id"])
        a_tag["href"] = footnote.href
        a_tag["id"] = footnote.id
        a_tag.string = footnote.string
    return html_soup


class Footnote:
    """
    After translation, the html should follow MyST/pandoc syntax:
        ```html
        <p> Ref of a footnote
            <sup>
                <a href="#footnote-$ID" id="footnote-ref-$ID">[footnote-$ID]</a>
            </sup>
        .</p>
        <ol>
            <li id="footnote-$ID">
              <p> Target of a footnote. <a href="#footnote-ref-$ID">↑</a></p>
            </li>
        </ol>
        ```
    where $ID is the unique_id of an instance of a footnote.

    This should be transformed by `html2md` to
        ```md
        Ref of a footnote[^footnote-$ID].
        [^footnote-$ID]: Target of a footnote.
        ```

    For more info see [docs](https://myst-parser.readthedocs.io/en/latest/syntax/typography.html#syntax-footnotes)
    """

    def __init__(self, fp: KeyPath | None):
        self.filepath: KeyPath | None = fp
        self.href: str = ""
        self.id: str = ""
        self.string: str = ""

    def _get_unique_id(self, old_id: str) -> str:
        return docutils.nodes.make_id(f"fn-{self.filepath.stem}-{old_id}")

    def from_ref(self, a_id: str) -> None:
        if not a_id.startswith("footnote-ref-"):
            return
        unique_id = self._get_unique_id(a_id[len("footnote-ref-") :])
        self.href = f"#footnote-{unique_id}"
        self.string = f"[{unique_id}]"
        # only for going back from target to ref in html, irrelevant in md
        self.id = f"footnote-ref-{unique_id}"

    def from_target(self, li_id: str) -> None:
        if not li_id.startswith("footnote-"):
            return
        if li_id.startswith("footnote-ref-"):
            return
        unique_id = self._get_unique_id(li_id[len("footnote-") :])
        self.id = f"footnote-{unique_id}"
        # only for going back from target to ref in html, irrelevant in md
        self.href = f"#footnote-ref-{unique_id}"

    def __str__(self) -> str:
        return f"Footnote(href={self.href}, id={self.id})"
