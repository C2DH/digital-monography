import json
import sqlmodel
import typing as t

try:
    from keys import KeyPath
    from models import DocumentMetadata, tables_to_models
except (ImportError, ModuleNotFoundError):
    from .keys import KeyPath  # type: ignore
    from .models import DocumentMetadata, tables_to_models


type PrimitiveValues = str | int | bool | None
type DocumentStateSerialized = dict[str, list[dict[str, PrimitiveValues]]]


class DocumentState:
    """
    Inter-microservice state describing a single docx document.
    The state is preserverd in between microservice calls in a database
    and as a json data appended to the processed document. It can be retrieved
    by the dashboard from the database or by another microservice from the json.

    The state consists of
        a) metadata and
        b) a collection of records (lists of models) about:
            assets: data from the Metadata tables describing assets
            refs: references (links and cross-references)
            targets: reference targets (e.g. headings, captions)
            substitutions: used to replace text with other text
            citation_groups: groupings of one or more citation
            citation_items: citations of a single source
            files: files (main parts of the book) in the book
    """

    def __init__(self, key: t.Optional[KeyPath] = None) -> None:
        self.__dict__: dict[str, list[sqlmodel.SQLModel]] = {}
        self.add(
            DocumentMetadata(
                **{
                    "key": key,
                    "slug": key.slug if key else "",
                    "word_count": 0,
                    "char_count": 0,
                }
            )
        )

    @property
    def metadata(self) -> DocumentMetadata:
        tablename = DocumentMetadata.__tablename__
        if tablename not in self.__dict__ or not self.__dict__[tablename]:
            raise ValueError("Metadata is not set.")
        return self.__dict__[tablename][0]

    def add(self, record: sqlmodel.SQLModel) -> None:
        """
        Add a model's instance (a record) to the state.
        """
        self.__dict__.setdefault(record.__tablename__, []).append(record)

    def to_dict(self) -> DocumentStateSerialized:
        """
        Serialize the state to dictionary that contains only JSON serializable types.
        """
        res = {}
        for tablename, records in self.__dict__.items():
            res[tablename] = [rec.model_dump(mode="json") for rec in records]
        return res

    def from_dict(self, jsml: DocumentStateSerialized) -> None:
        """
        Deserialize the state to dictionary that contains only JSON serializable types.
        """
        for tablename, records in jsml.items():
            model = tables_to_models.get(tablename)
            if not isinstance(model, sqlmodel.main.SQLModelMetaclass):
                continue
            assert isinstance(model, sqlmodel.main.SQLModelMetaclass)
            self.__dict__[tablename] = [model(**rec) for rec in records]

    def __str__(self) -> str:
        return json.dumps(self.__dict__, default=str)
