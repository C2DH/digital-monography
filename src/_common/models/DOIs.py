import sqlmodel


try:
    from ._base import ChapterSQLModel
except (ImportError, ModuleNotFoundError):
    from ._base import ChapterSQLModel  # type: ignore


DESC = {
    "proxy": "The web-based service that resolves DOI identifiers.",
    "doi": "DOI identifier, e.g. '10.1234/example'.",
    "parent": "The parent element that contains the DOI. Usually the quotation.",
}


class DOI(ChapterSQLModel, table=True):
    """
    Digital Object Identifier.
    See https://www.doi.org/the-identifier/what-is-a-doi/
    """

    __tablename__ = "dois"

    proxy: str | None = sqlmodel.Field(default=None, description=DESC["proxy"])
    doi: str = sqlmodel.Field(description=DESC["doi"])
    parent: str = sqlmodel.Field(description=DESC["parent"])


class DOIService:
    @staticmethod
    def is_proxy(s: str) -> bool:
        if s.lower() == "doi:":
            return False
        return True
