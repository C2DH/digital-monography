import uuid
import sqlmodel
import typing as t

try:
    from keys import KeyPath
except (ImportError, ModuleNotFoundError):
    from ..keys import KeyPath  # type: ignore


class BookSQLModel(sqlmodel.SQLModel):
    """
    All db models from book-level should inherit from this class.
    Unlike chapter-level models, data extracted from book should use int id
    instead of complicated UUID.

    Book-level models are NOT handled with DocumentState.sql_insert_all() or DocumentState.sql_delete_by_key()
    and therefore must be inserted/deleted manually.

    Extending existing tables is needed since the file with this model
    can be duplicated among microservices.
    https://docs.sqlalchemy.org/en/13/core/metadata.html#sqlalchemy.schema.Table.params.extend_existing
    """

    __table_args__ = {"extend_existing": True}

    id: int | None = sqlmodel.Field(default=None, primary_key=True)

    def __init__(self, **data: t.Dict[str, t.Any]) -> None:
        for k, v in data.items():
            if isinstance(v, KeyPath):
                data[k] = str(v)
        super().__init__(**data)

    def model_dump(self, *args, **kwargs) -> t.Dict[str, t.Any]:
        """
        Override model_dump by removing "x_" prefix from object's keys.
        In Pydantic, private attributes are prefixed with "_" but
        in SQLModel's tables such prefix is not allowed. Thus, I use "x_" instead.

        Thanks to this method, this works:
        `MyModel(**mymodel_instance.model_dump())`
        SomeModel needs arguments without "x_" prefix.
        """
        dump = super().model_dump(*args, **kwargs)
        for k, v in dump.copy().items():
            if k.startswith("x_"):
                dump[k[2:]] = dump.pop(k)
            else:
                dump[k] = v
        return dump


class ChapterSQLModel(sqlmodel.SQLModel):
    """
    All db models from chapter-level should inherit from this class.
    Unlike book-level models, data extracted from chapter must include
    UUID primary key and a chapter location.

    Chapter-level models are extracted from chapters (book's content)
    and thus must be prepared to handle concurrency or - when deployed with
    AWS Lambda - parallelism.

    Extending existing tables is needed since the file with this model
    can be duplicated among microservices.
    https://docs.sqlalchemy.org/en/13/core/metadata.html#sqlalchemy.schema.Table.params.extend_existing
    """

    __table_args__ = {"extend_existing": True}

    pk: str = sqlmodel.Field(primary_key=True, default_factory=lambda: uuid.uuid4().hex)
    x_loc: str = sqlmodel.Field(alias="loc")

    @property
    def loc(self) -> KeyPath:
        return KeyPath(self.x_loc)

    @loc.setter
    def loc(self, val: KeyPath) -> None:
        self.x_loc = str(val)

    def __init__(self, **data: t.Dict[str, t.Any]) -> None:
        for k, v in data.items():
            if isinstance(v, KeyPath):
                data[k] = str(v)
        super().__init__(**data)

    def model_dump(self, *args, **kwargs) -> t.Dict[str, t.Any]:
        """
        Override model_dump by removing "x_" prefix from object's keys.
        In Pydantic, private attributes are prefixed with "_" but
        in SQLModel's tables such prefix is not allowed. Thus, I use "x_" instead.

        Thanks to this method, this works:
        `MyModel(**mymodel_instance.model_dump())`
        SomeModel needs arguments without "x_" prefix.
        """
        dump = super().model_dump(*args, **kwargs)
        for k, v in dump.copy().items():
            if k.startswith("x_"):
                dump[k[2:]] = dump.pop(k)
            else:
                dump[k] = v
        return dump


# Metadata tables and warnings fit were left to DynamoDB,
# but maybe they should have a schema as well.
