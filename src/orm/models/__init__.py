import sqlalchemy
import sqlmodel
from ._base import Base  # noqa
from .assets import Asset
from .citation_groups import CitationGroup
from .citation_items import CitationItem
from .files import File
from .headings import Heading
from .doc_metadata import DocumentMetadata
from .refs import Ref
from .substitutions import Substitution
from .targets import Target
from .users import User

type ModelMeta = sqlmodel.main.SQLModelMetaclass | sqlalchemy.orm.DeclarativeMeta


__all__ = [
    "Asset",
    "CitationGroup",
    "CitationItem",
    "File",
    "Heading",
    "DocumentMetadata",
    "Ref",
    "Substitution",
    "Target",
    "User",
]

tables_to_models: dict[str, ModelMeta] = {
    "assets": Asset,
    "citation_groups": CitationGroup,
    "citation_items": CitationItem,
    "files": File,
    "headings": Heading,
    "document_metadata": DocumentMetadata,
    "refs": Ref,
    "substitutions": Substitution,
    "targets": Target,
    "users": User,
}


# def map_tables_to_models() -> dict[str, ModelMeta]:
#     """
#     Returns a dictionary of db model classes indexed by associate database
#     table names:
#     `"assets": <class 'src.{microservice}.models.assets.Asset'>`.
#     This is useful when we only know table names.
#     """
#     res = {}
#     for model in map(thismodule.__dict__.get, thismodule.__all__):
#         model: ModelMeta
#         if hasattr(model, "__tablename__"):
#             res[getattr(model, "__tablename__")] = model
#     return res


# MetadataTableDatapoint is only kwargs, so it's better suited for DynDB.
