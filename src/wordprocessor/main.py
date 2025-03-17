import argparse
import bs4
import docx
import json
import os
import pathlib

from constants import CLS_METADATA_TABLE_JSONDATA
from metadata import DocumentMetadata
from html2docx import Html2DocxConverter
from keys import KeyPath


parser = argparse.ArgumentParser(description="...")
parser.add_argument("book_path", type=str)

"""
python scripts/prepare_and_build.py book_path="/mnt/c/Users/Pawel.kaminski/OneDrive - University of Luxembourg/Books/guidelines-for-drafting-manuscripts"/
python scripts/out_paper.py  book_path=/tmp/efs/guidelines-for-drafting-manuscripts/_html/
"""

EXLUDED_TAGS = (
    "script",
    # for now all known instances are about custom directives, e.g.
    # <span hidden="hidden">% :::{dgt-mon-asset} ed9c2212-4ff1-4ae5-a77c-cd949abf7d91 :::</span>
    "span",
)


def is_div(elem: bs4.element.Tag) -> bool:
    return elem.name == "div"


def is_h(elem: bs4.element.Tag) -> bool:
    return elem.name.startswith("h") and elem.name[1:].isdigit()


def is_p(elem: bs4.element.Tag) -> bool:
    return elem.name == "p"


def div_handler(doc: docx.document.Document, elem: bs4.element.Tag) -> None:
    # NOTE: This has to be handled.
    # For now all known instances include bibliographies
    # <div><h2>Bibliography</h2><ol><li><small>Puckett, J., 2017. <i>Zotero: A Guide For Librarians, Researchers, and Educators</i> 2nd edition., Assoc of College &amp; Research Libraries.</small></li><li><small>Fickers, A. &amp; Tatarinov, J. eds., 2022. <i>Digital History and Hermeneutics</i> first edition. A. Fickers &amp; J. Tatarinov, eds., De Gruyter Oldenbourg. Available at: https://doi.org/10.1515/9783110723991.</small></li></ol></div>
    return None


def h_handler(doc: docx.document.Document, elem: bs4.element.Tag) -> None:
    doc.add_heading(elem.text, level=int(elem.name[1:]))


def p_handler(doc: docx.document.Document, elem: bs4.element.Tag) -> None:
    doc.add_paragraph(elem.text)


def _get_document_metadata(html_soup: bs4.BeautifulSoup) -> DocumentMetadata:
    script_html = html_soup.find("script", {"class": CLS_METADATA_TABLE_JSONDATA})
    metadata = DocumentMetadata()
    if isinstance(script_html, bs4.element.Tag):
        metadata.from_json(json.loads(script_html.text))
    return metadata


checks_and_handlers = [
    (is_div, div_handler),
    (is_h, h_handler),
    # (is_ol, ol_handler), # ol/li
    (is_p, p_handler),
    # (is_blockquote, blockquote_handler),
    # (is_pre, pre_handler),
    # (is_table, table_handler),
    # (is_ul, ul_handler), # ul/li
]


def lambda_handler():
    args = parser.parse_args()
    book_path_arg = args.book_path.split("=")
    assert (
        len(book_path_arg) == 2
    ), "Please provide book_path=/path/to/book as an agrument"
    book_path = pathlib.Path(book_path_arg[1])
    # toprint = set()
    for src in book_path.glob("*"):
        print("src ", src)
        if not src.exists() or src.is_dir() or src.name.startswith("~$"):
            continue
        elif src.suffix == ".html":
            dst = src.with_suffix(".docx")
            with src.open("r") as f:
                html_str = f.read()
                html_soup = bs4.BeautifulSoup(html_str, "html.parser")
                doc = docx.Document()
                metadata = _get_document_metadata(html_soup)
                for elem in html_soup.children:
                    if not isinstance(elem, bs4.element.Tag):
                        continue
                    elif elem.name in EXLUDED_TAGS:
                        continue
                    for check, handler in checks_and_handlers:
                        if check(elem):
                            handler(doc, elem)
                doc.save(f"/tmp/efs/{dst.name}")
        # print(toprint)


def main():
    args = parser.parse_args()
    book_path_arg = args.book_path.split("=")
    assert (
        len(book_path_arg) == 2
    ), "Please provide book_path=/path/to/book as an agrument"
    book_path = pathlib.Path(book_path_arg[1])
    # toprint = set()
    try:
        os.mkdir("/tmp/efs/test/")
    except FileExistsError as e:
        pass
    for src in book_path.glob("*"):
        # print("src ", src)
        if not src.exists() or src.is_dir() or src.name.startswith("~$"):
            continue
        # elif src.suffix == ".html": # <= TODO: restore, the one below is for testing only
        elif src.suffix == ".html" and src.name == "simple.html":
            dst = src.with_suffix(".docx")
            with src.open("r") as f:
                html_str = f.read()
                html_soup = bs4.BeautifulSoup(html_str, "html.parser")
                doc = Html2DocxConverter().convert_soup(html_soup)
                # print("html_soup", html_soup)
                doc.save(f"/tmp/efs/test/{dst.name}")


