import pathlib
import bs4

from src._common.state import DocumentState
from src.preparer.main import _convert_to_html
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
from src.builder.metadata import DocumentMetadata
from src.builder.keys import KeyPath
from src.builder.verif_book import RefsAndTargetsVerifier


class TestRefsAndTargetsVerifier:
    fp_a = KeyPath(pathlib.Path("tests") / "_fixtures" / "a_book" / "01_a.docx")
    fp_b = KeyPath(pathlib.Path("tests") / "_fixtures" / "a_book" / "02_b.docx")
    fp_cr = KeyPath(
        pathlib.Path("tests") / "_fixtures" / "a_book" / "05_conditional_rendering.docx"
    )

    @classmethod
    def setup_class(cls):
        cls.soup_a, cls.docstate_a = cls._prepare_docx_for_ref_handing(cls.fp_a)
        cls.soup_b, cls.docstate_b = cls._prepare_docx_for_ref_handing(cls.fp_b)
        cls.soup_cr, cls.docstate_cr = cls._prepare_docx_for_ref_handing(cls.fp_cr)
        cls.bookstate = {
            cls.fp_a.stem: cls.docstate_a,
            cls.fp_b.stem: cls.docstate_b,
            cls.fp_cr.stem: cls.docstate_cr,
        }
        cls.verifier = RefsAndTargetsVerifier()
        cls.warnings = cls.verifier.verify(cls.bookstate)

    @classmethod
    def _prepare_docx_for_ref_handing(
        cls, fp: KeyPath
    ) -> tuple[bs4.BeautifulSoup, DocumentMetadata]:
        html_str = _convert_to_html(fp)
        html_soup = bs4.BeautifulSoup(html_str, "html.parser")
        docstate = DocumentState(fp)
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
        html_soup = prepare_ref_targets_in_headers(
            html_soup, metadata, docstate, headers
        )
        html_soup = prepare_ref_targets_in_captions(
            html_soup, metadata, docstate, captions
        )
        html_soup = prepare_ref_targets_in_footnotes(
            html_soup, metadata, docstate, footnotes
        )
        html_soup = prepare_references(html_soup, metadata, docstate, references)
        return html_soup, docstate

    def test_check_a_is_not_https(self):
        warnings = [
            w
            for w in self.warnings
            if w["check"] == "check_a_not_archived" and w["fn"] == "01_a.docx"
        ]
        ref_string = "Link to external website without using https nor archived link"
        assert ref_string in warnings[0]["recommend"]
        assert len(warnings) == 1

    def test_check_a_not_archived(self):
        warnings = [
            w
            for w in self.warnings
            if w["check"] == "check_a_not_archived" and w["fn"] == "01_a.docx"
        ]
        ref_string = "Link to external website without using https nor archived link"
        assert ref_string in warnings[0]["recommend"]
        assert len(warnings) == 1

    def test_check_a_is_invalid_infile_link(self):
        warnings = [
            w for w in self.warnings if w["check"] == "check_a_is_invalid_infile_link"
        ]
        ref_string = "link to the same file where the fragment doesn't exist"
        assert ref_string in warnings[0]["recommend"]
        assert len(warnings) == 1

    def test_check_a_f2f_filename_is_invalid(self):
        warnings = [
            w for w in self.warnings if w["check"] == "check_a_f2f_filename_is_invalid"
        ]
        ref_string = "link to a separate file where the file does not exist"
        target_fn = "99_x"
        assert ref_string in warnings[0]["recommend"]
        assert target_fn in warnings[0]["recommend"]
        assert len(warnings) == 1

    def test_check_a_f2f_filename_is_absolute(self):
        warnings = [
            w for w in self.warnings if w["check"] == "check_a_f2f_filename_is_absolute"
        ]
        ref_string = "Link to a separate file with absolute path instead relative"
        assert ref_string in warnings[0]["recommend"]
        assert len(warnings) == 1

    def test_check_a_is_invalid_f2f(self):
        warnings = [w for w in self.warnings if w["check"] == "check_a_is_invalid_f2f"]
        ref_fragment = "#deletedTarget"
        assert ref_fragment in warnings[0]["recommend"]
        assert len(warnings) == 1

    def test_check_a_without_hash_or_http(self):
        warnings = [
            w for w in self.warnings if w["check"] == "check_a_without_hash_or_http"
        ]
        ref_string = "Hyperlink address is some characters – no hash or http protocol"
        ref_href = "addressTypedFromHand"
        assert ref_string in warnings[0]["recommend"]
        assert ref_href in warnings[0]["recommend"]
        assert len(warnings) == 1
