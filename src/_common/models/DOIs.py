import sqlmodel
import pydantic
import typing as t


try:
    from ._base import ChapterSQLModel
except (ImportError, ModuleNotFoundError):
    from ._base import ChapterSQLModel  # type: ignore


DESC = {
    "slug": "Book's slug.",
    "proxy": "The web-based service that resolves DOI identifiers, e.g. 'https://doi.org/'.",
    "doi": "DOI identifier, e.g. '10.1234/example'.",
    "parent": "The parent element that contains the DOI. Usually the quotation.",
}


class DOI(ChapterSQLModel, table=True):
    """
    Digital Object Identifier.
    See https://www.doi.org/the-identifier/what-is-a-doi/
    """

    __tablename__ = "dois"
    model_config = pydantic.ConfigDict(validate_assignment=True)

    slug: str = sqlmodel.Field(description=DESC["slug"])
    proxy: str | None = sqlmodel.Field(default=None, description=DESC["proxy"])
    doi: str = sqlmodel.Field(description=DESC["doi"])
    parent: str = sqlmodel.Field(description=DESC["parent"])

    @pydantic.field_validator("doi", mode="before")
    @classmethod
    def normalize_doi(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("DOI must be a string")
        normalized = DOIService.normalize(value)
        if not normalized:
            raise ValueError("DOI cannot be empty")
        return normalized


class DOIService:
    TRAILING_PUNCTUATION = ".,;:!?)]}\"'”’»"

    @staticmethod
    def is_proxy(s: str) -> bool:
        if not s:
            return False
        if s.lower() == "doi:":
            return False
        return True

    @classmethod
    def normalize(cls, s: str) -> str:
        return s.strip().rstrip(cls.TRAILING_PUNCTUATION)
