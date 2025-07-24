import sqlmodel
import typing as t

try:
    from _base import MySQLModel
except (ImportError, ModuleNotFoundError):
    from ._base import MySQLModel  # type: ignore


class File(MySQLModel, table=True):
    __tablename__ = "files"

    # id: int = sqlmodel.Field(primary_key=True)
    pk: str = sqlmodel.Field(primary_key=True)
    stem: str
    prefix: str

    def __init__(self, **data: t.Dict[str, t.Any]) -> None:
        data["pk"] = data["stem"]
        super().__init__(**data)


# class FileDatapoint(DatapointBase):
#     schema_v: int = 1  # if multiple v in the db, the client might have to differentiate
#     ###
#     pk: str
#     stem: str
#     prefix: str

#     def __init__(self, **data) -> None:
#         data["pk"] = data["stem"]
#         super().__init__(**data)
