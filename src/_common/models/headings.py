import sqlmodel
import typing as t

try:
    from ._base import MySQLModel
except (ImportError, ModuleNotFoundError):
    from ._base import MySQLModel  # type: ignore


class Heading(MySQLModel, table=True):
    __tablename__ = "headings"

    file_name: str
    file_num: int = sqlmodel.Field(default=-1)
    h_num: int
    elem: str
    level: str
    text: str
    word_count: int
    char_count: int
    target: str
    slug: str

    def __init__(self, **data: dict[str, t.Any]) -> None:
        data["file_num"] = HeadingService.get_number_from_filename(data["file_name"])
        super().__init__(**data)


class HeadingService:
    @staticmethod
    def get_number_from_filename(s: str) -> int:
        """Extract `int(1)` from file name '01_book_chapter'."""
        assert type(s) == str, "Only accepts string"
        number = ""
        default = -1
        for ch in s:
            if number and not ch.isdigit():
                return int(number)
            elif ch.isdigit():
                number += ch
        try:
            return int(number)
        except ValueError:
            return default
