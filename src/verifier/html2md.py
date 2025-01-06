# ===== IMPORTANT =====
# Remember, the only source of truth for html2md.py is the one defined in
# `src/_common/html2md.py`. Objects defined in other directories in
# the src/ folder should be replaced with `src/_common/html2md.py` before
# building the image. We advise that you always build the containers
# using Makefile commands, as the copy command is already included.
# ======================
import bs4
import markdownify
import re
import typing as t

try:
    from constants import CLS_METADATA_TABLE
    from metadata import DocumentMetadata
except (ImportError, ModuleNotFoundError):
    from .constants import CLS_METADATA_TABLE
    from .metadata import DocumentMetadata


line_beginning_re = re.compile(r"^", re.MULTILINE)

SUFFIXES_IMAGES = [".png", ".jpg"]


def sub_inline_conversion(markup_fn):
    """
    Returns a function that wraps the chomped text in a pair of the string
    that is returned by markup_fn. markup_fn is necessary to allow for
    references to self.strong_em_symbol etc.
    """

    def implementation(self, el, text, convert_as_inline):
        # footnotes: `el` param might be an anchor tag in a sup tag:
        # `<sup><a href="#footnote-1" id="footnote-ref-1">[1]</a></sup>`
        markup_tag = markup_fn(self)
        prefix, suffix, text = markdownify.chomp(text)
        if not text:
            return ""
        return "%s%s`%s`%s" % (prefix, markup_tag, text, suffix)

    return implementation


