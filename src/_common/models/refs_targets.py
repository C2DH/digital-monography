import sqlmodel

try:
    from ._base import MySQLModel
except (ImportError, ModuleNotFoundError):
    from ._base import MySQLModel  # type: ignore

DESC = {
    "target_id": "Hash of an element in a document, which is referenced by a Ref.",
    "proc_href": (
        'Processed "href" attribute of a anchor tag element to some target. '
        "Includes path to a file where the target is located and the previous href."
    ),
}


class RefTarget(MySQLModel, table=True):
    """
    RefTarget is a bridge table between a Ref and a Target.

    One element in a document might have multiple RefTargets, but only one Target.
    The target labels must be consolidated before running Jupyter Book v2, otherwise
    some labels might be removed down the stream by mystmd.
    """

    __tablename__ = "ref_targets"

    target_id: str = sqlmodel.Field(description=DESC["target_id"])
    proc_href: str = sqlmodel.Field(description=DESC["proc_href"])
