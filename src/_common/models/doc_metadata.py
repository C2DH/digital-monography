import typing as t

try:
    from ._base import MySQLModel
    from keys import KeyPath
except (ImportError, ModuleNotFoundError):
    from ._base import MySQLModel  # type: ignore
    from ..keys import KeyPath  # type: ignore


class DocumentMetadata(MySQLModel):
    pass
