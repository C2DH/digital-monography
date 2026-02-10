import sqlmodel
import typing as t

try:
    from ._base import ChapterSQLModel
    from keys import KeyPath
except (ImportError, ModuleNotFoundError):
    from ._base import ChapterSQLModel  # type: ignore
    from ..keys import KeyPath  # type: ignore


DESC = {
    "hash": "xxhash.xxh64 hash of the target element.",
    "fm_key": "Input file where the target was defined.",
    "file_count": "A number by which chapters are ordered.",
}


class Target(ChapterSQLModel, table=True):
    """
    Target (bookmark, heading or caption), which is referenced by
    a Ref (link or cross-reference). Both are extracted from a docx document.
    """

    __tablename__ = "targets"

    # pk: str = sqlmodel.Field(primary_key=True)
    html: str  # I see no use, delete
    text: str
    elem: str  # I see no use, delete
    hash: str = sqlmodel.Field(description=DESC["hash"])
    is_paper: bool | None
    is_digital: bool | None
    x_fm_key: str = sqlmodel.Field(alias="fm_key", description=DESC["fm_key"])
    item_type: t.Literal["heading", "equation", "figure", "table", "graph", ""] = (
        sqlmodel.Field(sa_type=sqlmodel.String, default="")
    )
    file_count: int | None
    prefix: str
    prev_item_num: int | None
    new_item_num: int | None = sqlmodel.Field(default=None)

    @property
    def fm_key(self) -> KeyPath:
        return KeyPath(self.x_fm_key)

    @fm_key.setter
    def fm_key(self, val: KeyPath) -> None:
        self.x_fm_key = str(val)


class TargetService:

    @staticmethod
    def to_digital_version(t: Target) -> str:
        """
        Returns the value that will replace placeholder.
        Used for substituting values in builder (for digital version).
        """
        if t.new_item_num is not None:
            file_count = f"{t.file_count}." if t.file_count is not None else ""
            prefix = t.prefix if t.prefix is not None else ""
            return f"{file_count}{prefix}{t.new_item_num}"
        else:
            return ""

    @staticmethod
    def to_paper_version(t: Target) -> str:
        """
        Returns the value that will replace placeholder.
        Used for substituting values in wordprocessor (for paper version).
        """
        if t.new_item_num is not None:
            file_count = t.file_count if t.file_count is not None else ""
            prefix = t.prefix if t.prefix is not None else ""
            return f"{file_count}.{prefix}{t.new_item_num}"
        else:
            return ""
