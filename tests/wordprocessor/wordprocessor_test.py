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
            "awsRegion": "eu-west-1",
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


from src.wordprocessor.conditional_rendering import (
    remove_parts_and_highlights_due_to_conditional_rendering,
)
from src.wordprocessor.constants import MAMMOTH_STYLE_MAP
from src.wordprocessor.main import _read_book_metadata
from src.wordprocessor.keys import KeyPath
from src.preparer.html2md import convert_to_md


class TestWordprocessor:
    key = KeyPath(
        pathlib.Path("/tmp") / "efs" / "docx2docx" / "02_assets_and_links.docx"
    )

    @classmethod
    def setup_class(cls):
        assert (
            cls.key.exists()
        ), "Make sure to run `make test/prep` to prepare the tests before running `make test`."
        # before wordprocessor
        cls.book_metadata = _read_book_metadata(cls.key)
        with open(cls.key, "rb") as f:
            cls.before_html = mammoth.convert_to_html(f, style_map=MAMMOTH_STYLE_MAP)
            cls.before_soup = bs4.BeautifulSoup(cls.before_html.value, "html.parser")
            cls.before_md = convert_to_md(cls.before_soup)
        # wordprocessor
        cls.doc = docx.Document(cls.key)
        remove_parts_and_highlights_due_to_conditional_rendering(cls.doc)
        file_stream = io.BytesIO()
        cls.doc.save(file_stream)
        file_stream.seek(0)
        # after wordprocessor
        cls.after_html = mammoth.convert_to_html(
            file_stream, style_map=MAMMOTH_STYLE_MAP
        )
        cls.after_soup = bs4.BeautifulSoup(cls.after_html.value, "html.parser")
        cls.after_md = convert_to_md(cls.after_soup)

    def test_removal_of_whole_highlighted_paragraph(self):
        before_headings = [tag.text for tag in self.before_soup.find_all("h3")]
        after_headings = [tag.text for tag in self.after_soup.find_all("h3")]
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
        assert before_txt in self.before_md
        assert before_txt not in self.after_md
        assert after_text in self.after_md
        assert after_text not in self.before_md

    def test_removal_of_highlight_from_run(self):
        before_soup_str = str(self.before_soup)
        after_soup_str = str(self.after_soup)
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
            a for a in self.before_soup.find_all("a", href=True) if a.text == "book"
        )
        after_link = next(
            a for a in self.after_soup.find_all("a", href=True) if a.text == "book"
        )
        assert len(before_link.span.get("class")) == 1
        assert before_link.span.get("class")[0] == "dgt-mon-paper-only"
        assert after_link.span is None
