import bs4
import pathlib

from src.preparer.constants import AUTONUMBER_PLACEHOLDER
from src.preparer.main import _convert_to_html, prepare_docx
from src.preparer.metadata import DocumentMetadata, SubstitutionDatapoint
from src.preparer.keys import KeyPath
from src.preparer.state import DocumentState


class TestRefDatapointsCreated:
    fp_i = KeyPath(pathlib.Path("tests") / "_fixtures" / "a_book" / "00_index.docx")
    fp_a = KeyPath(pathlib.Path("tests") / "_fixtures" / "a_book" / "01_a.docx")
    fp_b = KeyPath(pathlib.Path("tests") / "_fixtures" / "a_book" / "02_b.docx")
    fp_cr = KeyPath(
        pathlib.Path("tests") / "_fixtures" / "a_book" / "05_conditional_rendering.docx"
    )

    @classmethod
    def setup_class(cls):
        cls.book_metadata: dict[str, DocumentMetadata] = {}
        # in preparer
        cls.soup_i, cls.meta_i = cls._prepare_docx_for_ref_handing(cls.fp_i)
        cls.soup_a, cls.meta_a = cls._prepare_docx_for_ref_handing(cls.fp_a)
        cls.soup_b, cls.meta_b = cls._prepare_docx_for_ref_handing(cls.fp_b)
        cls.soup_cr, cls.meta_cr = cls._prepare_docx_for_ref_handing(cls.fp_cr)
        cls.book_metadata[cls.fp_i.stem] = cls.meta_i
        cls.book_metadata[cls.fp_a.stem] = cls.meta_a
        cls.book_metadata[cls.fp_b.stem] = cls.meta_b
        cls.book_metadata[cls.fp_cr.stem] = cls.meta_cr

    @classmethod
    def _prepare_docx_for_ref_handing(
        cls, fp: KeyPath
    ) -> tuple[bs4.BeautifulSoup, DocumentMetadata]:
        cls.dstate = DocumentState(fp)
        metadata = DocumentMetadata(fp)
        html_str = _convert_to_html(fp)
        html_soup, metadata, _ = prepare_docx(html_str, metadata, cls.dstate)
        return html_soup, metadata

    def test_target_as_a_user_placed_bookmark(self):
        # target = self.book_metadata[self.fp_a.stem].get_target("f-01-a-heading")
        target = self.book_metadata[self.fp_a.stem].get_target("f-01-a-a-heading")
        assert target
        assert target.text == "Heading"
        assert target.is_digital == True
        assert target.is_paper == True
        assert target.filename == "01_a.docx"
        assert target.fragment == "a_heading"
        assert target.item_type == "heading"
        assert target.prefix == ""
        assert target.prev_item_num == None

    def test_target_simple(self):
        target = self.book_metadata[self.fp_a.stem].get_target("f-01-a-ref177042490")
        assert target
        assert target.text == "1"
        assert target.is_digital == True
        assert target.is_paper == True
        assert target.filename == "01_a.docx"
        assert target.fragment == "_Ref177042490"
        assert target.item_type == "figure"
        assert target.prefix == ""
        assert target.prev_item_num == 1

    def test_two_targets_to_the_same_object(self):
        """The caption has two bookmarks assigned to it.
        This should be taken into account when updating the table numbering."""
        target1 = self.book_metadata[self.fp_a.stem].get_target("f-01-a-ref177044323")
        assert target1
        assert target1.text == "1"
        assert target1.is_digital == True
        assert target1.is_paper == True
        assert target1.filename == "01_a.docx"
        assert target1.fragment == "_Ref177044323"
        assert target1.item_type == "table"
        assert target1.prefix == ""
        assert target1.prev_item_num == 1

        target2 = self.book_metadata[self.fp_a.stem].get_target("f-01-a-ref177044319")
        assert target2
        assert target1.text == target2.text
        assert target1.is_digital == target2.is_digital
        assert target1.is_paper == target2.is_paper
        assert target1.filename == target2.filename
        assert target1.fragment != target2.fragment
        assert target2.fragment == "_Ref177044319"
        assert target1.item_type == target2.item_type
        assert target1.prefix == target2.prefix
        assert target1.prev_item_num == target2.prev_item_num

    def test_target_complex(self):
        target = self.book_metadata[self.fp_a.stem].get("targets", "I.A", "text")
        assert target
        assert target.text == "I.A"
        assert target.is_digital == True
        assert target.is_paper == True
        assert target.filename == "01_a.docx"
        assert target.fragment == "equationWithComplexNumbering"
        assert target.item_type == "equation"
        assert target.prefix == "I."
        assert target.prev_item_num == 1

    def test_caption_to_external(self):
        ref = next(
            ref
            for ref in self.book_metadata[self.fp_a.stem].refs
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
            for ref in self.book_metadata[self.fp_a.stem].refs
            if ref.prev_string == "link in caption to a table in chapter 2"
        )
        assert ref.text != ref.prev_string
        assert ref.text.startswith(r"link in caption to a table in chapter {{ ")
        assert ref.href == "./02_b.md#f-02-b-tblsimpletable"
        assert ref.prev_href == "02_b.docx#tblSimpleTable"

    def test_infile_link_to_heading(self):
        ref = next(
            ref
            for ref in self.book_metadata[self.fp_a.stem].refs
            if ref.text == "direct heading"
        )
        assert ref.text == ref.prev_string
        assert ref.href == "#f-01-a-heading"
        assert ref.prev_href == "#_Heading"

    def test_infile_link_to_bookmark(self):
        ref = next(
            ref
            for ref in self.book_metadata[self.fp_a.stem].refs
            if ref.text == "bookmark heading"
        )
        assert ref.text == ref.prev_string
        assert ref.href == "#f-01-a-a-heading"
        assert ref.prev_href == "#a_heading"

    def test_infile_crossref_to_figure(self):
        ref = next(
            ref
            for ref in self.book_metadata[self.fp_a.stem].refs
            if ref.prev_string == "Figure 1"
        )
        assert ref.text == r"Figure {{ f01aref177042490 }}"
        assert ref.href == "#f-01-a-ref177042490"
        assert ref.prev_href == "#_Ref177042490"

    def test_infile_crossref_to_table(self):
        ref = next(
            ref
            for ref in self.book_metadata[self.fp_a.stem].refs
            if ref.prev_string == "Table 1"
        )
        assert ref.text == r"Table {{ f01aref177044323 }}"
        assert ref.href == "#f-01-a-ref177044323"
        assert ref.prev_href == "#_Ref177044323"

    def test_f2f_link_to_heading(self):
        ref = next(
            ref
            for ref in self.book_metadata[self.fp_a.stem].refs
            if ref.prev_string == "Heading"
        )
        # # I don't understand why heading was numbered "1".
        # I did that to test substitution in refs, but why heading is 1?
        # Makes more sense with table and figure.
        # assert ref.text == r"Heading {{ 02bdocxf02bh2subheading }}"
        assert ref.text == r"Heading"
        assert ref.href == "./02_b.md#f-02-b-h2subheading"
        assert ref.prev_href == "02_b.docx#h2Subheading"

    def test_f2f_link_to_figure(self):
        ref = next(
            ref
            for ref in self.book_metadata[self.fp_a.stem].refs
            if ref.prev_string == f"Figure {AUTONUMBER_PLACEHOLDER}"
        )
        assert ref.text == r"Figure {{ 02bdocxf02bfigredsquare }}"
        assert ref.href == "./02_b.md#f-02-b-figredsquare"
        assert ref.prev_href == "02_b.docx#figRedSquare"

    def test_f2f_fig_substitution(self):
        subst = next(
            subst
            for subst in self.book_metadata[self.fp_a.stem].substitutions
            if subst.pk == "02bdocxf02bfigredsquare"
        )
        assert subst.was == AUTONUMBER_PLACEHOLDER
        assert subst.item_type == "ref"
        assert subst.file_count == 2
        assert subst.prefix == ""
        # NOTE: this is updated on the builder (once we see all the files)
        # assert subst.prev_item_num == 1
        # assert subst.new_value() == "2.1"

    def test_f2f_link_to_table(self):
        ref = next(
            ref
            for ref in self.book_metadata[self.fp_a.stem].refs
            if ref.prev_string == f"Table {AUTONUMBER_PLACEHOLDER}"
        )
        assert ref.text == r"Table {{ 02bdocxf02btblsimpletable }}"
        assert ref.href == "./02_b.md#f-02-b-tblsimpletable"
        assert ref.prev_href == "02_b.docx#tblSimpleTable"

    def test_f2f_tbl_substitution__two_refs(self):
        # NOTE: there are 2 separate references to the same table in the document.
        # The first one is in the caption, the second one is in the text.
        # But there was only one substitution created for them.

        # Then again, maybe it's not a problem
        # as long as we just replace placeholder with the same new_value()
        subst = next(
            subst
            for subst in self.book_metadata[self.fp_a.stem].substitutions
            if subst.pk == "02bdocxf02btblsimpletable"
        )
        assert subst.item_type == "ref"
        assert subst.file_count == 2
        # NOTE: this is updated on the builder (once we see all the files)
        # assert subst.prefix == ""
        # assert subst.prev_item_num == 1
        # assert subst.new_value() == "2.1"

    def test_footnote_start(self):
        ref = next(
            ref
            for ref in self.book_metadata[self.fp_a.stem].refs
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
            for ref in self.book_metadata[self.fp_a.stem].refs
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
            for ref in self.book_metadata[self.fp_a.stem].refs
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
            for subst in self.book_metadata[self.fp_a.stem].substitutions
            if subst.pk == "f01aref177042490"
        )
        assert subst.was == "1"
        assert subst.item_type == "figure"
        assert subst.file_count == 1
        assert subst.prefix == ""
        assert subst.prev_item_num == 1
        assert subst.new_value() == "1.1"

    def test_substitution_in_ref__crossref_fig1(self):
        ref = self.soup_a.find("a", href="#f-01-a-ref177042490")
        assert ref.text == r"Figure {{ f01aref177042490 }}"

    def test_substitution_tbl1(self):
        subst = next(
            subst
            for subst in self.book_metadata[self.fp_a.stem].substitutions
            if subst.pk == "f01aref177044323"
        )
        assert subst.was == "1"
        assert subst.item_type == "table"
        assert subst.file_count == 1
        assert subst.prefix == ""
        assert subst.prev_item_num == 1
        assert subst.new_value() == "1.1"

    def test_substitution_in_ref__crossref_tbl1(self):
        ref = self.soup_a.find("a", href="#f-01-a-ref177044323")
        assert ref.text == r"Table {{ f01aref177044323 }}"

    def test_substitution_tbl1(self):
        subst = next(
            subst
            for subst in self.book_metadata[self.fp_a.stem].substitutions
            if subst.pk == "f01aequationwithcomplexnumbering"
        )
        assert subst.was == "I.A"
        assert subst.item_type == "equation"
        assert subst.file_count == 1
        assert subst.prefix == "I."
        assert subst.prev_item_num == 1
        assert subst.new_value() == "1.I.1"

    def test_substitution_in_ref__infile_link(self):
        ref = self.soup_a.find("a", href="#f-01-a-equationwithcomplexnumbering")
        assert ref.text == r"see equation {{ f01aequationwithcomplexnumbering }}"

    def test_substitution_conditional_rendering_digital(self):
        # for ref in self.book_metadata[self.fp_a.stem].refs:
        #     print(ref)
        #     print("-" * 50)
        # print("=" * 75)
        # for subst in self.book_metadata[self.fp_a.stem].substitutions:
        #     print(subst)
        #     print("-" * 50)
        #     # print(subst.pk)
        subst = next(
            subst
            for subst in self.book_metadata[self.fp_a.stem].substitutions
            if subst.pk
            == "05conditionalrenderingdocxf05conditionalrenderingfigfordigital"
        )
        assert subst.was == AUTONUMBER_PLACEHOLDER
        assert subst.item_type == "ref"
        assert subst.file_count == 5
        assert subst.prefix == ""
        # assert subst.prev_item_num == None
        # assert subst.new_value() == ""

    def test_substitution_in_ref__conditional_rendering_digital(self):
        ref = self.soup_a.find(
            "a",
            href="./05_conditional_rendering.md#f-05-conditional-rendering-figfordigital",
        )
        assert (
            ref.text
            == r"link to fig {{ 05conditionalrenderingdocxf05conditionalrenderingfigfordigital }} (digital only)"
        )

    def test_substitution_conditional_rendering_paper(self):
        subst = next(
            subst
            for subst in self.book_metadata[self.fp_a.stem].substitutions
            if subst.pk
            == "05conditionalrenderingdocxf05conditionalrenderingfigforpaper"
        )
        assert subst.was == AUTONUMBER_PLACEHOLDER
        assert subst.item_type == "ref"
        assert subst.file_count == 5
        assert subst.prefix == ""
        # assert subst.prev_item_num == None
        # assert subst.new_value() == ""

    def test_substitution_in_ref__conditional_rendering_paper(self):
        ref = self.soup_a.find(
            "a",
            href="./05_conditional_rendering.md#f-05-conditional-rendering-figforpaper",
        )
        assert (
            ref.text
            == r"link to fig {{ 05conditionalrenderingdocxf05conditionalrenderingfigforpaper }} (paper only)"
        )

    def test_substitution_conditional_rendering_digital_and_paper(self):
        subst = next(
            subst
            for subst in self.book_metadata[self.fp_a.stem].substitutions
            if subst.pk
            == "05conditionalrenderingdocxf05conditionalrenderingfigfordigitalandpaper"
        )
        assert subst.was == AUTONUMBER_PLACEHOLDER
        assert subst.item_type == "ref"
        assert subst.file_count == 5
        assert subst.prefix == ""
        # assert subst.prev_item_num == None
        # assert subst.new_value() == ""

    def test_substitution_in_ref__conditional_rendering_digital_and_paper(self):
        ref = self.soup_a.find(
            "a",
            href="./05_conditional_rendering.md#f-05-conditional-rendering-figfordigitalandpaper",
        )
        assert (
            ref.text
            == r"link to fig {{ 05conditionalrenderingdocxf05conditionalrenderingfigfordigitalandpaper }} (digital and paper)"
        )


