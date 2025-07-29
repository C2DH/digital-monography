import uuid
import sqlmodel
import typing as t

try:
    from keys import KeyPath
except (ImportError, ModuleNotFoundError):
    from ..keys import KeyPath  # type: ignore


class MySQLModel(sqlmodel.SQLModel):
    """
    All db models that are stored in
    should inherit from this class.

    Extending existing tables if needed since the file with this model
    is duplicated among microservices.
    https://docs.sqlalchemy.org/en/13/core/metadata.html#sqlalchemy.schema.Table.params.extend_existing
    """

    __table_args__ = {"extend_existing": True}

    pk: str = sqlmodel.Field(
        primary_key=True, default_factory=lambda: str(uuid.uuid4())
    )
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

    @classmethod
    def has_db_table(cls) -> bool:
        """Returns True if the model has a db table assigned."""
        model_config = getattr(cls, "model_config", {})
        return model_config.get("table") == True

    # def has_db_table(self) -> bool:
    #     # ah, because this needs an instance, but I have a class
    #     """Returns True if the model has a db table assigned."""
    #     model_config = getattr(self, "model_config", {})
    #     return model_config.get("table") == True


# Metadata tables and warnings fit were left to DynamoDB,
# but maybe they should have a schema as well.