import docx.shared
import docx.styles.style
import docx.text.paragraph
import docx.oxml.text.font
import docx.oxml.text.paragraph


def main2():
    book_metadata: dict[str, DocumentMetadata] = {}
    key: KeyPath = KeyPath("/tmp/efs/docx2docx/")
    # for meta_file in (key.efs_slug_dir / "_metadata").glob("**/*.json"):
    for meta_file in (key / "_metadata").glob("**/*.json"):
        meta_file: KeyPath
        with meta_file.open("r") as f:
            book_metadata[meta_file.stem] = DocumentMetadata(meta_file)

    # with open("/tmp/efs/docx2docx/02_assets_and_links.docx") as f:
    doc = docx.Document("/tmp/efs/docx2docx/02_assets_and_links.docx")
    """
    # changing styles
    style = doc.styles["Normal"]
    style: docx.styles.style._ParagraphStyle
    style.font.color.rgb = docx.shared.RGBColor(235, 64, 52)
    # or
    # style.font.color.rgb = (docx.shared.RGBColor)(style.font.color.rgb).from_string("eb4034")
    style.font.size = docx.shared.Pt(12)
    style.font.bold = True
    style.font.italic = True
    style.font.underline = True
    # accessing xml
    print(doc._element.xml)
    """
    highlights = doc.paragraphs[0]._element.xpath(".//w:rPr/w:highlight")

    # conditional rendering
    digital_only = "lightGray"
    paper_only = "cyan"
    for p in doc.paragraphs:

        # If paragraph's properties (pPr) have a highlight,
        # then whole paragraph is highlighted
        # highlights: list[docx.oxml.text.font.CT_Highlight] = []
        # highlights = p._element.xpath(".//w:pPr/w:rPr/w:highlight")
        # if len(highlights) == 1 and digital_only in highlights[0].values():
        if _is_whole_paragraph_only_for_digital(p, digital_only):
            # par: docx.oxml.text.paragraph.CT_P = p._element
            # assert isinstance(par, docx.oxml.text.paragraph.CT_P)
            # par_parent: docx.oxml.document.CT_Body = par.getparent()
            # assert isinstance(par_parent, docx.oxml.document.CT_Body)
            # par_parent.remove(par)
            # par._p = None
            # par._element = None
            _remove_whole_paragraph(p)
            continue

        for r in p.runs:
            if (r.element.rPr is None) or (r.element.rPr.highlight is None):
                continue
            if digital_only in r.element.rPr.highlight.values():
                r.clear()
            elif paper_only in r.element.rPr.highlight.values():
                print("REMOVE HIGHLIGHT, LEAVE RUN")

    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    for r in p.runs:
                        if (r.element.rPr is None) or (r.element.rPr.highlight is None):
                            continue
                        if digital_only in r.element.rPr.highlight.values():
                            tbl._element.clear()
                            break
                        elif paper_only in r.element.rPr.highlight.values():
                            print("REMOVE HIGHLIGHT, LEAVE TABLE")

    return doc


def _is_whole_paragraph_only_for_digital(
    p: docx.text.paragraph.Paragraph, digital_only: str
) -> bool:
    """
    If paragraph's properties (pPr) have a highlight,
    then whole paragraph is highlighted.
    If so, check if the whole paragraph is marked as digital_only.

    Example of a paragraph where the function should return True:
    ```xml
    <p>
        <pPr>
            <pStyle w:val="BodyText" />
            <rPr>
                <highlight w:val="lightGray" />
            </rPr>
        </pPr>
        ...
    ```
    Example of a paragraph where the function should return False:
    ```xml
    <p>
        <pPr>
            <pStyle w:val="BodyText" />
        </pPr>
        ...
    ```
    """
    highlights: list[docx.oxml.text.font.CT_Highlight] = []
    highlights = p._element.xpath(".//w:pPr/w:rPr/w:highlight")
    return len(highlights) == 1 and digital_only in highlights[0].values()


def _remove_whole_paragraph(p: docx.text.paragraph.Paragraph) -> None:
    par: docx.oxml.text.paragraph.CT_P = p._element
    assert isinstance(par, docx.oxml.text.paragraph.CT_P)
    par_parent: docx.oxml.document.CT_Body = par.getparent()
    assert isinstance(par_parent, docx.oxml.document.CT_Body)
    par_parent.remove(par)
    par._p = None
    par._element = None


doc = None
if __name__ == "__main__":
    doc = main2()
    doc.save("/tmp/efs/docx2docx/test.docx")
