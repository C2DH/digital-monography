import pytest


from src._common.constants import JB_DIR, PAPER_DIR, WORK_DIR
from src._common.state import DocumentState
from src._common.html2md import convert_to_md
from src._common.models import Chapter, ChapterService
from src._common.keys import KeyPath
from src.preparer.main import _convert_to_html, convert_to_bs
from src.preparer.prep_frontmatter import prepare_frontmatter, FrontmatterBlob
from src.preparer.split_into_chapters import prepend_htmls_with_frontmatter


SLUG = "book-content-examples"


class TestFrontmatterPreparationAndGenChaptersFromToC:
    @classmethod
    def setup_class(cls):
        fp = KeyPath("tests") / "_fixtures" / SLUG / "frontmatter_extraction.docx"
        cls.key = KeyPath("/tmp/efs") / WORK_DIR / SLUG / fp.name
        html_str = _convert_to_html(fp)
        html_soup = convert_to_bs(html_str)
        # cls.html_soup = bs4.BeautifulSoup(html_str, "html.parser")
        # classifiers = [
        #     (is_table, tables),
        # ]
        # for node in cls.html_soup.descendants:
        #     for check_if_meets_criteria, container in classifiers:
        #         if isinstance(node, bs4.element.Tag) and check_if_meets_criteria(node):
        #             container.append(node)
        cls.html_soup, cls.frontmatter = prepare_frontmatter(html_soup, cls.key)
        prepend_htmls_with_frontmatter([cls.html_soup], cls.frontmatter)
        dstate = DocumentState(cls.key)
        cls.md = convert_to_md(cls.html_soup, dstate)

    def test_frontmatter_extraction(self):
        assert isinstance(self.frontmatter, FrontmatterBlob)
        assert len(self.frontmatter.all_data.keys()) > 0
        assert len(self.frontmatter.myst_data.keys()) > 0

    def test_simple_value_extraction(self):
        assert self.frontmatter.all_data["title"] == "Just a book"
        assert self.frontmatter.all_data["license"] == "CC-BY-NC-ND-4.0"
        assert (
            self.frontmatter.all_data["github"]
            == "https://github.com/monograph-prototypes/split-to-multiple-chapters"
        )

    def test_list_extraction(self):
        assert isinstance(self.frontmatter.all_data["keywords"], list)
        assert self.frontmatter.all_data["keywords"][0] == "test"
        assert self.frontmatter.all_data["keywords"][1] == "e2e"

    def test_dict_as_value_extraction(self):
        assert isinstance(self.frontmatter.all_data["isbn"], dict)
        assert len(self.frontmatter.all_data["isbn"].keys()) == 3
        assert "ebook" in self.frontmatter.all_data["isbn"]
        assert "hardcover" in self.frontmatter.all_data["isbn"]
        assert "paperback" in self.frontmatter.all_data["isbn"]
        assert self.frontmatter.all_data["isbn"]["ebook"] == "9876543210123"
        assert self.frontmatter.all_data["isbn"]["hardcover"] == "9876543210123"
        assert self.frontmatter.all_data["isbn"]["paperback"] == "9876543210123"

    def test_list_of_dicts_extraction(self):
        assert len(self.frontmatter.all_data["authors"]) == 2
        assert self.frontmatter.all_data["authors"][0] == {
            "name": "Pawel Kaminski",
            "affiliations": "University of Luxembourg",
        }
        assert self.frontmatter.all_data["authors"][1] == {
            "name": "Elisabeth Guerard",
            "affiliations": "Luxembourg Centre for Contemporary and Digital History (C²DH)",
        }

    def test_boolean_value_extraction(self):
        # TODO: should this be converted to bool?
        assert self.frontmatter.all_data["open_access"] == "True"

    def test_mystmd_frontmatter_has_fields_from_specs(
        self,
    ):
        assert "title" in self.frontmatter.myst_data
        assert "authors" in self.frontmatter.myst_data
        assert "keywords" in self.frontmatter.myst_data
        assert "license" in self.frontmatter.myst_data
        assert "github" in self.frontmatter.myst_data
        assert "open_access" in self.frontmatter.myst_data
        ##
        assert "isbn" not in self.frontmatter.myst_data
        assert "isbn" in self.frontmatter.all_data

    def test_frontmatter_dump_yamlstr(self):
        print("self.md", self.md)
        assert self.md.startswith("---\n")
        assert "chapters\n---\n\n\n\n# Book Title\n" in self.md  # end
        assert "\ntitle: Just a book\n" in self.md
        assert (
            "Luxembourg Centre for Contemporary and Digital History (C²DH)" in self.md
        )
        assert (
            "authors:\n"
            "- name: Pawel Kaminski\n"
            "  affiliations: University of Luxembourg\n"
            "- name: Elisabeth Guerard\n"
            "  affiliations: Luxembourg Centre for Contemporary and Digital History (C²DH)\n"
        ) in self.md
        assert "\nkeywords:\n- test\n- e2e\n" in self.md
        assert "\nlicense: CC-BY-NC-ND-4.0\n" in self.md
        assert (
            "\ngithub: https://github.com/monograph-prototypes/split-to-multiple-chapters\n"
            in self.md
        )
        assert "isbn" not in self.md

    @pytest.mark.parametrize(
        "i, bookmark, slug, prefix, fn, jb_key, docx_key",
        [
            (
                0,
                "h1_index",
                "h1-index",
                "I",
                None,
                KeyPath(f"/tmp/efs/{JB_DIR}/{SLUG}/h1-index.md"),
                KeyPath(f"/tmp/efs/{PAPER_DIR}/{SLUG}/h1-index.docx"),
            ),  # slug is auto-generated
            (
                1,
                "h1_infile",
                "in-file",
                "1",
                None,
                KeyPath(f"/tmp/efs/{JB_DIR}/{SLUG}/in-file.md"),
                KeyPath(f"/tmp/efs/{PAPER_DIR}/{SLUG}/in-file.docx"),
            ),
            (
                2,
                "h1_isunicode",
                "is-unicode-handled-well",
                "2",
                "isunicode_with_custom_file_name",
                KeyPath(f"/tmp/efs/{JB_DIR}/{SLUG}/isunicode_with_custom_file_name.md"),
                KeyPath(
                    f"/tmp/efs/{PAPER_DIR}/{SLUG}/isunicode_with_custom_file_name.docx"
                ),
            ),
        ],
    )
    def test_generate_chapters_from_toc(
        self, i, bookmark, slug, prefix, fn, jb_key, docx_key
    ):
        """
        Test ChepterService.generate_chapters_from_toc
        """
        assert len(self.frontmatter.dgtmon_data["_toc"]) == 3
        chapter = self.frontmatter.dgtmon_data["_toc"][i]
        assert isinstance(chapter, Chapter)
        assert chapter.bookmark == bookmark
        assert chapter.chapter_slug == slug
        assert chapter.book_slug == SLUG
        assert chapter.prefix == prefix
        assert chapter.fn == fn
        assert isinstance(chapter.fm_key, KeyPath)
        assert isinstance(chapter.jb_key, KeyPath)
        assert isinstance(chapter.docx_key, KeyPath)
        assert chapter.fm_key == self.key
        assert chapter.fm_key.name == "frontmatter_extraction.docx"
        assert chapter.jb_key == jb_key
        assert chapter.docx_key == docx_key


