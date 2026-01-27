import sqlmodel

try:
    from ._base import ChapterSQLModel
    from keys import KeyPath
except (ImportError, ModuleNotFoundError):
    from ._base import ChapterSQLModel  # type: ignore
    from ..keys import KeyPath  # type: ignore

DESC = {
    "target_id": "Hash of an element in a document, which is referenced by a Ref.",
    "proc_href": (
        'Processed "href" attribute of a anchor tag element to some target. '
        "Includes path to a file where the target is located and the previous href."
    ),
    "fm_key": "Frontmatter key. Location of the source file where the target is placed.",
    "jb_key": "Key to jupyter book markdown file. After linking, a ref will point to this file.",
    "fragment": (
        "Local id unique only inside the DOCX file. When referencing across files, "
        "combine with target file id.",
    ),
}


class RefTarget(ChapterSQLModel, table=True):
    """
    RefTarget is a bridge table between a Ref and a Target.

    One element in a document might have multiple RefTargets, but only one Target.
    The target labels must be consolidated before running Jupyter Book v2, otherwise
    some labels might be removed down the stream by mystmd.
    """

    __tablename__ = "ref_targets"

    target_id: str = sqlmodel.Field(description=DESC["target_id"])
    proc_href: str = sqlmodel.Field(description=DESC["proc_href"])
    x_fm_key: str = sqlmodel.Field(alias="fm_key", description=DESC["fm_key"])
    x_jb_key: str = sqlmodel.Field(alias="jb_key", description=DESC["jb_key"])
    fragment: str = sqlmodel.Field(description=DESC["fragment"])

    @property
    def fm_key(self) -> KeyPath:
        return KeyPath(self.x_fm_key)

    @fm_key.setter
    def fm_key(self, val: KeyPath) -> None:
        self.x_fm_key = str(val)

    @property
    def jb_key(self) -> KeyPath:
        return KeyPath(self.x_jb_key)

    @jb_key.setter
    def jb_key(self, val: KeyPath) -> None:
        self.x_jb_key = str(val)
