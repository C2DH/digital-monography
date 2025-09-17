try:
    from _base import MySQLModel
except (ImportError, ModuleNotFoundError):
    from ._base import MySQLModel  # type: ignore


class Chapter(MySQLModel, table=True):
    "Entry in the '_toc' field from a frontmatter table."

    __tablename__ = "chapters"

    bookmark: str
    slug: str
    prefix: str
    fn: str | None


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
            chapters.append(Chapter(**chapter))
        return chapters
