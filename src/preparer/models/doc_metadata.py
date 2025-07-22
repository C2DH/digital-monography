import typing as t

try:
    from ._base import MySQLModel
    from keys import KeyPath
except (ImportError, ModuleNotFoundError):
    from ._base import MySQLModel  # type: ignore
    from ..keys import KeyPath  # type: ignore


class DocumentMetadata(MySQLModel):
    __tablename__ = "doc_metadata"

    x_key: str
    slug: str = ""
    word_count: int = 0
    char_count: int = 0

    @property
    def key(self) -> KeyPath:
        return KeyPath(self.x_key)

    @key.setter
    def key(self, val: KeyPath) -> None:
        self.x_key = str(val)

    def __init__(self, **data: t.Dict[str, t.Any]) -> None:
        data["x_key"] = str(data["key"])
        super().__init__(**data)
