import uuid
import sqlmodel
import typing as t


class MySQLModel(sqlmodel.SQLModel):
    """
    All db models that are stored in
    should inherit from this class.
    """

    pk: str = sqlmodel.Field(primary_key=True, default=str(uuid.uuid4()))

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
