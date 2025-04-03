import bs4
import pathlib

from src.preparer.refs import (
    is_caption,
    is_header,
    is_footnote,
    is_reference,
    prepare_ref_targets_in_headers,
    prepare_ref_targets_in_captions,
    prepare_ref_targets_in_footnotes,
    prepare_references,
)
from src.preparer.main import _convert_to_html
from src.preparer.metadata import DocumentMetadata
from src.preparer.keys import KeyPath
from src.preparer.substitutions_prep import count_targets_for_substitutions
from src.preparer.conditional_rendering import is_paper_only, remove_paper_only


class TestRefDatapointsCreated:
    fp_a = KeyPath(pathlib.Path("tests") / "_fixtures" / "a_book" / "01_a.docx")
    fp_b = KeyPath(pathlib.Path("tests") / "_fixtures" / "a_book" / "02_b.docx")

    @classmethod
    def setup_class(cls):
        cls.multidocs_meta: dict[str, DocumentMetadata] = {}
        cls.soup_a, cls.meta_a = cls._prepare_docx_for_ref_handing(cls.fp_a)
        cls.soup_b, cls.meta_b = cls._prepare_docx_for_ref_handing(cls.fp_b)
        cls.multidocs_meta[cls.fp_a.stem] = cls.meta_a
        cls.multidocs_meta[cls.fp_b.stem] = cls.meta_b

    @classmethod
    def _prepare_docx_for_ref_handing(
        cls, fp: KeyPath
    ) -> tuple[bs4.BeautifulSoup, DocumentMetadata]:
        html_str = _convert_to_html(fp)
        html_soup = bs4.BeautifulSoup(html_str, "html.parser")
        metadata = DocumentMetadata(fp)
        headers, captions, footnotes, references = [], [], [], []
        classifiers = [
            (is_header, headers),
            (is_caption, captions),
            (is_footnote, footnotes),
            (is_reference, references),
        ]
        for node in html_soup.descendants:
            for check_if_meets_criteria, container in classifiers:
                if isinstance(node, bs4.element.Tag) and check_if_meets_criteria(node):
                    container.append(node)
        html_soup = prepare_ref_targets_in_headers(html_soup, metadata, headers)
        html_soup = prepare_ref_targets_in_captions(html_soup, metadata, captions)
        html_soup = prepare_ref_targets_in_footnotes(html_soup, metadata, footnotes)
        html_soup = prepare_references(html_soup, metadata, references)
        return html_soup, metadata

    def test_target_as_a_user_placed_bookmark(self):
        # target = self.multidocs_meta[self.fp_a.stem].get_target("f-01-a-heading")
        target = self.multidocs_meta[self.fp_a.stem].get_target("f-01-a-a-heading")
        assert target
        assert target.text == "Heading"
        assert target.is_digital == True
        assert target.is_paper == True
        assert target.item_type == "heading"
        assert target.prefix == ""
        assert target.prev_item_num == None

    def test_target_simple(self):
        target = self.multidocs_meta[self.fp_a.stem].get_target("f-01-a-ref177042490")
        assert target
        assert target.text == "1"
        assert target.is_digital == True
        assert target.is_paper == True
        assert target.item_type == "figure"
        assert target.prefix == ""
        assert target.prev_item_num == 1

    def test_two_targets_to_the_same_object(self):
        """The caption has two bookmarks assigned to it.
        This should be taken into account when updating the table numbering."""
        target1 = self.multidocs_meta[self.fp_a.stem].get_target("f-01-a-ref177044323")
        assert target1
        assert target1.text == "1"
        assert target1.is_digital == True
        assert target1.is_paper == True
        assert target1.item_type == "table"
        assert target1.prefix == ""
        assert target1.prev_item_num == 1

        target2 = self.multidocs_meta[self.fp_a.stem].get_target("f-01-a-ref177044319")
        assert target2
        assert target1.text == target2.text
        assert target1.is_digital == target2.is_digital
        assert target1.is_paper == target2.is_paper
        assert target1.item_type == target2.item_type
        assert target1.prefix == target2.prefix
        assert target1.prev_item_num == target2.prev_item_num

    def test_target_complex(self):
        target = self.multidocs_meta[self.fp_a.stem].get("targets", "I.A", "text")
        assert target
        assert target.text == "I.A"
        assert target.is_digital == True
        assert target.is_paper == True
        assert target.item_type == "equation"
        assert target.prefix == "I."
        assert target.prev_item_num == 1

    def test_caption_to_external(self):
        ref = next(
            ref
            for ref in self.multidocs_meta[self.fp_a.stem].refs
            if ref.prev_string == "link in caption to an external source"
        )
        assert ref.text == ref.prev_string
        assert (
            ref.href == "https://web.archive.org/web/20250101004557/http:/example.com/"
        )
        assert (
            ref.prev_href
            == "https://web.archive.org/web/20250101004557/http:/example.com/"
        )

    def test_caption_to_internal(self):
        ref = next(
            ref
            for ref in self.multidocs_meta[self.fp_a.stem].refs
            if ref.prev_string == "link in caption to a table in chapter 2"
        )
        assert ref.text != ref.prev_string
        assert ref.text.startswith(r"link in caption to a table in chapter {{ ")
        assert ref.href == "./02_b.md#f-02-b-tblsimpletable"
        assert ref.prev_href == "02_b.docx#tblSimpleTable"

    def test_infile_link_to_heading(self):
        ref = next(
            ref
            for ref in self.multidocs_meta[self.fp_a.stem].refs
            if ref.text == "direct heading"
        )
        assert ref.text == ref.prev_string
        assert ref.href == "#f-01-a-heading"
        assert ref.prev_href == "#_Heading"

    def test_infile_link_to_bookmark(self):
        ref = next(
            ref
            for ref in self.multidocs_meta[self.fp_a.stem].refs
            if ref.text == "bookmark heading"
        )
        assert ref.text == ref.prev_string
        assert ref.href == "#f-01-a-a-heading"
        assert ref.prev_href == "#a_heading"

    def test_infile_crossref_to_figure(self):
        ref = next(
            ref
            for ref in self.multidocs_meta[self.fp_a.stem].refs
            if ref.prev_string == "Figure 1"
        )
        assert ref.text == r"Figure {{ f01aref177042490 }}"
        assert ref.href == "#f-01-a-ref177042490"
        assert ref.prev_href == "#_Ref177042490"

    def test_infile_crossref_to_table(self):
        ref = next(
            ref
            for ref in self.multidocs_meta[self.fp_a.stem].refs
            if ref.prev_string == "Table 1"
        )
        assert ref.text == r"Table {{ f01aref177044323 }}"
        assert ref.href == "#f-01-a-ref177044323"
        assert ref.prev_href == "#_Ref177044323"

    def test_f2f_link_to_heading(self):
        ref = next(
            ref
            for ref in self.multidocs_meta[self.fp_a.stem].refs
            if ref.prev_string == "Heading 1"
        )
        assert ref.text == r"Heading {{ 02bdocxf02bh2subheading }}"
        assert ref.href == "./02_b.md#f-02-b-h2subheading"
        assert ref.prev_href == "02_b.docx#h2Subheading"

    def test_f2f_link_to_figure(self):
        ref = next(
            ref
            for ref in self.multidocs_meta[self.fp_a.stem].refs
            if ref.prev_string == "Figure"
        )
        assert ref.text == "Figure"
        assert ref.href == "./02_b.md#f-02-b-figredsquare"
        assert ref.prev_href == "02_b.docx#figRedSquare"

    def test_f2f_link_to_table(self):
        ref = next(
            ref
            for ref in self.multidocs_meta[self.fp_a.stem].refs
            if ref.prev_string == "Table"
        )
        assert ref.text == "Table"
        assert ref.href == "./02_b.md#f-02-b-tblsimpletable"
        assert ref.prev_href == "02_b.docx#tblSimpleTable"

    def test_footnote_start(self):
        ref = next(
            ref
            for ref in self.multidocs_meta[self.fp_a.stem].refs
            if ref.text == "Footnote link to an external website"
        )
        assert (
            ref.href == "https://web.archive.org/web/20250101004557/http:/example.com/"
        )
        assert ref.prev_string == "Footnote link to an external website"
        assert (
            ref.prev_href
            == "https://web.archive.org/web/20250101004557/http:/example.com/"
        )

    def test_footnote_mid(self):
        ref = next(
            ref
            for ref in self.multidocs_meta[self.fp_a.stem].refs
            if ref.text == "footnote link"
        )
        assert (
            ref.href == "https://web.archive.org/web/20250101004557/http:/example.com/"
        )
        assert ref.prev_string == "footnote link"
        assert (
            ref.prev_href
            == "https://web.archive.org/web/20250101004557/http:/example.com/"
        )

    def test_footnote_end(self):
        ref = next(
            ref
            for ref in self.multidocs_meta[self.fp_a.stem].refs
            if ref.text == "end of the footnote."
        )
        assert (
            ref.href == "https://web.archive.org/web/20250101004557/http:/example.com/"
        )
        assert ref.prev_string == "end of the footnote."
        assert (
            ref.prev_href
            == "https://web.archive.org/web/20250101004557/http:/example.com/"
        )

    def test_substitution_fig1(self):
        subst = next(
            subst
            for subst in self.multidocs_meta[self.fp_a.stem].substitutions
            if subst.pk == "f01aref177042490"
        )
        assert subst.was == "1"
        assert subst.item_type == "fig"

    def test_substitution_tbl1(self):
        subst = next(
            subst
            for subst in self.multidocs_meta[self.fp_a.stem].substitutions
            if subst.pk == "f01aref177044323"
        )
        assert subst.was == "1"
        assert subst.item_type == "tbl"

    # def test_substitution_figRedSquare_bookmark_from_ref(self):
    #     subst = next(
    #         subst
    #         for subst in self.multidocs_meta[self.fp_a.stem].substitutions
    #         if subst.pk == "02bdocxf02bfigredsquare"
    #     )
    #     assert subst.was == ""
    #     assert subst.item_type == "fig"


