import pydantic
import sqlmodel

try:
    from ._base import ChapterSQLModel
except (ImportError, ModuleNotFoundError):
    from ._base import ChapterSQLModel  # type: ignore


class Ref(ChapterSQLModel, table=True):
    """
    A reference (link or cross-reference) to a RefTarget (bookmark, heading or caption).
    RefTarget is a bridge table to a Target, which represents the document element
    referenced by this Ref.
    """

    __tablename__ = "refs"

    fn: str
    target_id: str
    text: str
    href: str
    prev_string: str
    prev_href: str
    elem: str
    asset_id: str | None = sqlmodel.Field(default=None)
    _was_updated: bool = pydantic.PrivateAttr(default=False)


class RefService:
    @staticmethod
    def is_external(href: str) -> bool:
        """Is it a link to an external target
        (currently only email and http protocol is recognized)."""
        if href.startswith("mailto:") and "@" in href:
            return True
        return href.startswith("http") and ".sharepoint.com/" not in href

    @staticmethod
    def is_internal_infile(href: str) -> bool:
        "Is it a link to a target in the same document (file)?"
        return href.startswith("#")

    @staticmethod
    def is_internal_f2f(href: str) -> bool:
        "Is it a link to another document (file)?"
        if RefService.is_internal_infile(href) or RefService.is_external(href):
            return False
        return "#" in href

    @staticmethod
    def remove_docx_syntax_from_href(href: str) -> str:
        prev = href
        href = _remove_switch(href)
        return href


#     @staticmethod
#     def get_s3_key(slug: str, stem: str) -> str:
#         return f"{slug}/{stem}.json"


def _remove_switch(href: str) -> str:
    """
    In ECMA-376 specification, a switch `\\l` is used to indicate a location,
    such as bookmark, where a hyperlink will jump. This has to be replaced
    with a hash symbol to be recognized as a link to a specific element (bookmark).
    """
    if "' \\l '" in href:
        href = href.replace("' \\l '", "#")
    if '" \\l "' in href:
        href = href.replace('" \\l "', "#")
    return href
