import bs4
import docx
import io
import pathlib
import mammoth

DEFAULT_S3_EVENT = {
    "Records": [
        {
            "eventVersion": "2.1",
            "eventSource": "aws:s3",
            "awsRegion": "eu-central-1",
            "eventTime": "2024-06-01T10:01:01.100Z",
            "eventName": "ObjectCreated:Put",
            "userIdentity": {"principalId": "AWS:AROAVK5GEQE3275W6UTUO:preparer"},
            "requestParameters": {"sourceIPAddress": "10.10.2.149"},
            "responseElements": {
                "x-amz-request-id": "7MMJ7WJPN7GM5KYN",
                "x-amz-id-2": "E3m/Eudcp6Z7vZh9Ex1blHs1bHy7ajDl71V6BBnXFD5dwiHqE+ylOE578E4+ShRpve8ctI5y9abpl4QbtsPrl3XhN8bxbgiF",
            },
            "s3": {
                "s3SchemaVersion": "1.0",
                "configurationId": "tf-s3-lambda-20240531090332003100000001",
                "bucket": {
                    "name": "dgtmon-dev-apkg-upload",
                    "ownerIdentity": {"principalId": "A13XBETHGUR4IG"},
                    "arn": "arn:aws:s3:::dgtmon-dev-apkg-upload",
                },
                "object": {
                    "key": "PLACE YOUR SLUG/PATH/TO/FILE HERE",
                    "size": 278,
                    "eTag": "3647c11ea643861bb23a8dd628cd0642",
                    "sequencer": "00665DF6D32A167391",
                },
            },
        }
    ]
}


from src._common.constants import AUTONUMBER_PLACEHOLDER, MAMMOTH_STYLE_MAP
from src._common.keys import KeyPath
from src._common.metadata import DocumentMetadata
from src._common.state import DocumentState
from src.preparer.main import prepare_docx
from src.preparer.html2md import convert_to_md
from src.wordprocessor.main import wordprocess_docx


