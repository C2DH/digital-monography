# import bs4
# import mammoth
# import pathlib

# from src.preparer.citations import add_citations_and_bibliography
# from src.preparer.html2md import convert_to_md
# from src.preparer.md_extraction import DocumentMetadata


# class TestHtml2MdFootnotes:
#     fp = pathlib.Path("tests") / "_fixtures" / "hyperlinks-a.docx"

#     @classmethod
#     def setup_class(cls):
#         with open(cls.fp, "rb") as f:
#             result = mammoth.convert_to_html(f)
#         cls.html_soup = bs4.BeautifulSoup(result.value, "html.parser")
#         cls.html_soup = add_citations_and_bibliography(cls.html_soup)
#         metadata = DocumentMetadata()
#         cls.md = convert_to_md(cls.html_soup, metadata)

#     def test_testing(self):
#         print(self.md)
#         assert 1 == 2
