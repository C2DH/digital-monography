import bs4
import sqlmodel

try:
    from ._base import MySQLModel
    from keys import KeyPath
except (ImportError, ModuleNotFoundError):
    from ._base import MySQLModel  # type: ignore
    from ..keys import KeyPath  # type: ignore


DESC = {
    "bookmark": "Bookmark in a `.docx` file where a chapter begins. Serves as a target in table of contents. Should be defined in the frontmatter.",
    "book_slug": "Slug of the book the chapter belongs to. Automatically derived from the file path.",
    "chapter_slug": "Slug of the chapter. Serves as a path to a webpage in the digital version of a book.",
    "prefix": "Prefix of the chapter, e.g. '1', '1.1', 'A', 'A.1'. Used in handling numbers, both refs and targets.",
    "fn": "An author can optionally define a custom file name for a chapter. If not defined, the chapter slug is used. Should be set in the frontmatter.",
    #
    # "src_key": "Key to source file, i.e. a document that will be processed into a chapter.",
    "fm_key": "Frontmatter key. Location of the frontmatter where the chapter is defined.",
    "jb_key": "Key to jupyter book input file. It is derived from other values.",
    "docx_key": "Key to the .docx output file that will be used in typesetting. It is derived from other values.",
}


class Chapter(MySQLModel, table=True):
    "Entry in the '_toc' field from a frontmatter table."

    __tablename__ = "chapters"

    bookmark: str = sqlmodel.Field(description=DESC["bookmark"])
    book_slug: str = sqlmodel.Field(description=DESC["book_slug"])
    chapter_slug: str = sqlmodel.Field(description=DESC["chapter_slug"])
    prefix: str = sqlmodel.Field(description=DESC["prefix"])
    fn: str | None = sqlmodel.Field(default=None, description=DESC["fn"])
    # NOTE: maybe src_key too if src_key is different from fm_key?
    x_fm_key: str = sqlmodel.Field(alias="fm_key", description=DESC["fm_key"])
    x_jb_key: str = sqlmodel.Field(alias="jb_key", description=DESC["jb_key"])
    x_docx_key: str = sqlmodel.Field(alias="docx_key", description=DESC["docx_key"])

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

    @property
    def docx_key(self) -> KeyPath:
        return KeyPath(self.x_docx_key)

    @docx_key.setter
    def docx_key(self, val: KeyPath) -> None:
        self.x_docx_key = str(val)


class ChapterService:
    @staticmethod
    def generate_chapters_from_toc(
        toc: list[dict[str, str | KeyPath]],
    ) -> list[Chapter]:
        """
        Generate a list of Chapter objects from a parsed frontmatter.
        Note that this couldn't be done in the Chapter class itself,
        because we might need access to the whole ToC, e.g. number in the list.
        """
        chapters = []
        for idx, chapter in enumerate(toc, 1):
            fm_key = chapter["frontmatter_key"]
            chapter["book_slug"] = fm_key.slug
            chapter["prefix"] = chapter["prefix"] if "prefix" in chapter else str(idx)
            chapter["fm_key"] = fm_key.efs_work_path
            chapter["chapter_slug"] = _get_chapter_slug_from_toc(idx, chapter)
            chapter["jb_key"] = _get_jb_key(chapter)
            chapter["docx_key"] = _get_docx_key(chapter)
            chapters.append(Chapter(**chapter))
        return chapters

    @staticmethod
    def generate_chapter_from_h1(
        idx: int, frontmatter_key: KeyPath, h1: bs4.Tag | None = None
    ) -> Chapter:
        """
        Generate a Chapter obj while splitting a document into chapters.
            :param idx: index of the chapter in the book, where 0 denotes content before first h1 tag.
            :param frontmatter_key: keypath to a file with a frontmatter where the chapter is defined.
            :param h1: the h1 tag that begins the chapter.
        """
        chapter_slug = _get_chapter_slug_from_h1(idx, h1)
        chapter = {
            "bookmark": "",  # if this func is called, there is no bookmark
            "book_slug": frontmatter_key.slug,
            "chapter_slug": chapter_slug,
            "prefix": str(idx),
            "fn": chapter_slug,
            "fm_key": frontmatter_key.efs_work_path,
        }
        chapter["jb_key"] = _get_jb_key(chapter)
        chapter["docx_key"] = _get_docx_key(chapter)
        return Chapter(**chapter)


def _get_chapter_filename(chapter: dict[str, str | KeyPath]) -> str:
    # TODO: consider a smarter way to add fn prefix, e.g. 01 in 01_first_chapter
    fn = chapter["fn"].lower() if "fn" in chapter else chapter["chapter_slug"].lower()
    fn = "".join(ch for ch in fn if ch.isalnum() or ch in ("-", "_"))
    return fn


def _get_jb_key(chapter: dict[str, str | KeyPath]) -> KeyPath:
    """Returns /mnt/efs/_JB/my-slug/filename.md"""
    fm_key = chapter["fm_key"]
    assert isinstance(fm_key, KeyPath)
    fn = _get_chapter_filename(chapter)
    key = fm_key.efs_jb_dir / fn
    return key.with_suffix(".md")


def _get_docx_key(chapter: dict[str, str | KeyPath]) -> KeyPath:
    """Returns /mnt/efs/_PAPER/my-slug/filename.docx"""
    fm_key = chapter["fm_key"]
    assert isinstance(fm_key, KeyPath)
    fn = _get_chapter_filename(chapter)
    key = fm_key.efs_paper_dir / fn
    return key.with_suffix(".docx")


def _get_chapter_slug_from_toc(i: int, chapter: dict[str, str]) -> str:
    """
    Returns a slug from parsing a table of contents set in a frontmatter.
    The slug will be part of an url path to the Jupyter Book page,
    e.g. `03-chapter-slug` in `website.com/read/book-slug/03-chapter-slug.html`.
    """
    if not chapter.get("slug"):
        return chapter.get("bookmark", f"{i}-chapter").replace("_", "-").lower()
    slug = chapter["slug"]
    del chapter["slug"]
    return slug


def _get_chapter_slug_from_h1(idx: int, h1: bs4.Tag | None) -> str:
    """
    Returns a chapter slug from splitting by h1 tags.
    The slug will be part of an url path to the Jupyter Book page,
    e.g. `03-chapter-slug` in `website.com/read/book-slug/03-chapter-slug.html`.
    """
    if idx == 0 and h1 is None:
        chapter_slug = "0-index"
    elif h1 is None:
        chapter_slug = f"{idx}-chapter"
    else:
        tag_text = h1.get_text().strip().replace(" ", "-").lower()
        chapter_slug = "".join(
            ch for ch in tag_text if ch.isalnum() or ch in ("-", "_")
        )
    return chapter_slug
