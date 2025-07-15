# class FileDatapoint(DatapointBase):
#     schema_v: int = 1  # if multiple v in the db, the client might have to differentiate
#     ###
#     pk: str
#     stem: str
#     prefix: str

#     def __init__(self, **data) -> None:
#         data["pk"] = data["stem"]
#         super().__init__(**data)

import sqlmodel
import typing as t


class File(sqlmodel.SQLModel, table=True):
    id: int = sqlmodel.Field(primary_key=True)
    pk: str
    stem: str
    prefix: str

    def __init__(self, **data: t.Any) -> None:
        data["pk"] = data["stem"]
        super().__init__(**data)
