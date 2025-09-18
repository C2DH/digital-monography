import random
import string
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
    book_slug: str
    chapter_slug: str
    prefix: str
    curr_file: str
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
    def parse_toc(toc: list[dict[str, str | KeyPath]]) -> list[Chapter]:
        """
        Parse the '_toc' frontmatter field into a list of Chapter objects.
        Note that this couldn't be done in the Chapter class itself,
        because we might need access to the whole ToC, e.g. number in the list.
        """
        chapters = []
        for i, chapter in enumerate(toc, 1):
            chapter["chapter_slug"] = _get_chapter_slug(i, chapter)
            chapter["prefix"] = chapter["prefix"] if "prefix" in chapter else str(i)
            chapter["fp"] = _get_fp(chapter)
            chapter["book_slug"] = chapter["fp"].slug
            chapter["curr_file"] = str(chapter["_curr_file"])
            chapters.append(Chapter(**chapter))
        return chapters


def _get_chapter_slug(i: int, chapter: dict[str, str]) -> str:
    if not chapter.get("slug"):
        return chapter.get("bookmark", f"{i}-chapter").replace("_", "-").lower()
    slug = chapter["slug"]
    del chapter["slug"]
    return slug


def _get_fp(chapter: dict[str, str | KeyPath]) -> KeyPath:
    curr_file = chapter.get("_curr_file")
    if isinstance(curr_file, KeyPath):
        slug = curr_file.slug
    else:
        slug = "".join(random.choices(string.ascii_lowercase, k=8))
    fn = chapter["fn"].lower() if "fn" in chapter else chapter["chapter_slug"].lower()
    fn = "".join(ch for ch in fn if ch.isalnum() or ch in ("-", "_"))
    key: KeyPath = KeyPath(DEFAULT_SFS_DIR) / slug / fn
    return key.with_suffix(".docx")
