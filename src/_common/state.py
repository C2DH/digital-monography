import collections
import json
import sqlmodel
from sqlmodel.main import SQLModelMetaclass
import typing as t

try:
    from keys import KeyPath
    from models import Chapter, DocumentMetadata, tables_to_models
    from models._base import MySQLModel
except (ImportError, ModuleNotFoundError):
    from .keys import KeyPath  # type: ignore
    from .models import Chapter, DocumentMetadata, tables_to_models  # type: ignore
    from .models._base import MySQLModel  # type: ignore


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
            * assets: data from the Metadata tables describing assets
            * refs: references (links and cross-references)
            * targets: reference targets (e.g. headings, captions)
            * substitutions: used to replace text with other text
            * citation_groups: groupings of one or more citation
            * citation_items: citations of a single source
            * files: files (main parts of the book) in the book
    """

    def __init__(self, key: t.Optional[KeyPath] = None) -> None:
        # NOTE: for __dict__ can only have sqlmodel.SQLModel-s,
        # but that might change in the future once we add DynamoDB into the mix.
        self.__dict__: dict[str, list[sqlmodel.SQLModel]] = {}
        self.temp: dict[str, t.Any] = {}
        if key is not None:
            key = KeyPath(key)
            self.add(
                DocumentMetadata(
                    **{
                        "key": key,
                        "loc": key,
                        "slug": key.slug if key else "",
                        "word_count": 0,
                        "char_count": 0,
                    }
                )
            )

    def __getitem__(self, item) -> list[sqlmodel.SQLModel]:
        if item in self.__dict__:
            return self.__dict__[item]
        return []

    @property
    def metadata(self) -> DocumentMetadata:
        tablename = DocumentMetadata.__tablename__
        if tablename not in self.__dict__ or not self.__dict__[tablename]:
            raise ValueError("Metadata is not set.")
        return self.__dict__[tablename][0]

    @property
    def key(self) -> KeyPath:
        return self.metadata.key

    def add(self, record: sqlmodel.SQLModel) -> None:
        """Add a model's instance (a record) to the state."""
        if not isinstance(record, sqlmodel.SQLModel):
            raise TypeError(f"Expected sqlmodel.SQLModel, got {type(record)}")
        self.__dict__.setdefault(record.__tablename__, []).append(record)

    def get(
        self, tablename: str, val: str | int, attrib: str = "pk"
    ) -> t.Optional[sqlmodel.SQLModel]:
        """Get a model's instance (a record) from the state."""
        records = self.__dict__.get(tablename, [])
        try:
            return next(rec for rec in records if getattr(rec, attrib) == val)
        except StopIteration:
            return None

    def filter(
        self, tablename: str, val: str | int | bool, attrib: str
    ) -> list[sqlmodel.SQLModel]:
        """Filter 0 or more models instances (records) from the state."""
        records = self.__dict__.get(tablename, [])
        return [rec for rec in records if getattr(rec, attrib) == val]

    def first(self, tablename: str) -> t.Optional[sqlmodel.SQLModel]:
        """Get the first model's instance (a record) from the state."""
        records = self.__dict__.get(tablename, [])
        if records:
            return records[0]
        return None

    def all(self, tablename: str) -> list[sqlmodel.SQLModel]:
        return self.__dict__.get(tablename, [])

    def len(self, tablename: str) -> int:
        """Get the number of records in a current document's state."""
        return len(self.__dict__.get(tablename, []))

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

    def sql_insert_all(self, session: sqlmodel.Session) -> None:
        """
        Send a sql INSERT command with all records that have a SQLModel db table assigned.
        Note that during iteration we are generating the sql statement and
        at the end we emit a single sql COMMIT command to the database
        (assuming we have 1 db connection). After the commit, the db connection is released
        back to the connection pool (important for unlocking SQLite db).
        """
        for _, records in self.__dict__.items():
            if _ == "doc_metadata":
                continue
            if (
                records
                and isinstance(records[0], MySQLModel)
                and has_db_table(records[0])
                # and records[0].has_db_table()
            ):
                session.add_all(records)
        session.commit()

    def sql_delete_by_key(self, session: sqlmodel.Session, key: KeyPath) -> None:
        """
        Send a sql DELETE command to remove all db rows for a given document (filtered
        by key). This is used to delete all records for currently processed document
        before inserting new ones, so that there are no duplicated datapoints.

        Note we are operating not on records but on models' classes. This is
        because DocumentState might be empty while a database might have data.

        Note that during iteration we are generating the sql statement and
        at the end we emit a single sql COMMIT command to the database
        (assuming we have 1 db connection). After the commit, the db connection is released
        back to the connection pool (important for unlocking SQLite db).
        """
        for model in tables_to_models.values():
            model: SQLModelMetaclass
            if isinstance(model, SQLModelMetaclass) and has_db_table(model):
                assert hasattr(
                    model, "x_loc"
                ), f"Model {model.__name__} does not have x_loc attribute. Every db table model should inherit from {MySQLModel.__name__}."
                model: MySQLModel
                statement = sqlmodel.delete(model).where(model.x_loc == str(key))
                session.exec(statement)
        session.commit()

    def __str__(self) -> str:
        return json.dumps(self.__dict__, default=str)


