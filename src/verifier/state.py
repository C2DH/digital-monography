import json
import sqlmodel
import sqlalchemy
import sqlalchemy.orm
import typing as t

try:
    from keys import KeyPath
    from models import DocumentMetadata, tables_to_models
    from models._base import MySQLModel
except (ImportError, ModuleNotFoundError):
    from .keys import KeyPath  # type: ignore
    from .models import DocumentMetadata, tables_to_models
    from .models._base import MySQLModel


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
        self.__dict__: dict[str, list[sqlmodel.SQLModel]] = {}
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

    # def sql_insert_all(self, session: sqlalchemy.orm.Session) -> None:
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
                and records[0].has_db_table()
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
            if isinstance(model, MySQLModel) and model.has_db_table():
                statement = sqlmodel.delete(model).where(model.loc == key)
                print(">> loc", statement)
                session.exec(statement)
                statement = sqlmodel.delete(model).where(model.x_loc == key)
                print(">> x_loc", statement)
                session.exec(statement)
        session.commit()

    def __str__(self) -> str:
        return json.dumps(self.__dict__, default=str)
