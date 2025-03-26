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


class TestRefDatapointsCreated:
    fp_a = KeyPath(pathlib.Path("tests") / "_fixtures" / "refs" / "01_a.docx")
    fp_b = KeyPath(pathlib.Path("tests") / "_fixtures" / "refs" / "02_b.docx")

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

    # def test_testing(self):
    #     print(">>> LEN=", len(self.multidocs_meta[self.fp_a.stem].refs))
    #     for ref in self.multidocs_meta[self.fp_a.stem].refs:
    #         print(ref.text)
    #         print(ref.href)
    #         print(ref.prev_string)
    #         print(ref.prev_href)
    #         print("-" * 75)
    #     assert 1 == 222
