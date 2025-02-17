import collections
import pathlib
import bs4

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
    fp_a = KeyPath(pathlib.Path("tests") / "_fixtures" / "refs" / "01_a.docx")
    fp_b = KeyPath(pathlib.Path("tests") / "_fixtures" / "refs" / "02_b.docx")

    @classmethod
    def setup_class(cls):
        cls.multidocs_meta: dict[KeyPath, DocumentMetadata] = {}
        cls.soup_a, cls.meta_a = cls._prepare_docx_for_ref_handing(cls.fp_a)
        cls.soup_b, cls.meta_b = cls._prepare_docx_for_ref_handing(cls.fp_b)
        cls.multidocs_meta[cls.fp_a] = cls.meta_a
        cls.multidocs_meta[cls.fp_b] = cls.meta_b
        cls.verifier = RefsAndTargetsVerifier()
        cls.warnings = cls.verifier.verify(cls.multidocs_meta)

    @classmethod
    def _prepare_docx_for_ref_handing(
        cls, fp: KeyPath
    ) -> tuple[bs4.BeautifulSoup, DocumentMetadata]:
        html_str = _convert_to_html(fp)
        html_soup = bs4.BeautifulSoup(html_str, "html.parser")
        metadata = DocumentMetadata(cls.fp_a)
        headers, captions, footnotes, references = [], [], [], []
        classifiers = [
            (is_header, headers),
            (is_caption, captions),
            (is_footnote, footnotes),
            (is_reference, references),
        ]
        # print(html_soup.prettify())
        for node in html_soup.descendants:
            for check_if_meets_criteria, container in classifiers:
                if isinstance(node, bs4.element.Tag) and check_if_meets_criteria(node):
                    container.append(node)
        html_soup = prepare_ref_targets_in_headers(html_soup, metadata, headers)
        html_soup = prepare_ref_targets_in_captions(html_soup, metadata, captions)
        html_soup = prepare_ref_targets_in_footnotes(html_soup, metadata, footnotes)
        html_soup = prepare_references(html_soup, metadata, references)
        return html_soup, metadata

    def test_verification(self):
        # print("self.warnings", self.warnings)
        for w in self.warnings:
            print(w["problem"])
            print(w["recommend"])
            print("-" * 20)

        print("len(self.warnings)", len(self.warnings))
        assert 1 == 5
