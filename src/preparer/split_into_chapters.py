import bs4

from frontmatter import FrontmatterBlob


def split_docx_into_multiple_chapters(
    html_soup: bs4.BeautifulSoup, frontmatter: FrontmatterBlob | None
) -> list[bs4.BeautifulSoup]:
    """
    Split the HTML document into multiple chapters based on <h1> tags.
    """
    if frontmatter is None or frontmatter.should_be_splitted is False:
        return [html_soup]
    html_soups = []
    current_bs = None
    for elem in html_soup.contents:
        if current_bs is None:
            current_bs = bs4.BeautifulSoup("", "html.parser")
            html_soups.append(current_bs)
        elif isinstance(elem, bs4.Tag) and elem.name == "h1" and elem.text.strip():
            if not current_bs.contents:
                # include the first <h1> tag
                current_bs.append(elem.__copy__())
            else:
                # current_bs has content before the first <h1> tag
                current_bs = bs4.BeautifulSoup("", "html.parser")
                current_bs.append(elem.__copy__())
                html_soups.append(current_bs)
        else:
            # append non-<h1> node to a current chapter
            current_bs.append(elem.__copy__())
    return html_soups