def read_book_metadata(key: KeyPath) -> dict[str, DocumentState]:
    """
    Read JSON state stored in Elastic File System (EFS) and update the __dict__
    with all DocumentState objects for a specific book.
    """
    book_metadata: dict[str, DocumentState] = {}
    for meta_file in key.efs_state_dir.glob("**/*.json"):
        meta_file: KeyPath
        with meta_file.open("r") as f:
            state = DocumentState(meta_file)
            state.from_dict(json.load(f))
            book_metadata[meta_file.stem] = state
    return book_metadata


class BookState(collections.abc.MutableMapping):
    """
    Collection of DocumentState data.
    It is meant to act as an inter-microservice state describing a single book
    consisting of one or more docx or ipynb documents.

    The usage pattern is not yet fully understood, so I made 2 alternative
    data structures to use:
    * hashmap (self.docstates) and
    * records (self.all_records).

    TODO: consider an adapter over JupyterBook config and ToC.
    """

    def __init__(self) -> None:
        self.docstates: dict[KeyPath, DocumentState] = {}
        self.all_records: DocumentState | None = None

    # TODO: Dunder methods should be targeting self.all_records instead.
    # Bookstate should require merging all docstates first.

    def __contains__(self, name: str) -> bool:
        return name in self.docstates

    def __getitem__(self, name: str) -> DocumentState:
        return self.docstates[name]

    def __setitem__(self, name: str, value: DocumentState):
        self.docstates[name] = value

    def __delitem__(self, name: str):
        del self.docstates[name]

    def __iter__(self):
        return iter(self.docstates)

    def __len__(self):
        return len(self.docstates)

    def load_from_file(self, key: KeyPath) -> None:
        """
        Read JSON state stored in a file system, i.e.
        * from Elastic File System (EFS) in AWS, or
        * from /tmp directory during local development.
        Then, update the docstates with all DocumentState objects for a specific book.
        Creates new DocumentState object that contains all the records.
        """
        for meta_file in key.efs_state_dir.glob("**/*.json"):
            meta_file: KeyPath
            with meta_file.open("r") as f:
                state = DocumentState(meta_file)
                state.from_dict(json.load(f))
                assert (
                    len(state["chapters"]) == 1
                ), "Each docstate should have exactly 1 chapter."
                chapter: Chapter = state.first("chapters")
                assert isinstance(chapter.jb_key, KeyPath)
                self.docstates[chapter.jb_key] = state
                # self.docstates[meta_file.stem] = state

    def merge_docstate(self, key: KeyPath) -> DocumentState:
        """
        Merge all DocumentState objects into one.
        Used by aggregation microservices to have an overview of the whole book.
        """
        self.all_records = DocumentState(key)
        for docstate in self.docstates.values():
            for records in docstate.__dict__.values():
                for record in records:
                    self.all_records.add(record)
        return self.all_records

    def get(
        self, tablename: str, val: str | int, attrib: str = "pk"
    ) -> t.Optional[sqlmodel.SQLModel]:
        """Get a model's instance (a record) from all document state objects."""
        return self.all_records.get(tablename, val, attrib)

    def filter(
        self, tablename: str, val: str | int | bool, attrib: str
    ) -> list[sqlmodel.SQLModel]:
        """Filter 0 or more models instances (records) from the state."""
        return self.all_records.filter(tablename, val, attrib)

    def all(self, tablename: str) -> list[sqlmodel.SQLModel]:
        return self.all_records.all(tablename)

    def len(self, tablename: str) -> int:
        """Get the number of records in a current document's state."""
        return self.all_records.len(tablename)


def has_db_table(model: sqlmodel.SQLModel | sqlmodel.main.SQLModelMetaclass) -> bool:
    """Returns True if the model has a db table assigned."""
    model_config = getattr(model, "model_config", {})
    return model_config.get("table") == True
