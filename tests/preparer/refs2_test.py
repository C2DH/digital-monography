import bs4
import pathlib

from src.preparer.main import _convert_to_html, prepare_docx
from src._common.constants import AUTONUMBER_PLACEHOLDER
from src._common.metadata import DocumentMetadata
from src._common.keys import KeyPath
from src._common.state import DocumentState
from src._common.models import (
    FileService,
    Ref,
    Substitution,
    SubstitutionService,
    Target,
)


class TestRefDatapointsCreated:
    fp_i = KeyPath(pathlib.Path("tests") / "_fixtures" / "a_book" / "00_index.docx")
    fp_a = KeyPath(pathlib.Path("tests") / "_fixtures" / "a_book" / "01_a.docx")
    fp_b = KeyPath(pathlib.Path("tests") / "_fixtures" / "a_book" / "02_b.docx")
    fp_cr = KeyPath(
        pathlib.Path("tests") / "_fixtures" / "a_book" / "05_conditional_rendering.docx"
    )

    @classmethod
    def setup_class(cls):
        cls.bookstate: dict[str, DocumentState] = {}
        # in preparer
        cls.soup_i, cls.meta_i, cls.dstate_i = cls._prepare_docx_for_ref_handing(
            cls.fp_i
        )
        cls.soup_a, cls.meta_a, cls.dstate_a = cls._prepare_docx_for_ref_handing(
            cls.fp_a
        )
        cls.soup_b, cls.meta_b, cls.dstate_b = cls._prepare_docx_for_ref_handing(
            cls.fp_b
        )
        cls.soup_cr, cls.meta_cr, cls.dstate_cr = cls._prepare_docx_for_ref_handing(
            cls.fp_cr
        )
        cls.bookstate[cls.fp_i.stem] = cls.dstate_i
        cls.bookstate[cls.fp_a.stem] = cls.dstate_a
        cls.bookstate[cls.fp_b.stem] = cls.dstate_b
        cls.bookstate[cls.fp_cr.stem] = cls.dstate_cr

    @classmethod
    def _prepare_docx_for_ref_handing(
        cls, fp: KeyPath
    ) -> tuple[bs4.BeautifulSoup, DocumentMetadata, DocumentState]:
        dstate = DocumentState(fp)
        metadata = DocumentMetadata(fp)
        html_str = _convert_to_html(fp)
        html_soup, metadata, dstate, _ = prepare_docx(html_str, metadata, dstate)
        return html_soup, metadata, dstate

    def test_target_as_a_user_placed_bookmark(self):
        target: Target = self.bookstate[self.fp_a.stem].get(
            "targets", "f-01-a-a-heading"
        )
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
        target: Target = self.bookstate[self.fp_a.stem].get(
            "targets", "f-01-a-ref177042490"
        )
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
        target1: Target = self.bookstate[self.fp_a.stem].get(
            "targets", "f-01-a-ref177044323"
        )
        assert target1
        assert target1.text == "1"
        assert target1.is_digital == True
        assert target1.is_paper == True
        assert target1.filename == "01_a.docx"
        assert target1.fragment == "_Ref177044323"
        assert target1.item_type == "table"
        assert target1.prefix == ""
        assert target1.prev_item_num == 1

        target2: Target = self.bookstate[self.fp_a.stem].get(
            "targets", "f-01-a-ref177044319"
        )
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
        target: Target = self.bookstate[self.fp_a.stem].get("targets", "I.A", "text")
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
        refs: list[Ref] = self.bookstate[self.fp_a.stem]["refs"]
        ref = next(
            ref
            for ref in refs
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
        refs: list[Ref] = self.bookstate[self.fp_a.stem]["refs"]
        ref = next(
            ref
            for ref in refs
            if ref.prev_string == "link in caption to a table in chapter 2"
        )
        assert ref.text != ref.prev_string
        assert ref.text.startswith(r"link in caption to a table in chapter {{ ")
        assert ref.href == "./02_b.md#f-02-b-tblsimpletable"
        assert ref.prev_href == "02_b.docx#tblSimpleTable"

    def test_infile_link_to_heading(self):
        refs: list[Ref] = self.bookstate[self.fp_a.stem]["refs"]
        ref = next(ref for ref in refs if ref.text == "direct heading")
        assert ref.text == ref.prev_string
        assert ref.href == "#f-01-a-heading"
        assert ref.prev_href == "#_Heading"

    def test_infile_link_to_bookmark(self):
        refs: list[Ref] = self.bookstate[self.fp_a.stem]["refs"]
        ref = next(ref for ref in refs if ref.text == "bookmark heading")
        assert ref.text == ref.prev_string
        assert ref.href == "#f-01-a-a-heading"
        assert ref.prev_href == "#a_heading"

    def test_infile_crossref_to_figure(self):
        refs: list[Ref] = self.bookstate[self.fp_a.stem]["refs"]
        ref = next(ref for ref in refs if ref.prev_string == "Figure 1")
        assert ref.text == r"Figure {{ f01aref177042490 }}"
        assert ref.href == "#f-01-a-ref177042490"
        assert ref.prev_href == "#_Ref177042490"

    def test_infile_crossref_to_table(self):
        refs: list[Ref] = self.bookstate[self.fp_a.stem]["refs"]
        ref = next(ref for ref in refs if ref.prev_string == "Table 1")
        assert ref.text == r"Table {{ f01aref177044323 }}"
        assert ref.href == "#f-01-a-ref177044323"
        assert ref.prev_href == "#_Ref177044323"

    def test_f2f_link_to_heading(self):
        refs: list[Ref] = self.bookstate[self.fp_a.stem]["refs"]
        ref = next(ref for ref in refs if ref.prev_string == "Heading")
        # # I don't understand why heading was numbered "1".
        # I did that to test substitution in refs, but why heading is 1?
        # Makes more sense with table and figure.
        # assert ref.text == r"Heading {{ 02bdocxf02bh2subheading }}"
        assert ref.text == r"Heading"
        assert ref.href == "./02_b.md#f-02-b-h2subheading"
        assert ref.prev_href == "02_b.docx#h2Subheading"

    def test_f2f_link_to_figure(self):
        refs: list[Ref] = self.bookstate[self.fp_a.stem]["refs"]
        ref = next(
            ref for ref in refs if ref.prev_string == f"Figure {AUTONUMBER_PLACEHOLDER}"
        )
        assert ref.text == r"Figure {{ 02bdocxf02bfigredsquare }}"
        assert ref.href == "./02_b.md#f-02-b-figredsquare"
        assert ref.prev_href == "02_b.docx#figRedSquare"

    def test_f2f_fig_substitution(self):
        substitutions: list[Substitution] = self.bookstate[self.fp_a.stem][
            "substitutions"
        ]
        subst = next(
            subst for subst in substitutions if subst.pk == "02bdocxf02bfigredsquare"
        )
        assert subst.was == AUTONUMBER_PLACEHOLDER
        assert subst.item_type == "ref"
        assert subst.file_count == 2
        assert subst.prefix == ""
        # NOTE: this is updated on the builder (once we see all the files)
        # assert subst.prev_item_num == 1
        # assert subst.new_value() == "2.1"

    def test_f2f_link_to_table(self):
        refs: list[Ref] = self.bookstate[self.fp_a.stem]["refs"]
        ref = next(
            ref for ref in refs if ref.prev_string == f"Table {AUTONUMBER_PLACEHOLDER}"
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
        substitutions: list[Substitution] = self.bookstate[self.fp_a.stem][
            "substitutions"
        ]
        subst = next(
            subst for subst in substitutions if subst.pk == "02bdocxf02btblsimpletable"
        )
        assert subst.item_type == "ref"
        assert subst.file_count == 2
        # NOTE: this is updated on the builder (once we see all the files)
        # assert subst.prefix == ""
        # assert subst.prev_item_num == 1
        # assert subst.new_value() == "2.1"

    def test_footnote_start(self):
        refs: list[Ref] = self.bookstate[self.fp_a.stem]["refs"]
        ref = next(
            ref for ref in refs if ref.text == "Footnote link to an external website"
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
        refs: list[Ref] = self.bookstate[self.fp_a.stem]["refs"]
        ref = next(ref for ref in refs if ref.text == "footnote link")
        assert (
            ref.href == "https://web.archive.org/web/20250101004557/http:/example.com/"
        )
        assert ref.prev_string == "footnote link"
        assert (
            ref.prev_href
            == "https://web.archive.org/web/20250101004557/http:/example.com/"
        )

    def test_footnote_end(self):
        refs: list[Ref] = self.bookstate[self.fp_a.stem]["refs"]
        ref = next(ref for ref in refs if ref.text == "end of the footnote.")
        assert (
            ref.href == "https://web.archive.org/web/20250101004557/http:/example.com/"
        )
        assert ref.prev_string == "end of the footnote."
        assert (
            ref.prev_href
            == "https://web.archive.org/web/20250101004557/http:/example.com/"
        )

    def test_substitution_fig1(self):
        substitutions: list[Substitution] = self.bookstate[self.fp_a.stem][
            "substitutions"
        ]
        subst = next(subst for subst in substitutions if subst.pk == "f01aref177042490")
        assert subst.was == "1"
        assert subst.item_type == "figure"
        assert subst.file_count == 1
        assert subst.prefix == ""
        assert subst.prev_item_num == 1
        # assert subst.new_value() == "1.1"
        file_prefix = FileService.get_number_from_filename(self.fp_a.stem)
        assert file_prefix == 1
        assert SubstitutionService.to_digital_version(subst, file_prefix) == "1.1"

    def test_substitution_in_ref__crossref_fig1(self):
        ref = self.soup_a.find("a", href="#f-01-a-ref177042490")
        assert ref.text == r"Figure {{ f01aref177042490 }}"

    def test_substitution_tbl1(self):
        substitutions: list[Substitution] = self.bookstate[self.fp_a.stem][
            "substitutions"
        ]
        subst = next(subst for subst in substitutions if subst.pk == "f01aref177044323")
        assert subst.was == "1"
        assert subst.item_type == "table"
        assert subst.file_count == 1
        assert subst.prefix == ""
        assert subst.prev_item_num == 1
        # assert subst.new_value() == "1.1"
        file_prefix = FileService.get_number_from_filename(self.fp_a.stem)
        assert file_prefix == 1
        assert SubstitutionService.to_digital_version(subst, file_prefix) == "1.1"

    def test_substitution_in_ref__crossref_tbl1(self):
        ref = self.soup_a.find("a", href="#f-01-a-ref177044323")
        assert ref.text == r"Table {{ f01aref177044323 }}"

    def test_substitution_tbl1(self):
        file_stem = self.fp_a.stem
        substitutions: list[Substitution] = self.bookstate[file_stem]["substitutions"]
        subst = next(
            subst
            for subst in substitutions
            if subst.pk == "f01aequationwithcomplexnumbering"
        )
        assert subst.was == "I.A"
        assert subst.item_type == "equation"
        assert subst.file_count == 1
        assert subst.prefix == "I."
        assert subst.prev_item_num == 1
        file_prefix = FileService.get_number_from_filename(file_stem)
        assert file_prefix == 1
        assert SubstitutionService.to_digital_version(subst, file_prefix) == "1.I.1"

    def test_substitution_in_ref__infile_link(self):
        ref = self.soup_a.find("a", href="#f-01-a-equationwithcomplexnumbering")
        assert ref.text == r"see equation {{ f01aequationwithcomplexnumbering }}"

    def test_substitution_conditional_rendering_digital(self):
        substitutions: list[Substitution] = self.bookstate[self.fp_a.stem][
            "substitutions"
        ]
        subst = next(
            subst
            for subst in substitutions
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
        substitutions: list[Substitution] = self.bookstate[self.fp_a.stem][
            "substitutions"
        ]
        subst = next(
            subst
            for subst in substitutions
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
        substitutions: list[Substitution] = self.bookstate[self.fp_a.stem][
            "substitutions"
        ]
        subst = next(
            subst
            for subst in substitutions
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
        cls.bookstate: dict[str, DocumentState] = {}
        cls.soup, cls.docstate = cls._prepare_docx_for_ref_handing(cls.fp)
        cls.bookstate[cls.fp.stem] = cls.docstate

    @classmethod
    def _prepare_docx_for_ref_handing(
        cls, fp: KeyPath
    ) -> tuple[bs4.BeautifulSoup, DocumentMetadata]:
        docstate = DocumentState(fp)
        metadata = DocumentMetadata(fp)
        html_str = _convert_to_html(fp)
        html_soup, metadata, docstate, _ = prepare_docx(html_str, metadata, docstate)
        return html_soup, docstate

    def test_target_for_digital(self):
        target = self.docstate.get(
            "targets", "f-05-conditional-rendering-figfordigital"
        )
        assert target
        assert target.text == "1"
        assert target.is_digital == True
        assert target.is_paper == False
        assert target.filename == self.fp.name
        assert target.fragment == "figForDigital"

    def test_target_for_paper(self):
        target = self.docstate.get("targets", "f-05-conditional-rendering-figforpaper")
        assert target
        assert target.text == "2"
        assert target.is_digital == False
        assert target.is_paper == True
        assert target.filename == self.fp.name
        assert target.fragment == "figForPaper"

    def test_target_for_digital_and_for_paper(self):
        target = self.docstate.get(
            "targets", "f-05-conditional-rendering-figfordigitalandpaper"
        )
        assert target
        assert target.text == "3"
        assert target.is_digital == True
        assert target.is_paper == True
        assert target.filename == self.fp.name
        assert target.fragment == "figForDigitalAndPaper"

    def test_substitution_for_digital(self):
        subs = self.docstate.get("substitutions", "f05conditionalrenderingref193102947")
        assert subs
        assert subs.was == "1"
        assert subs.is_digital == True
        assert subs.is_paper == False
        assert subs.item_type == "figure"
        assert subs.file_count == 5
        assert subs.prefix == ""
        assert subs.prev_item_num == 1
        assert subs.new_item_num == 1
        # assert subs.new_value() == "5.1"
        file_prefix = FileService.get_number_from_filename(self.fp.stem)
        assert file_prefix == 5
        assert SubstitutionService.to_digital_version(subs, file_prefix) == "5.1"

    def test_substitution_for_paper(self):
        subs = self.docstate.get("substitutions", "f05conditionalrenderingref193102988")
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
        subs = self.docstate.get("substitutions", "f05conditionalrenderingref193103002")
        assert subs
        assert subs.was == "3"
        assert subs.is_digital == True
        assert subs.is_paper == True
        assert subs.item_type == "figure"
        assert subs.file_count == 5
        assert subs.prefix == ""
        assert subs.prev_item_num == 3
        assert subs.new_item_num == 2
        # assert subs.new_value() == "5.2"

    def test_substitution_for_refs(self):
        assert len(self.docstate["substitutions"]) == 7  # 4 targets + 3 refs
        subs = self.docstate.get(
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
        subs = self.docstate.get("substitutions", "f05conditionalrenderingfigforpaper")
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
        subs = self.docstate.get(
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
        subs: Substitution = self.docstate.get(
            "substitutions", "f05conditionalrenderingref193103002"
        )
        jsonified = subs.model_dump(mode="json")
        assert jsonified["was"] == "3"
        assert jsonified["is_digital"] == True
        assert jsonified["is_paper"] == True
        assert jsonified["item_type"] == "figure"
        assert jsonified["file_count"] == 5
        assert jsonified["prefix"] == ""
        assert jsonified["prev_item_num"] == 3
        assert jsonified["new_item_num"] == 2

    def test_substitution_from_json_handling(self):
        subs = self.docstate.get("substitutions", "f05conditionalrenderingref193103002")
        jsonified = subs.model_dump(mode="json")
        subs: Substitution = Substitution(**jsonified)
        assert subs.was == "3"
        assert subs.is_digital == True
        assert subs.is_paper == True
        assert subs.item_type == "figure"
        assert subs.file_count == 5
        assert subs.prefix == ""
        assert subs.prev_item_num == 3
        assert subs.new_item_num == 2
        file_prefix = FileService.get_number_from_filename(self.fp.stem)
        assert file_prefix == 5
        assert SubstitutionService.to_digital_version(subs, file_prefix) == "5.2"
        assert SubstitutionService.to_digital_version(subs, file_prefix="V") == "V.2"
