import pathlib
import sqlmodel
import typing as t
import uuid

try:
    from ._base import ChapterSQLModel
    from keys import KeyPath
    from constants import AUTONUMBER_PLACEHOLDER
except (ImportError, ModuleNotFoundError):
    from ._base import ChapterSQLModel  # type: ignore
    from ..keys import KeyPath  # type: ignore
    from ..constants import AUTONUMBER_PLACEHOLDER


class Substitution(ChapterSQLModel, table=True):
    """
    This is used only in builder and defunct tests.
    TODO: Remove this after migrating to Jupyter Book v2.
    """

    __tablename__ = "substitutions"

    # pk: str = sqlmodel.Field(primary_key=True, default=str(uuid.uuid4()))
    was: str
    placeholder: str
    is_digital: bool | None
    is_paper: bool | None
    item_type: t.Literal[
        "heading", "equation", "figure", "table", "graph", "ref", ""
    ] = sqlmodel.Field(sa_type=sqlmodel.String)
    x_location: str = sqlmodel.Field(alias="location")
    target_fn: str | None
    file_count: int | None
    prefix: str
    prev_item_num: int | None
    new_item_num: int | None = sqlmodel.Field(default=None)
    fprefix: str | None = sqlmodel.Field(default=None)
    hash: str = sqlmodel.Field(description="xxhash.xxh64 hash of the target element.")

    @property
    def location(self) -> pathlib.Path:
        return pathlib.Path(self.x_location)

    @location.setter
    def location(self, val: pathlib.Path) -> None:
        self.x_location = str(val)

    def __init__(self, **data: t.Dict[str, t.Any]) -> None:
        data["x_location"] = str(data.pop("location"))
        super().__init__(**data)


class SubstitutionService:
    """
    Only old builder (for Jupyter Book v1) uses this.
    After migrating to Jupyter Book v2, this can be removed.
    """

    @staticmethod
    def to_digital_version(
        subst: Substitution, file_prefix: None | str | int = None
    ) -> str:
        """
        Returns the value that will replace placeholder, e.g. `1.I`.
        Used for substituting values in builder (for digital version).
        """
        if subst.is_digital is False and subst.is_paper is True:
            return ""
        elif subst.new_item_num and file_prefix:
            return f"{file_prefix}.{subst.prefix}{subst.new_item_num}"
        elif subst.new_item_num is not None:
            file_count = subst.file_count if subst.file_count is not None else ""
            return f"{file_count}.{subst.prefix}{subst.new_item_num}"
        elif subst.was == AUTONUMBER_PLACEHOLDER:
            return ""
        else:
            return subst.was