class TestWordprocessor:
    # key = KeyPath(
    #     pathlib.Path("/tmp") / "efs" / "a_book" / "05_conditional_rendering.docx"
    # )
    # fp_i = KeyPath(pathlib.Path("tests") / "_fixtures" / "a_book" / "00_index.docx")
    key_a = KeyPath(pathlib.Path("tests") / "_fixtures" / "a_book" / "01_a.docx")
    key_b = KeyPath(pathlib.Path("tests") / "_fixtures" / "a_book" / "02_b.docx")
    key_cr = KeyPath(
        pathlib.Path("tests") / "_fixtures" / "a_book" / "05_conditional_rendering.docx"
    )

    @classmethod
    def setup_class(cls):
        cls.bookstate: dict[str, DocumentState] = {}
        cls.before_soup, cls.before_md, cls.after_soup, cls.after_md = {}, {}, {}, {}
        cls._prepare_docx(cls.key_a)
        cls._prepare_docx(cls.key_b)
        cls._prepare_docx(cls.key_cr)
        cls._wordprocess_docx(cls.key_a)
        cls._wordprocess_docx(cls.key_b)
        cls._wordprocess_docx(cls.key_cr)

    @classmethod
    def _prepare_docx(cls, key: KeyPath) -> None:
        # before wordprocessor
        with open(key, "rb") as f:
            before_html = mammoth.convert_to_html(f, style_map=MAMMOTH_STYLE_MAP)
            before_soup = bs4.BeautifulSoup(before_html.value, "html.parser")
        # preparer
        cls.docstate = DocumentState(key)
        metadata = DocumentMetadata(key)
        _, metadata, cls.docstate, _ = prepare_docx(
            before_html.value, metadata, cls.docstate
        )
        cls.bookstate[key.stem] = cls.docstate
        cls.before_soup[key.stem] = before_soup
        cls.before_md[key.stem] = convert_to_md(before_soup)

    @classmethod
    def _wordprocess_docx(cls, key: KeyPath) -> None:
        # wordprocessor
        doc = wordprocess_docx(key, cls.bookstate)
        # after wordprocessor
        file_stream = io.BytesIO()
        doc.save(file_stream)
        file_stream.seek(0)
        after_html = mammoth.convert_to_html(file_stream, style_map=MAMMOTH_STYLE_MAP)
        after_soup = bs4.BeautifulSoup(after_html.value, "html.parser")
        after_md = convert_to_md(after_soup)
        cls.after_soup[key.stem] = after_soup
        cls.after_md[key.stem] = after_md

    def test_removal_of_whole_highlighted_paragraph(self):
        before_headings = [
            tag.text for tag in self.before_soup[self.key_cr.stem].find_all("h3")
        ]
        after_headings = [
            tag.text for tag in self.after_soup[self.key_cr.stem].find_all("h3")
        ]
        assert "Asset for digital" in before_headings
        assert "Asset for digital" not in after_headings

        """
    def test_clearance_of_highlighted_run(self):
        # NOTE: this should pass, but the preparer inserts newlines where spans were.
        # TODO: add conditional rendering to the preparer
        # print("self.before_md", repr(self.before_md)[150:400])
        # print("self.after_md", repr(self.after_md)[150:400])
        before_txt = "This paragraph contains an example of a run (part of a paragraph) that is only visible in the digitalpaper version."
        after_text = "This paragraph contains an example of a run (part of a paragraph) that is only visible in the paper version."
        assert before_txt in self.before_md
        assert before_txt not in self.after_md
        assert after_text in self.after_md
        assert after_text not in self.before_md
        """

    def test_clearance_of_highlighted_hyperlink(self):
        before_txt = "hyperlinks to e.g. [ebook](https://en.wikipedia.org/wiki/Ebook)[book](https://en.wikipedia.org/wiki/Book)."
        after_text = "hyperlinks to e.g. [book](https://en.wikipedia.org/wiki/Book)."
        assert before_txt in self.before_md[self.key_cr.stem]
        assert before_txt not in self.after_md[self.key_cr.stem]
        assert after_text in self.after_md[self.key_cr.stem]
        assert after_text not in self.before_md[self.key_cr.stem]

    def test_removal_of_highlight_from_run(self):
        before_soup_str = str(self.before_soup[self.key_cr.stem])
        after_soup_str = str(self.after_soup[self.key_cr.stem])
        before_txt = (
            "is only visible in the "
            '<span class="dgt-mon-digital-only">digital</span>'
            '<span class="dgt-mon-paper-only">paper</span>'
            " version."
        )
        after_text = "is only visible in the paper version."
        assert before_txt in before_soup_str
        assert after_text not in before_soup_str
        assert after_text in after_soup_str
        assert before_txt not in after_soup_str

    def test_removal_of_highlight_from_hyperlink(self):
        before_link = next(
            a
            for a in self.before_soup[self.key_cr.stem].find_all("a", href=True)
            if a.text == "book"
        )
        after_link = next(
            a
            for a in self.after_soup[self.key_cr.stem].find_all("a", href=True)
            if a.text == "book"
        )
        assert len(before_link.span.get("class")) == 1
        assert before_link.span.get("class")[0] == "dgt-mon-paper-only"
        assert after_link.span is None

    def test_targets_in_captions_with_added_chapter_numbers(self):
        # Figure 1 removed during conditional rendering
        assert "**Figure 5.1:** Drawing" not in self.before_md[self.key_cr.stem]
        assert "**Figure 5.1:** Drawing" not in self.after_md[self.key_cr.stem]
        assert "**Figure 1:** Drawing" not in self.after_md[self.key_cr.stem]

        assert "**Figure 2:** Image" in self.before_md[self.key_cr.stem]
        assert "**Figure 5.2:** Image" not in self.before_md[self.key_cr.stem]
        assert "**Figure 5.2:** Image" in self.after_md[self.key_cr.stem]
        assert "**Figure 2:** Image" not in self.after_md[self.key_cr.stem]

        assert "**Figure 3:** An example" in self.before_md[self.key_cr.stem]
        assert "**Figure 5.3:** An example" not in self.before_md[self.key_cr.stem]
        assert "**Figure 5.3:** An example" in self.after_md[self.key_cr.stem]
        assert "**Figure 3:** An example" not in self.after_md[self.key_cr.stem]

        assert "**Figure 4:** Target" in self.before_md[self.key_cr.stem]
        assert "**Figure 5.4:** Target" not in self.before_md[self.key_cr.stem]
        assert "**Figure 5.4:** Target" in self.after_md[self.key_cr.stem]
        assert "**Figure 4:** Target" not in self.after_md[self.key_cr.stem]

    def test_prepare_refs__placeholder_f2f(self):
        before = (
            "In a separate file: Links to "
            "[Heading](02_b.docx#h2Subheading), "
            f"[Figure {AUTONUMBER_PLACEHOLDER}](02_b.docx#figRedSquare), and to "
            f"[Table {AUTONUMBER_PLACEHOLDER}](02_b.docx#tblSimpleTable)."
        )
        after = (
            "In a separate file: Links to "
            "[Heading](02_b.docx#h2Subheading), "
            "[Figure 2.1](02_b.docx#figRedSquare), and to "
            "[Table 2.1](02_b.docx#tblSimpleTable)."
        )
        assert before in self.before_md[self.key_a.stem]
        assert before not in self.after_md[self.key_a.stem]
        assert after in self.after_md[self.key_a.stem]
        assert after not in self.before_md[self.key_a.stem]
        # assert 1 == 3

    def test_prepare_refs__placeholder_infile(self):
        before = f"Complex numbering: [see equation {AUTONUMBER_PLACEHOLDER}](#equationWithComplexNumbering)."
        after = (
            "Complex numbering: [see equation 1.I.1](#equationWithComplexNumbering)."
        )
        assert before in self.before_md[self.key_a.stem]
        assert before not in self.after_md[self.key_a.stem]
        assert after in self.after_md[self.key_a.stem]
        assert after not in self.before_md[self.key_a.stem]

    def test_prepare_refs__placeholder_with_conditional_rendering(self):
        before = (
            "Conditional rendering: "
            f"[link to fig {AUTONUMBER_PLACEHOLDER} (digital only)](05_conditional_rendering.docx#figForDigital), "
            f"[link to fig {AUTONUMBER_PLACEHOLDER} (paper only)](05_conditional_rendering.docx#figForPaper), "
            f"[link to fig {AUTONUMBER_PLACEHOLDER} (digital and paper)](05_conditional_rendering.docx#figForDigitalAndPaper)."
        )
        after = (
            "Conditional rendering: "
            "[link to fig (digital only)](05_conditional_rendering.docx#figForDigital), "
            "[link to fig 5.1 (paper only)](05_conditional_rendering.docx#figForPaper), "
            "[link to fig 5.2 (digital and paper)](05_conditional_rendering.docx#figForDigitalAndPaper)."
        )

        print(self.after_md[self.key_a.stem])
        assert before in self.before_md[self.key_a.stem]
        assert before not in self.after_md[self.key_a.stem]
        assert after in self.after_md[self.key_a.stem]
        assert after not in self.before_md[self.key_a.stem]

    def test_remove_images(self):
        imgs = self.before_soup[self.key_cr.stem].find_all("img")
        for img in imgs:
            print(img.get("alt"))
        assert len(imgs) == 4
        imgs = self.after_soup[self.key_cr.stem].find_all("img")
        assert len(imgs) == 0
