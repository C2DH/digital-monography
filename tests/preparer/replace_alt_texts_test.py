import bs4

from src.preparer.replace_alt_texts import replace_alt_texts


HTML_STR = f"""<h1>Book Title</h1>
<h2>Heading 2</h2>
<p>An example of an image is placed below.</p>
<p class="dgt-mon-caption"><strong>Figure 1:</strong> An example of an image.</p>
<p><img alt="The

Alt

Text" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAIAAAACUFjqAAAAAXNSR0IArs4c6QAAAAlwSFlzAAAOvgAADr4B6kKxwAAAABNJREFUKFNj/M+ADzDhlWUYqdIAQSwBE8U+X40AAAAASUVORK5CYII="/></p>
"""


class TestReplacingLineBreaksInAltTexts:
    @classmethod
    def setup_class(cls):
        cls.html_soup = bs4.BeautifulSoup(HTML_STR, "html.parser")
        cls.html_soup = replace_alt_texts(cls.html_soup)

    def test_line_break_was_removed_from_alttext(self):
        img = self.html_soup.find_all("img")[0]
        assert img["alt"] == "The  Alt  Text"
