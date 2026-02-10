import sqlmodel

try:
    from ._base import ChapterSQLModel
except (ImportError, ModuleNotFoundError):
    from ._base import ChapterSQLModel  # type: ignore


class CitationGroup(ChapterSQLModel, table=True):
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

    # pk: str = sqlmodel.Field(primary_key=True)
    id: str = sqlmodel.Field(description="The citationID")
    file_name: str
    citation_schema: str
    formattedCitation: str
    noteIndex: int
    plainCitation: str
    slug: str


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