class TestDatapointsCreatedAndMarkedForDigitalAndForPaper:
    fp = KeyPath(
        pathlib.Path("tests") / "_fixtures" / "a_book" / "05_conditional_rendering.docx"
    )

    @classmethod
    def setup_class(cls):
        cls.book_metadata: dict[str, DocumentMetadata] = {}
        cls.soup, cls.metadata = cls._prepare_docx_for_ref_handing(cls.fp)
        # cls.book_metadata[cls.fp.stem] = cls.meta

    @classmethod
    def _prepare_docx_for_ref_handing(
        cls, fp: KeyPath
    ) -> tuple[bs4.BeautifulSoup, DocumentMetadata]:
        cls.dstate = DocumentState(fp)
        metadata = DocumentMetadata(fp)
        html_str = _convert_to_html(fp)
        html_soup, metadata, _ = prepare_docx(html_str, metadata, cls.dstate)
        return html_soup, metadata

    def test_target_for_digital(self):
        target = self.metadata.get(
            "targets", "f-05-conditional-rendering-figfordigital"
        )
        assert target
        assert target.text == "1"
        assert target.is_digital == True
        assert target.is_paper == False
        assert target.filename == self.fp.name
        assert target.fragment == "figForDigital"

    def test_target_for_paper(self):
        target = self.metadata.get("targets", "f-05-conditional-rendering-figforpaper")
        assert target
        assert target.text == "2"
        assert target.is_digital == False
        assert target.is_paper == True
        assert target.filename == self.fp.name
        assert target.fragment == "figForPaper"

    def test_target_for_digital_and_for_paper(self):
        target = self.metadata.get(
            "targets", "f-05-conditional-rendering-figfordigitalandpaper"
        )
        assert target
        assert target.text == "3"
        assert target.is_digital == True
        assert target.is_paper == True
        assert target.filename == self.fp.name
        assert target.fragment == "figForDigitalAndPaper"

    def test_substitution_for_digital(self):
        subs = self.metadata.get("substitutions", "f05conditionalrenderingref193102947")
        assert subs
        assert subs.was == "1"
        assert subs.is_digital == True
        assert subs.is_paper == False
        assert subs.item_type == "figure"
        assert subs.file_count == 5
        assert subs.prefix == ""
        assert subs.prev_item_num == 1
        assert subs.new_item_num == 1
        assert subs.new_value() == "5.1"

    def test_substitution_for_paper(self):
        subs = self.metadata.get("substitutions", "f05conditionalrenderingref193102988")
        assert subs
        assert subs.was == "2"
        assert subs.is_digital == False
        assert subs.is_paper == True
        assert subs.item_type == "figure"
        assert subs.file_count == 5
        assert subs.prefix == ""
        assert subs.prev_item_num == 2
        assert subs.new_item_num == None

    def test_substitution_for_digital_and_for_paper(self):
        subs = self.metadata.get("substitutions", "f05conditionalrenderingref193103002")
        assert subs
        assert subs.was == "3"
        assert subs.is_digital == True
        assert subs.is_paper == True
        assert subs.item_type == "figure"
        assert subs.file_count == 5
        assert subs.prefix == ""
        assert subs.prev_item_num == 3
        assert subs.new_item_num == 2
        assert subs.new_value() == "5.2"

    def test_substitution_for_refs(self):
        assert len(self.metadata.substitutions) == 7  # 4 targets + 3 refs
        subs = self.metadata.get(
            "substitutions", "f05conditionalrenderingfigfordigital"
        )
        assert subs
        assert subs.was == "1"
        assert subs.is_digital == None
        assert subs.is_paper == None
        assert subs.item_type == "ref"
        assert subs.file_count == 5
        # NOTE: this is updated on the builder (once we see all the files)
        # assert subs.prev_item_num == None
        # assert subs.prefix == ""
        # assert subs.new_item_num == 1
        # assert subs.new_value() == "5.1"
        subs = self.metadata.get("substitutions", "f05conditionalrenderingfigforpaper")
        assert subs
        assert subs.was == "2"
        assert subs.is_digital == None
        assert subs.is_paper == None
        assert subs.item_type == "ref"
        assert subs.file_count == 5
        # NOTE: this is updated on the builder (once we see all the files)
        # assert subs.prev_item_num == None
        # assert subs.prefix == ""
        # assert subs.new_item_num == None
        # assert subs.new_value() == ""
        subs = self.metadata.get(
            "substitutions", "f05conditionalrenderingfigfordigitalandpaper"
        )
        assert subs
        assert subs.was == "3"
        assert subs.is_digital == None
        assert subs.is_paper == None
        assert subs.item_type == "ref"
        assert subs.file_count == 5
        # NOTE: this is updated on the builder (once we see all the files)
        # assert subs.prefix == ""
        # assert subs.prev_item_num == None
        # assert subs.new_item_num == 2
        # assert subs.new_value() == "5.2"

    def test_substitution_to_json_handling(self):
        subs = self.metadata.get("substitutions", "f05conditionalrenderingref193103002")
        jsonified = subs.to_json()
        assert jsonified["was"] == "3"
        assert jsonified["is_digital"] == True
        assert jsonified["is_paper"] == True
        assert jsonified["item_type"] == "figure"
        assert jsonified["file_count"] == 5
        assert jsonified["prefix"] == ""
        assert jsonified["prev_item_num"] == 3
        assert jsonified["new_item_num"] == 2

    def test_substitution_from_json_handling(self):
        subs = self.metadata.get("substitutions", "f05conditionalrenderingref193103002")
        jsonified = subs.to_json()
        subs = SubstitutionDatapoint.from_json(jsonified)
        assert subs.was == "3"
        assert subs.is_digital == True
        assert subs.is_paper == True
        assert subs.item_type == "figure"
        assert subs.file_count == 5
        assert subs.prefix == ""
        assert subs.prev_item_num == 3
        assert subs.new_item_num == 2
        assert subs.new_value() == "5.2"
        assert subs.new_value("V") == "V.2"
