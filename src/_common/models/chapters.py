import sqlmodel

try:
    from ._base import MySQLModel
    from keys import KeyPath
    from constants import DEFAULT_SFS_DIR
except (ImportError, ModuleNotFoundError):
    from ._base import MySQLModel  # type: ignore
    from ..keys import KeyPath  # type: ignore
    from ..constants import DEFAULT_SFS_DIR


class Chapter(MySQLModel, table=True):
    "Entry in the '_toc' field from a frontmatter table."

    __tablename__ = "chapters"

    bookmark: str
    slug: str
    prefix: str
    x_fp: str = sqlmodel.Field(alias="fp")
    fn: str | None = sqlmodel.Field(default=None)

    @property
    def fp(self) -> KeyPath:
        return KeyPath(self.x_fp)

    @fp.setter
    def fp(self, val: KeyPath) -> None:
        self.x_fp = str(val)


class ChapterService:
    @staticmethod
    def parse_toc(toc: list[dict[str, str]]) -> list[Chapter]:
        """
        Parse the '_toc' frontmatter field into a list of Chapter objects.
        Note that this couldn't be done in the Chapter class itself,
        because we might need access to the whole ToC, e.g. number in the list.
        """
        chapters = []
        for i, chapter in enumerate(toc, 1):
            if "slug" not in chapter:
                chapter["slug"] = chapter["bookmark"].replace("_", "-").lower()
            if "prefix" not in chapter or not chapter["prefix"]:
                chapter["prefix"] = str(i)
            if chapter["fn"]:
                chapter["fp"] = KeyPath(DEFAULT_SFS_DIR) / chapter["fn"]
            chapters.append(Chapter(**chapter))
        return chapters
