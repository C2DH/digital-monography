import sqlmodel

try:
    from ._base import MySQLModel
except (ImportError, ModuleNotFoundError):
    from ._base import MySQLModel  # type: ignore


class AssetMetadata(MySQLModel, table=True):
    """
    Data from a Metadata table that describes an asset.
    """

    __tablename__ = "asset_metadata"

    id: str
    author: str
    digitalinput: str
    paperinput: str
    license: str
    source: str
    height: str = sqlmodel.Field(default="100%")
    alttext: str
    iscolor: bool
    deleteprevious: bool
    comments: str
    isready: bool = sqlmodel.Field(default=False)
    kwargs: str


##########################################


# class MetadataTableDatapoint(DatapointBase):
#     """
#     Unprocessed data from a Metadata table that describes an asset.
#     """

#     schema_v: int = 1  # if multiple v in the db, the client might have to differentiate
#     ###
#     kwargs: dict[str, t.Any]

#     def to_json(self) -> dict[str, PrimitiveValues]:
#         "Converts the dataclass obj to a dict with str/int/bool as values."
#         return {"pk": self.pk, "kwargs": json.dumps(self.kwargs, default=str)}

#     @classmethod
#     def from_json(cls: t.Type[T], json_data: dict[str, PrimitiveValues]) -> T:
#         return cls(
#             **{
#                 "pk": json_data["pk"],
#                 "kwargs": json.loads(json.dumps(json_data["kwargs"])),
#             }
#         )
#         # return cls(
#         #     **{"pk": json_data["pk"], "kwargs": json.loads(str(json_data["kwargs"]))}
#         # )
