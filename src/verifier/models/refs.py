import sqlmodel

try:
    from ._base import MySQLModel
except (ImportError, ModuleNotFoundError):
    from ._base import MySQLModel  # type: ignore


class Ref(MySQLModel, table=True):
    """
    Reference (link or cross-reference) to a Target (bookmark, heading or caption)
    extracted from a docx document.
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


#     @staticmethod
#     def get_s3_key(slug: str, stem: str) -> str:
#         return f"{slug}/{stem}.json"
