import bs4
import pytest

from src.preparer.main import convert_to_bs
from src.preparer.split_into_chapters import split_docx_into_multiple_chapters
from src.preparer.frontmatter import FrontmatterBlob


def _html_equal(a: bs4.BeautifulSoup, b: bs4.BeautifulSoup) -> bool:
    # Compare normalized string representations
    return a.decode().strip() == b.decode().strip()


# A basic test with two chapters.
basic_input_html = """
<h1>text1</h1>
<a href="link">link</a>

<h1>text2</h1>
<p>Some content</p>
"""
basic_expected_split = [
    """
    <h1>text1</h1>
    <a href="link">link</a>
    """,
    """
    <h1>text2</h1>
    <p>Some content</p>
    """,
]
# Check if it preserves attributes and order, and handles nested tags.
complex_input_html = """
<h1 id="a">A</h1>
<table><tr><td>Data</td></tr></table>
<h1 id="b">B</h1>
<h2>...</h2>
<img src="i.png" alt="img">
<h1>C</h1>
<p class="x">xxx</p>
"""
complex_expected_split = [
    """
    <h1 id="a">A</h1>
    <table><tr><td>Data</td></tr></table>
    """,
    """
    <h1 id="b">B</h1>
    <h2>...</h2>
    <img src="i.png" alt="img">
    """,
    """
    <h1>C</h1>
    <p class="x">xxx</p>
    """,
]
# Test if it includes content before the first <h1>.
no_h1_input_html = """
<span class="dgt-mon-frontmatter-table">---
title: Frontmatter example
---
</span>
<h2>Intro</h2>
<p>...</p>
<h1>Main</h1>
<p>Main content</p>
"""
no_h1_expected_split = [
    """<span class="dgt-mon-frontmatter-table">---
title: Frontmatter example
---
</span>
<h2>Intro</h2>
<p>...</p>
""",
    """
<h1>Main</h1>
<p>Main content</p>
    """,
]
# Test if it handles bookmarks (<pre> tags) before headings.
bookmarked_input_html = """
<pre>(f-filename-bookmark1)=</pre>
<h1>Heading1</h1>
<p>xxx</p>
<pre>(f-filename-bookmark2)=</pre>
<pre>(f-filename-bookmark3)=</pre>
<h1>Heading2</h1>
<p>yyy</p>
<h1>No bookmark</h1>
<p>zzz</p>
"""
bookmarked_expected_split = [
    """
<pre>(f-filename-bookmark1)=</pre>
<h1>Heading1</h1>
<p>xxx</p>
""",
    """
<pre>(f-filename-bookmark2)=</pre>
<pre>(f-filename-bookmark3)=</pre>
<h1>Heading2</h1>
<p>yyy</p>
""",
    """
<h1>No bookmark</h1>
<p>zzz</p>
""",
]
# Before h1 there is content and bookmark
bookmarked_with_into_input_html = """
<p>Don't forget about me</p>
<pre>(f-filename-bookmark-to-h2)=</pre>
<h2>intro</h2>
<p>...</p>
<pre>(f-filename-bookmark1)=</pre>
<h1>Heading1</h1>
<p>xxx</p>
<pre>(f-filename-bookmark2)=</pre>
<pre>(f-filename-bookmark3)=</pre>
<h1>Heading2</h1>
<p>yyy</p>
"""
bookmarked_with_into_expected_split = [
    """
<p>Don't forget about me</p>
<pre>(f-filename-bookmark-to-h2)=</pre>
<h2>intro</h2>
<p>...</p>
""",
    """<pre>(f-filename-bookmark1)=</pre>
<h1>Heading1</h1>
<p>xxx</p>
""",
    """
<pre>(f-filename-bookmark2)=</pre>
<pre>(f-filename-bookmark3)=</pre>
<h1>Heading2</h1>
<p>yyy</p>
""",
]


@pytest.mark.parametrize(
    "input_html, expected",
    [
        (basic_input_html, basic_expected_split),
        (complex_input_html, complex_expected_split),
        (no_h1_input_html, no_h1_expected_split),
        # TODO: remove duplicated <pre> tags and restore tests
        # (bookmarked_input_html, bookmarked_expected_split),
        # (bookmarked_with_into_input_html, bookmarked_with_into_expected_split),
    ],
)
def test_split(input_html: str, expected: list[str]):
    html_soup = convert_to_bs(input_html)
    frontmatter = FrontmatterBlob({"split": "True"})
    html_soups = split_docx_into_multiple_chapters(html_soup, frontmatter)
    for i in range(len(expected)):
        print("=" * 50)
        print(html_soups[i])
        print("-" * 50)
        print(expected[i])
    print("#" * 75)
    assert len(html_soups) == len(expected)
    for i in range(len(expected)):
        print("=" * 50)
        print(html_soups[i])
        print("-" * 50)
        print(expected[i])
        assert _html_equal(html_soups[i], convert_to_bs(expected[i]))