class TestSubstitutions:
    fp_a = KeyPath(pathlib.Path("tests") / "_fixtures" / "a_book" / "01_a.docx")
    fp_b = KeyPath(pathlib.Path("tests") / "_fixtures" / "a_book" / "02_b.docx")
    # fp = KeyPath(
    #     pathlib.Path("tests") / "_fixtures" / "a_book" / "05_conditional_rendering.docx"
    # )

    @classmethod
    def setup_class(cls):
        cls.multidocs_meta: dict[str, DocumentMetadata] = {}
        cls.soup_a, cls.meta_a = cls._prepare_docx_for_ref_handing(cls.fp_a)
        cls.soup_b, cls.meta_b = cls._prepare_docx_for_ref_handing(cls.fp_b)
        cls.multidocs_meta[cls.fp_a.stem] = cls.meta_a
        cls.multidocs_meta[cls.fp_b.stem] = cls.meta_b

    @classmethod
    def _prepare_docx_for_ref_handing(
        cls, fp: KeyPath
    ) -> tuple[bs4.BeautifulSoup, DocumentMetadata]:
        html_str = _convert_to_html(fp)
        html_soup = bs4.BeautifulSoup(html_str, "html.parser")
        metadata = DocumentMetadata(fp)
        headers, captions, footnotes, references, paper_only = [], [], [], [], []
        classifiers = [
            (is_header, headers),
            (is_caption, captions),
            (is_footnote, footnotes),
            (is_reference, references),
            (is_paper_only, paper_only),
        ]
        for node in html_soup.descendants:
            for check_if_meets_criteria, container in classifiers:
                if isinstance(node, bs4.element.Tag) and check_if_meets_criteria(node):
                    container.append(node)
        html_soup = prepare_ref_targets_in_headers(html_soup, metadata, headers)
        html_soup = prepare_ref_targets_in_captions(html_soup, metadata, captions)
        html_soup = prepare_ref_targets_in_footnotes(html_soup, metadata, footnotes)
        html_soup = prepare_references(html_soup, metadata, references)
        # html_soup = prepare_metadata_tables(html_soup, metadata, tables)
        html_soup = remove_paper_only(html_soup, metadata, paper_only)
        # html_soup = remove_empty_tables(html_soup, metadata, tables)
        # html_soup = prepare_alt_texts(html_soup, metadata, images_with_alttxt)
        html_soup = count_targets_for_substitutions(html_soup, metadata)
        return html_soup, metadata

    def test_testing(self):
        assert False


