import bs4
import mammoth
import pathlib

# from src.preparer.citations import add_citations_and_bibliography
# from src.preparer.html2md import convert_to_md
# from src.preparer.md_extraction import BookMetadata
from src.preparer.main import _convert_to_html
from src.preparer.keys import KeyPath


class TestStyleMappings:
    fp = pathlib.Path("tests") / "_fixtures" / "style_mappings.docx"

    @classmethod
    def setup_class(cls):
        cls.html_str = _convert_to_html(KeyPath(cls.fp))
        cls.html_soup = bs4.BeautifulSoup(cls.html_str, "html.parser")

    def test_blockquotes(self):
        blockquotes = self.html_soup.find_all("blockquote")
        assert len(blockquotes) == 1
        assert blockquotes[0].text == "A quote."

    def test_captions(self):
        captions = self.html_soup.find_all("p", "dgt-mon-caption")
        assert len(captions) == 1
        assert captions[0].text == "Figure 1: A caption."
