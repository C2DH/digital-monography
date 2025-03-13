import bs4
import docx
import docx.document
import docx.text.paragraph
import docx.text.run
import re
import typing as t


re_all_whitespace = re.compile(r"[\t \r\n]+")
re_html_heading = re.compile(r"h(\d+)")
# Pattern for creating convert_<tag> function names from tag names
re_make_convert_fn_name = re.compile(r"[\[\]:-]")


def should_remove_whitespace_inside(el: bs4.NavigableString):
    """Return to remove whitespace immediately inside a block-level element."""
    assert isinstance(el, bs4.NavigableString)
    if not el or not el.name:
        return False
    if re_html_heading.match(el.name) is not None:
        return True
    return el.name in (
        "p",
        "blockquote",
        "article",
        "div",
        "section",
        "ol",
        "ul",
        "li",
        "dl",
        "dt",
        "dd",
        "table",
        "thead",
        "tbody",
        "tfoot",
        "tr",
        "td",
        "th",
    )


def should_remove_whitespace_outside(el: t.Any):
    """Return to remove whitespace immediately outside a block-level element."""
    return should_remove_whitespace_inside(el) or (el and el.name == "pre")


class Html2DocxConverter:
    """
    Converts html as string or BeautifulSoup to .docx (MS Word).
    This method of processing was modelled after Matthew Dapena-Tretter's python-markdownify
    """

    def __init__(self):
        self.doc: docx.document.Document = docx.Document()
        self.options: dict[str, str | bool] = {}
        # Initialize the conversion function cache
        self.convert_fn_cache: dict[str, t.Callable | None] = {}

    def convert(self, html: str) -> docx.document.Document:
        soup = bs4.BeautifulSoup(html, "html.parser")
        return self.convert_soup(soup)

    def convert_soup(self, soup: bs4.BeautifulSoup) -> docx.document.Document:
        assert isinstance(soup, bs4.BeautifulSoup)
        self.convert_recursively(soup)
        return self.doc

    def convert_recursively(
        self, htmlnode: bs4.BeautifulSoup | bs4.Tag, docxnode: t.Any | None = None
    ) -> str:
        assert isinstance(htmlnode, bs4.BeautifulSoup | bs4.Tag)
        for child in htmlnode.children:
            print("docxnode", docxnode)
            if isinstance(child, bs4.NavigableString):
                self.convert_string(child, docxnode)
            elif isinstance(child, bs4.Tag):
                convert_fn = self.get_conv_fn_cached(child.name)
                if convert_fn is not None:
                    docxnode = convert_fn(child, docxnode)
                self.convert_recursively(child, docxnode)

    # def process_element(
    #     self,
    #     node: bs4.Tag | bs4.NavigableString,
    # ) -> str:
    #     if isinstance(node, bs4.NavigableString):
    #         res = self.process_text(node)
    #     else:
    #         res = self.process_tag(node)
    #     # assert isinstance(res, str) # NO, it can't be a string
    #     return res

    # def _can_ignore(self, el: t.Any):
    #     if isinstance(el, bs4.Tag):
    #         # Tags are always processed.
    #         return False
    #     elif isinstance(el, (bs4.Comment, bs4.Doctype)):
    #         # Comment and Doctype elements are always ignored.
    #         # (subclasses of NavigableString, must test first)
    #         return True
    #     elif isinstance(el, bs4.NavigableString):
    #         # markdownify uses six to support python2
    #         if str(el).strip() != "":
    #             return False

    # def process_tag(
    #     self, node: bs4.BeautifulSoup | bs4.Tag, parent_tags: list[t.Any] | None = None
    # ) -> str:
    #     # For the top-level element, initialize the parent context with an empty list.
    #     if parent_tags is None:
    #         parent_tags = list()

    #     # Collect child elements to process, ignoring whitespace-only text elements
    #     # adjacent to the inner/outer boundaries of block elements.
    #     should_remove_inside = should_remove_whitespace_inside(node)

    #     def _can_ignore(el):
    #         if isinstance(el, bs4.Tag):
    #             # Tags are always processed.
    #             return False
    #         elif isinstance(el, (bs4.Comment, bs4.Doctype)):
    #             # Comment and Doctype elements are always ignored.
    #             # (subclasses of NavigableString, must test first)
    #             return True
    #         elif isinstance(el, bs4.NavigableString):
    #             # markdownify uses six to support python2
    #             if str(el).strip() != "":
    #                 # Non-whitespace text nodes are always processed.
    #                 return False
    #             elif should_remove_inside and (
    #                 not el.previous_sibling or not el.next_sibling
    #             ):
    #                 # Inside block elements (excluding <pre>), ignore adjacent whitespace elements.
    #                 return True
    #             elif should_remove_whitespace_outside(
    #                 el.previous_sibling
    #             ) or should_remove_whitespace_outside(el.next_sibling):
    #                 # Outside block elements (including <pre>), ignore adjacent whitespace elements.
    #                 return True
    #             else:
    #                 return False
    #         elif el is None:
    #             return True
    #         else:
    #             raise ValueError("Unexpected element type: %s" % type(el))

    #     children_to_convert = [el for el in node.children if not _can_ignore(el)]
    #     children_to_convert: list[bs4.Tag | bs4.NavigableString]

    #     # Create a copy of this tag's parent context, then update it to include this tag
    #     # to propagate down into the children.
    #     parent_tags_for_children = list(parent_tags)
    #     parent_tags_for_children.append(node)
    #     # parent_tags_for_children.add(node.name)

    #     # TODO: if this tag is a heading or table cell, add an '_inline' parent pseudo-tag
    #     # TODO: if this tag is a preformatted element, add a '_noformat' parent pseudo-tag

    #     # Convert the children elements into a list of result strings.
    #     child_strings = [
    #         self.process_element(el, parent_tags=parent_tags_for_children)
    #         for el in children_to_convert
    #     ]

    #     # Remove empty string values.
    #     child_strings = [s for s in child_strings if s]
    #     # print("child_strings", child_strings)

    #     # TODO: Collapse newlines at child element boundaries, if needed.

    #     # Join all child text strings into a single string.
    #     # text = "".join(child_strings)
    #     text = ""

    #     # apply this tag's final conversion function
    #     convert_fn = self.get_conv_fn_cached(node.name)
    #     if convert_fn is not None:
    #         text = convert_fn(node, text, parent_tags=parent_tags)

    #     # assert isinstance(text, str)
    #     # print("text", text)
    #     return text

    # def process_text(
    #     self, el: bs4.NavigableString, parent_tags: list[t.Any] | None = None
    # ) -> str:
    #     assert isinstance(el, bs4.NavigableString)
    #     if parent_tags is None:
    #         parent_tags = list()

    #     # TODO: support whitespaces and special characters
    #     # markdownify uses six to support python2
    #     return str(el) or ""

    def get_conv_fn_cached(self, tag_name: str) -> t.Callable | None:
        """Given a tag name, return the conversion function using the cache."""
        # If conversion function is not in cache, add it
        assert isinstance(tag_name, str)
        if tag_name not in self.convert_fn_cache:
            self.convert_fn_cache[tag_name] = self.get_conv_fn(tag_name)

        # Return the cached entry
        assert isinstance(self.convert_fn_cache[tag_name], t.Callable | None)
        return self.convert_fn_cache[tag_name]

    def get_conv_fn(self, tag_name: str) -> t.Callable | None:
        """Given a tag name, find and return the conversion function."""
        tag_name = tag_name.lower()
        # TODO: Handle strip/convert exclusion options

        # Handle headings with _convert_hn() function
        match = re_html_heading.match(tag_name)
        if match:
            n = int(match.group(1))
            return lambda currnode, docxparent: self._convert_hn(
                n, currnode, docxparent
            )
            # return lambda el, text, parent_tags: self._convert_hn(
            #     n, el, text, parent_tags
            # )

        # For other tags, look up their conversion function by tag name
        convert_fn_name = "convert_%s" % re_make_convert_fn_name.sub("_", tag_name)
        convert_fn = getattr(self, convert_fn_name, None)
        assert isinstance(convert_fn, t.Callable | None)
        return convert_fn

    def convert_string(
        self,
        el: bs4.NavigableString,
        docxparent: docx.text.paragraph.Paragraph | docx.text.run.Run | None,
    ) -> None:
        print("convert_string")
        print("el", el, type(el))
        print("parent", docxparent, type(docxparent))
        text = str(el)
        if text and isinstance(docxparent, docx.text.paragraph.Paragraph):
            assert isinstance(docxparent, docx.text.paragraph.Paragraph)
            docxparent.add_run(str(el))
        return None

    def convert_p(
        self,
        el: bs4.Tag,
        docxparent: t.Any | None,
    ) -> docx.text.paragraph.Paragraph:
        print("convert_p")
        print("el", el, type(el))
        print("parent", docxparent, type(docxparent))
        return self.doc.add_paragraph()
        # return text

    def convert_em(
        self,
        el: bs4.Tag,
        docxparent: t.Any | None,
    ) -> None:
        print("convert_em")
        print("el", el, type(el))
        print("parent", docxparent, type(docxparent))
        if isinstance(docxparent, docx.text.paragraph.Paragraph):
            run = docxparent.add_run()
            run.italic = True
            return run
        return docxparent

    def convert_strong(
        self,
        el: bs4.Tag,
        docxparent: t.Any | None,
    ) -> None:
        print("convert_em")
        print("el", el, type(el))
        print("parent", docxparent, type(docxparent))
        if isinstance(docxparent, docx.text.paragraph.Paragraph):
            run = docxparent.add_run()
            run.bold = True
            return run
        return docxparent

    def convert_script(
        self,
        el: bs4.Tag,
        docxparent: t.Any | None,
    ) -> None:
        # print("convert_script")
        # print("el", el, type(el))
        # print("parent", docxparent, type(docxparent))
        return None

    def _convert_hn(
        self,
        n: int,
        el: bs4.Tag,
        docxparent: t.Any | None,
    ) -> None:
        """Method name prefixed with _ to prevent <hn> to call this"""
        print("convert_hn")
        print("el", el, type(el))
        print("parent", docxparent, type(docxparent))

        assert isinstance(n, int)
        assert isinstance(el, bs4.Tag)

        # prevent MemoryErrors in case of very large n
        n = max(1, min(6, n))

        text = el.text.strip()
        text = re_all_whitespace.sub(" ", text)

        assert isinstance(self.doc, docx.document.Document)
        self.doc.add_heading(text, level=n)
        return None
        # NOTE: this worked with markdown but with docx I need something different
        # return text
