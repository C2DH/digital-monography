# import sqlalchemy as sa
import json
import sqlmodel
import typing as t

try:
    from ._base import MySQLModel
except (ImportError, ModuleNotFoundError):
    from ._base import MySQLModel  # type: ignore


class CitationGroup(MySQLModel, table=True):
    """
    If a manuscript stores citations as objects, those objects can be extracted
    and saved to the database. One citation block is represented by a citation group.
    A citation group can include multiple citation items. An example of a citation group:
    {
        "citationID": "MQAb9y5G",
        "properties": {
            "formattedCitation": "(Jay 2004)",
            "noteIndex": 0,
            "plainCitation": "(Jay 2004)",
        },
        "schema": "https://github.com/citation-style-language/schema/raw/master/csl-citation.json",
    }
    """

    __tablename__ = "citation_groups"

    id: int = sqlmodel.Field(primary_key=True)
    file_name: str
    citation_schema: str
    formattedCitation: str
    noteIndex: int
    plainCitation: str


class CitationItem(MySQLModel, table=True):
    """
    If a manuscript stores citations as objects, those objects can be extracted
    and saved to the database. One citation block is represented by a citation group,
    which consists of one or more citation items. An example of a citation item:
    {
        "id": 3,
        "itemData": {
            "ISBN": "9780867196047",
            "abstract": "This book is about...",
            "author": [{"family": "Jay", "given": "Aye"}],
            "id": 3,
            "issued": {"date-parts": [["2004", 4, 1]]},
            "number-of-pages": "50",
            "publisher": "Last Gasp",
            "title": "Gangsta Rap Coloring Book",
            "type": "book",
        },
        "uris": ["http://zotero.org/users/local/bv74ArEQ/items/KKITI438"],
    }
    """

    __tablename__ = "citation_items"

    pk: str = sqlmodel.Field(primary_key=True)
    id: int
    file_name: str
    citationId: str
    x_uris: str = sqlmodel.Field(alias="uris")
    x_itemData: str = sqlmodel.Field(alias="itemData")
    # x_uris: str = sqlmodel.Field(
    #     sa_column_args=sa.Column("uris", sa.String), alias="uris"
    # )
    # x_itemData: str  # dict[str, t.Any]

    @property
    def uris(self) -> list[str]:
        return self.x_uris.split("|")

    def _get_uris(self, val: list[str]) -> str:
        return "|".join(val)

    @property
    def itemData(self) -> dict[str, t.Any]:
        return json.loads(self.x_itemData)

    def _get_itemData(self, val: dict[str, t.Any]) -> str:
        return json.dumps(val)

    def __init__(self, **data: t.Dict[str, t.Any]) -> None:
        data["uris"] = self._get_uris(data["uris"])
        data["itemData"] = self._get_itemData(data["itemData"])
        super().__init__(**data)


###################

# class CitationGroupDatapoint(DatapointBase):
#     schema_v: int = 1  # if multiple v in the db, the client might have to differentiate
#     ###
#     # id: int
#     file_name: str
#     citation_schema: str
#     # schema: str
#     formattedCitation: str
#     noteIndex: int
#     plainCitation: str


# class CitationItemDatapoint(DatapointBase):
#     schema_v: int = 1  # if multiple v in the db, the client might have to differentiate
#     ###
#     id: int
#     file_name: str
#     citationId: str
#     uris: list[str]
#     itemData: dict[str, t.Any]
