import sqlalchemy
import sqlalchemy.orm
import sqlmodel
from .assets import Asset, AssetService  # noqa
from .authors import Author, Book, LinkAuthorsBooks  # noqa
from .config import Config, ConfigService  # noqa
from .citation_groups import CitationGroup
from .citation_items import CitationItem
from .chapters import Chapter, ChapterService  # noqa
from .footnotes import Footnote  # noqa
from .files import File, FileService  # noqa
from .headings import Heading, HeadingService  # noqa
from .doc_metadata import DocumentMetadata
from .refs import Ref, RefService  # noqa
from .refs_targets import RefTarget  # noqa
from .substitutions import Substitution, SubstitutionService  # noqa
from .targets import Target, TargetService  # noqa
from .users import User  # noqa

type ModelMeta = sqlmodel.main.SQLModelMetaclass | sqlalchemy.orm.DeclarativeMeta


__all__ = [
    "Asset",
    "Author",
    "Book",
    "Config",
    "CitationGroup",
    "CitationItem",
    "Chapter",
    "File",
    "Footnote",
    "Heading",
    "DocumentMetadata",
    "Ref",
    "RefTarget",
    "Substitution",
    "Target",
]

tables_to_models: dict[str, ModelMeta] = {
    Asset.__tablename__: Asset,
    Author.__tablename__: Author,
    Book.__tablename__: Book,
    CitationGroup.__tablename__: CitationGroup,
    CitationItem.__tablename__: CitationItem,
    Chapter.__tablename__: Chapter,
    File.__tablename__: File,
    Footnote.__tablename__: Footnote,
    Heading.__tablename__: Heading,
    DocumentMetadata.__tablename__: DocumentMetadata,
    Ref.__tablename__: Ref,
    RefTarget.__tablename__: RefTarget,
    Substitution.__tablename__: Substitution,
    Target.__tablename__: Target,
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
