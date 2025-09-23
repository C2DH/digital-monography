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


DESCRIPTIONS = {
    "bookmark": "Bookmark in a `.docx` file where a chapter begins. Serves as a target in table of contents. Should be defined in the frontmatter.",
    "book_slug": "Slug of the book the chapter belongs to. Automatically derived from the file path.",
    "chapter_slug": "Slug of the chapter. Serves as a path to a webpage in the digital version of a book.",
    "prefix": "Prefix of the chapter, e.g. '1', '1.1', 'A', 'A.1'. Used in handling numbers, both refs and targets.",
    "curr_file": "Location of the frontmatter where the chapter is defined.",
    "fp": "File path of the chapter, derived from other values.",
    "fn": "An author can optionally define a custom file name for a chapter. If not defined, the chapter slug is used. Should be set in the frontmatter.",
}


class Chapter(MySQLModel, table=True):
    "Entry in the '_toc' field from a frontmatter table."

    __tablename__ = "chapters"

    bookmark: str = sqlmodel.Field(description=DESCRIPTIONS["bookmark"])
    book_slug: str = sqlmodel.Field(description=DESCRIPTIONS["book_slug"])
    chapter_slug: str = sqlmodel.Field(description=DESCRIPTIONS["chapter_slug"])
    prefix: str = sqlmodel.Field(description=DESCRIPTIONS["prefix"])
    curr_file: str = sqlmodel.Field(description=DESCRIPTIONS["curr_file"])
    x_fp: str = sqlmodel.Field(alias="fp", description=DESCRIPTIONS["fp"])
    fn: str | None = sqlmodel.Field(default=None, description=DESCRIPTIONS["fn"])

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
            chapter["chapter_slug"] = ChapterService._get_chapter_slug(i, chapter)
            chapter["prefix"] = chapter["prefix"] if "prefix" in chapter else str(i)
            chapter["fp"] = ChapterService.get_chapter_filepath(chapter)
            chapter["book_slug"] = chapter["fp"].slug
            chapter["curr_file"] = str(chapter["_curr_file"])
            chapters.append(Chapter(**chapter))
        return chapters

    @staticmethod
    def get_chapter_filepath(chapter: dict[str, str | KeyPath]) -> KeyPath:
        curr_file = chapter.get("_curr_file")
        if isinstance(curr_file, KeyPath):
            slug = curr_file.slug
        else:
            slug = "".join(random.choices(string.ascii_lowercase, k=8))
        fn = (
            chapter["fn"].lower()
            if "fn" in chapter
            else chapter["chapter_slug"].lower()
        )
        fn = "".join(ch for ch in fn if ch.isalnum() or ch in ("-", "_"))
        # NOTE: this is /tmp/efs/slug/fn so NOT jb or paper dir
        # TODO: change to include jb dir and paper dir
        key: KeyPath = KeyPath(DEFAULT_SFS_DIR) / slug / fn
        return key.with_suffix(".docx")

    @staticmethod
    def _get_chapter_slug(i: int, chapter: dict[str, str]) -> str:
        if not chapter.get("slug"):
            return chapter.get("bookmark", f"{i}-chapter").replace("_", "-").lower()
        slug = chapter["slug"]
        del chapter["slug"]
        return slug