class TestFrontmatterPreparationAndGenChapterFromKey:
    @classmethod
    def setup_class(cls):
        fp = KeyPath("tests") / "_fixtures" / SLUG / "index.docx"
        cls.key = KeyPath("/tmp/efs") / WORK_DIR / SLUG / fp.name
        html_str = _convert_to_html(fp)
        html_soup = convert_to_bs(html_str)
        cls.html_soup, cls.frontmatter = prepare_frontmatter(html_soup, cls.key)
        # dstate = DocumentState(cls.key)
        # cls.md = convert_to_md(cls.html_soup, dstate)

    def test_frontmatter_is_empty(self):
        # there is no frontmatter in this file
        assert len(self.frontmatter.all_data) == 0
        assert self.frontmatter.should_be_splitted() == False

    def test_fm_curr_file_points_to_work_dir(self):
        assert self.frontmatter.current_file == self.key

    @pytest.mark.parametrize(
        "key, book_slug, chapter_slug, prefix, fn, fm_key, jb_key, docx_key",
        [
            (
                KeyPath(f"{SLUG}/01_chapter_slug.docx"),
                SLUG,
                "01_chapter_slug",
                "1",
                "01_chapter_slug",
                KeyPath(f"/tmp/efs/{WORK_DIR}/{SLUG}/01_chapter_slug.docx"),
                KeyPath(f"/tmp/efs/{JB_DIR}/{SLUG}/01_chapter_slug.md"),
                KeyPath(f"/tmp/efs/{PAPER_DIR}/{SLUG}/01_chapter_slug.docx"),
            )
        ],
    )
    def test_generate_chapter_from_key(
        self, key, book_slug, chapter_slug, prefix, fn, fm_key, jb_key, docx_key
    ):
        """
        Test ChepterService.generate_chapter_from_key
        """
        chapter = ChapterService.generate_chapter_from_key(key)

        assert isinstance(chapter, Chapter)
        assert chapter.bookmark == ""
        assert chapter.book_slug == book_slug
        assert chapter.chapter_slug == chapter_slug
        assert chapter.prefix == prefix
        assert chapter.fn == fn
        assert chapter.fm_key == fm_key
        assert chapter.jb_key == jb_key
        assert chapter.docx_key == docx_key
        assert isinstance(chapter.fm_key, KeyPath)
        assert isinstance(chapter.jb_key, KeyPath)
        assert isinstance(chapter.docx_key, KeyPath)
