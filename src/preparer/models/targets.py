import sqlmodel
import typing as t

try:
    from ._base import MySQLModel
except (ImportError, ModuleNotFoundError):
    from ._base import MySQLModel  # type: ignore


class Target(MySQLModel, table=True):
    """
    Target (bookmark, heading or caption), which is referenced by
    a Ref (link or cross-reference). Both are extracted from a docx document.
    """

    __tablename__ = "targets"

    pk: str = sqlmodel.Field(primary_key=True)
    html: str
    text: str
    elem: str
    is_paper: bool | None
    is_digital: bool | None
    # no "ref"
    filename: str | None
    fragment: str | None
    item_type: t.Literal["heading", "equation", "figure", "table", "graph", ""] = (
        sqlmodel.Field(sa_type=sqlmodel.String, default="")
    )
    file_count: int | None
    prefix: str
    prev_item_num: int | None
    new_item_num: int | None = sqlmodel.Field(default=None)
