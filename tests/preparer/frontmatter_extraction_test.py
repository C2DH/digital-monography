import pytest


from src._common.state import DocumentState
from src._common.html2md import convert_to_md
from src._common.models import Chapter
from src._common.keys import KeyPath
from src.preparer.main import _convert_to_html, convert_to_bs
from src.preparer.prep_frontmatter import prepare_frontmatter, FrontmatterBlob


SLUG = "book-content-examples"


class TestFrontmatterPreparation:
    @classmethod
    def setup_class(cls):
        fp = KeyPath("tests") / "_fixtures" / SLUG / "frontmatter_extraction.docx"
        key = KeyPath("/tmp/efs") / SLUG / fp.name
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
        cls.html_soup, cls.frontmatter = prepare_frontmatter(html_soup, key)
        dstate = DocumentState(key)
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
        "i, bookmark, slug, prefix, fn, fp",
        [
            (
                0,
                "h1_index",
                "h1-index",
                "I",
                None,
                KeyPath(f"/tmp/efs/{SLUG}/h1-index.docx"),
            ),  # slug is auto-generated
            (
                1,
                "h1_infile",
                "in-file",
                "1",
                None,
                KeyPath(f"/tmp/efs/{SLUG}/in-file.docx"),
            ),
            (
                2,
                "h1_isunicode",
                "is-unicode-handled-well",
                "2",
                "isunicode_with_custom_file_name",
                KeyPath(f"/tmp/efs/{SLUG}/isunicode_with_custom_file_name.docx"),
            ),
        ],
    )
    def test_chapters_extracted_from_toc(self, i, bookmark, slug, prefix, fn, fp):
        assert len(self.frontmatter.dgtmon_data["_toc"]) == 3
        assert isinstance(self.frontmatter.dgtmon_data["_toc"][i], Chapter)
        assert self.frontmatter.dgtmon_data["_toc"][i].bookmark == bookmark
        assert self.frontmatter.dgtmon_data["_toc"][i].chapter_slug == slug
        assert self.frontmatter.dgtmon_data["_toc"][i].book_slug == SLUG
        assert self.frontmatter.dgtmon_data["_toc"][i].prefix == prefix
        assert self.frontmatter.dgtmon_data["_toc"][i].fn == fn
        assert isinstance(self.frontmatter.dgtmon_data["_toc"][i].fp, KeyPath)
        assert self.frontmatter.dgtmon_data["_toc"][i].fp == fp