class TestDatapointsCreatedAndMarkedForDigitalAndForPaper:
    fp = KeyPath(
        pathlib.Path("tests") / "_fixtures" / "a_book" / "05_conditional_rendering.docx"
    )

    @classmethod
    def setup_class(cls):
        cls.multidocs_meta: dict[str, DocumentMetadata] = {}
        cls.soup, cls.metadata = cls._prepare_docx_for_ref_handing(cls.fp)
        # cls.multidocs_meta[cls.fp.stem] = cls.meta

    @classmethod
    def _prepare_docx_for_ref_handing(
        cls, fp: KeyPath
    ) -> tuple[bs4.BeautifulSoup, DocumentMetadata]:
        html_str = _convert_to_html(fp)
        html_soup = bs4.BeautifulSoup(html_str, "html.parser")
        metadata = DocumentMetadata(fp)
        headers, captions, footnotes, references = [], [], [], []
        classifiers = [
            (is_header, headers),
            (is_caption, captions),
            (is_footnote, footnotes),
            (is_reference, references),
        ]
        for node in html_soup.descendants:
            for check_if_meets_criteria, container in classifiers:
                if isinstance(node, bs4.element.Tag) and check_if_meets_criteria(node):
                    container.append(node)
        html_soup = prepare_ref_targets_in_headers(html_soup, metadata, headers)
        html_soup = prepare_ref_targets_in_captions(html_soup, metadata, captions)
        html_soup = prepare_ref_targets_in_footnotes(html_soup, metadata, footnotes)
        html_soup = prepare_references(html_soup, metadata, references)
        return html_soup, metadata

    def test_target_for_digital(self):
        target = self.metadata.get(
            "targets", "f-05-conditional-rendering-figfordigital"
        )
        assert target
        assert target.text == "1"
        assert target.is_digital == True
        assert target.is_paper == False

    def test_target_for_paper(self):
        target = self.metadata.get("targets", "f-05-conditional-rendering-figforpaper")
        assert target
        assert target.text == "2"
        assert target.is_digital == False
        assert target.is_paper == True

    def test_target_for_digital_and_for_paper(self):
        target = self.metadata.get(
            "targets", "f-05-conditional-rendering-figfordigitalandpaper"
        )
        assert target
        assert target.text == "3"
        assert target.is_digital == True
        assert target.is_paper == True

    def test_substitution_for_digital(self):
        subs = self.metadata.get("substitutions", "f05conditionalrenderingref193102947")
        assert subs
        assert subs.was == "1"
        assert subs.is_digital == True
        assert subs.is_paper == False
        assert subs.file_count == 5

    def test_substitution_for_paper(self):
        subs = self.metadata.get("substitutions", "f05conditionalrenderingref193102988")
        assert subs
        assert subs.was == "2"
        assert subs.is_digital == False
        assert subs.is_paper == True
        assert subs.file_count == 5

    def test_substitution_for_digital_and_for_paper(self):
        subs = self.metadata.get("substitutions", "f05conditionalrenderingref193103002")
        assert subs
        assert subs.was == "3"
        assert subs.is_digital == True
        assert subs.is_paper == True
        assert subs.file_count == 5

    def test_substitution_for_refs(self):
        assert len(self.metadata.substitutions) == 7  # 4 targets + 3 refs
        subs = self.metadata.get(
            "substitutions", "f05conditionalrenderingfigfordigital"
        )
        assert subs
        assert subs.was == "1"
        assert subs.is_digital == None
        assert subs.is_paper == None
        subs = self.metadata.get("substitutions", "f05conditionalrenderingfigforpaper")
        assert subs
        assert subs.was == "2"
        assert subs.is_digital == None
        assert subs.is_paper == None
        subs = self.metadata.get(
            "substitutions", "f05conditionalrenderingfigfordigitalandpaper"
        )
        assert subs
        assert subs.was == "3"
        assert subs.is_digital == None
        assert subs.is_paper == None
        assert subs.file_count == 5