class MystMdConverter(markdownify.MarkdownConverter):

    def __init__(self, metadata: t.Optional[DocumentMetadata], **options):
        self._metadata: DocumentMetadata = metadata
        self._soup = bs4.BeautifulSoup("", "html.parser")
        super().__init__(**options)

    class Options(markdownify.MarkdownConverter.DefaultOptions):
        heading_style = markdownify.ATX
        autolinks = True
        escape_underscores = False
        escape_misc = False
        sub_symbol = "{sub}"
        sup_symbol = "{sup}"

    def escape(self, text):
        if not text:
            return ""
        if self.options["escape_misc"]:
            text = re.sub(r"([\\&<`[>~#=+|-])", r"\\\1", text)
            text = re.sub(r"([0-9])([.)])", r"\1\\\2", text)
        if self.options["escape_asterisks"]:
            text = text.replace("*", r"\*")
        if self.options["escape_underscores"]:
            text = text.replace("_", r"\_")
        return text

    # TODO: use regex to find _Ref patterns and better handle making data safe

    def convert_a(self, el, text, convert_as_inline):
        prefix, suffix, text = markdownify.chomp(text)
        identif = el.get("id", "")
        href = el.get("href", "")
        if href.startswith("#footnote-") and identif.startswith("footnote-ref-"):
            return "[^%s]" % identif
        if href.startswith("#endnote-") and identif.startswith("endnote-ref-"):
            return "[^%s]" % identif
        if identif.startswith("_Ref"):
            return '<html><a id="%s">%s</a></html>' % (identif, text)
        # if href.startswith("#_Ref"):
        #     return '<html><a href="%s">%s</a></html>' % (href, text)
        return super().convert_a(el, text, convert_as_inline)

    # def convert_a(self, el, text, convert_as_inline):
    #     prefix, suffix, text = chomp(text)
    #     if not text:
    #         return ''
    #     href = el.get('href')
    #     title = el.get('title')
    #     # For the replacement see #29: text nodes underscores are escaped
    #     if (self.options['autolinks']
    #             and text.replace(r'\_', '_') == href
    #             and not title
    #             and not self.options['default_title']):
    #         # Shortcut syntax
    #         return '<%s>' % href
    #     if self.options['default_title'] and not title:
    #         title = href
    #     title_part = ' "%s"' % title.replace('"', r'\"') if title else ''
    #     return '%s[%s](%s%s)%s' % (prefix, text, href, title_part, suffix) if href else text

    def convert_p(self, el, text, convert_as_inline):
        if text.startswith(
            ":::{iframe} <https://www.youtube.com/embed/"
        ) or text.startswith(":::{iframe} <https://player.vimeo.com/video/"):
            text = text.replace("<", "", 1)
            text = text.replace(">", "", 1)
        return super().convert_p(el, text, convert_as_inline)

    def convert_span(self, el, text, convert_as_inline):
        if text.startswith("% :::{") and text.endswith(":::"):
            return "\n%s\n\n" % text
        return super().convert_p(el, text, convert_as_inline)

    def convert_pre(self, el, text, convert_as_inline):
        h_target_match = re.match(r"^\([\w\-_]+\)=$", text)
        if h_target_match is not None:
            return "\n\n%s\n" % text
        return super().convert_pre(el, text, convert_as_inline)

    def convert_hn(self, n, el, text, convert_as_inline):
        if '<a href="' in text or '<a id="' in text:
            text = text.replace('<a href="', '<html><a href="')
            text = text.replace('<a id="', '<html><a id="')
            text = text.replace("</html>", "</a></html>")
        text = "\n" + text
        return super().convert_hn(n, el, text, convert_as_inline)

    def convert_li(self, el, text, convert_as_inline):
        identif = el.get("id", "")
        if identif.startswith("footnote-") or identif.startswith("endnote-"):
            inner = next(el.children)
            try:
                a = next(
                    node
                    for node in inner.children
                    if node.name == "a"
                    and (
                        node["href"].startswith("#footnote-ref-")
                        or node["href"].startswith("#endnote-ref-")
                    )
                )
            except StopIteration:
                return ""
            if a is None:
                return ""
            a.extract()
            text = inner.text.strip()
            if text.endswith(" ↑"):
                text = text[:-2]
            href = a.get("href", "")
            if href.startswith("#"):
                href = href[1:]
            return "[^%s]: %s" % (href, self.convert_soup(el))
        return super().convert_li(el, text, convert_as_inline)

    def convert_blockquote(self, el, text, convert_as_inline):
        if convert_as_inline:
            return text
        if el.next_sibling and el.next_sibling.name == "blockquote":
            end = "\n"
        else:
            end = "\n\n"
        return "" + (line_beginning_re.sub("> ", text) + end) if text else ""

    convert_sub = sub_inline_conversion(lambda self: self.options["sub_symbol"])

    def convert_sup(self, el, text, convert_as_inline):
        markup_tag = self.options["sup_symbol"]
        prefix, suffix, text = markdownify.chomp(text)
        if not text:
            return ""
        if text.startswith("[^footnote-ref-"):
            return text
        if text.startswith("[^endnote-ref-"):
            return text
        return "%s%s`%s`%s" % (prefix, markup_tag, text, suffix)

    def convert_iframe(
        self, el: bs4.element.Tag, text: str, convert_as_inline: bool
    ) -> str:
        print("\n\n\n")

        src = el.get("src")
        if src and src.startswith("https:/") and not src.startswith("https://"):
            el["src"] = src.replace("https:/", "https://")
        if src and src.startswith("http:/") and not src.startswith("http://"):
            el["src"] = src.replace("http:/", "http://")

        print('el.get("src")', el.get("src"))
        print("text", text)
        print("el", el)
        print(
            r'"\n\n<html>%s</html>\n\n" % repr(el)',
            "\n\n<html>%s</html>\n\n" % repr(el),
        )
        print(
            r'"\n\n<html>%s</html>\n\n" % str(el)', "\n\n<html>%s</html>\n\n" % str(el)
        )
        return "\n\n<html>%s</html>\n\n" % str(el)

    def convert_script(self, el, text, convert_as_inline):
        if el.get("hidden"):
            return "\n"
        return super().convert_script(el, text, convert_as_inline)

    # def convert_table(self, el, text, convert_as_inline):
    #     if el.get("hidden") and el.get("class") == CLS_METADATA_TABLE:
    #         return "\n% :::{dgt-mon-asset} " + el.get("id") + "\n"
    #     return super().convert_table(el, text, convert_as_inline)


def convert_to_md(
    soup: bs4.BeautifulSoup,
    metadata: t.Optional[DocumentMetadata] = None,
    **options,
) -> str:
    # TODO: change custom options to be passed to convert_to_md(**options <==)
    return MystMdConverter(metadata, **options).convert_soup(soup)
