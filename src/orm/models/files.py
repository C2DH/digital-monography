import sqlmodel
import typing as t


class File(sqlmodel.SQLModel, table=True):
    __tablename__ = "files"

    id: int = sqlmodel.Field(primary_key=True)
    pk: str
    stem: str
    prefix: str

    def __init__(self, **data: t.Any) -> None:
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


class Heading(sqlmodel.SQLModel, table=True):
    __tablename__ = "headings"

    id: int = sqlmodel.Field(primary_key=True)
    file_name: str
    elem: str
    level: str
    text: str
    word_count: int
    char_count: int
    target: str


# class HeadingDatapoint(DatapointBase):
#     schema_v: int = 1  # if multiple v in the db, the client might have to differentiate
#     ###
#     file_name: str
#     elem: str
#     level: str
#     text: str
#     word_count: int
#     char_count: int
#     target: str
