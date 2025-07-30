import sqlmodel

try:
    from _base import MySQLModel
except (ImportError, ModuleNotFoundError):
    from ._base import MySQLModel  # type: ignore


class Heading(MySQLModel, table=True):
    __tablename__ = "headings"

    # id: int = sqlmodel.Field(primary_key=True)
    file_name: str
    elem: str
    level: str
    text: str
    word_count: int
    char_count: int
    target: str
    slug: str


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
