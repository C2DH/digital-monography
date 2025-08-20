import typing as t

try:
    from _base import MySQLModel
except (ImportError, ModuleNotFoundError):
    from ._base import MySQLModel  # type: ignore


class File(MySQLModel, table=True):
    __tablename__ = "files"

    stem: str
    slug: str
    prefix: str

    def __init__(self, **data: t.Dict[str, t.Any]) -> None:
        data["pk"] = data["stem"]
        super().__init__(**data)


class FileService:
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
