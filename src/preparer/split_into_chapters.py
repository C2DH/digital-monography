import bs4

from prep_frontmatter import FrontmatterBlob


def split_docx_into_multiple_chapters(
    html_soup: bs4.BeautifulSoup, frontmatter: FrontmatterBlob | None
) -> list[bs4.BeautifulSoup]:
    """
    Split the HTML document into multiple chapters based on <h1> tags.
    """
    if frontmatter is None or frontmatter.should_be_splitted is False:
        return [html_soup]
    groups = []
    boundaries = _find_boundaries_where_to_split(html_soup)
    html_before_first_boundary = _extract_content_before_first_boundary(boundaries)
    if html_before_first_boundary.strip():
        groups.append(bs4.BeautifulSoup(html_before_first_boundary, "html.parser"))
    for i, start_bnd in enumerate(boundaries):
        end_bnd = boundaries[i + 1] if i + 1 < len(boundaries) else None
        fragment_html = _extract_content_between_two_boundaries(i, start_bnd, end_bnd)
        groups.append(bs4.BeautifulSoup(fragment_html, "html.parser"))
    return groups


def _find_boundaries_where_to_split(html_soup: bs4.BeautifulSoup) -> list[bs4.Tag]:
    """
    Find the actual boundary tags where to split the document.
    By default, these are the <h1> tags.
    However, if there are <pre> tags (bookmarks) immediately preceding an <h1> tag,
    set the most outer <pre> tag as the boundary.
    """
    h1s: bs4.ResultSet[bs4.Tag] = html_soup.find_all("h1")
    boundaries: list[bs4.Tag] = []
    for h1 in h1s:
        boundary = h1
        prev = h1.previous_sibling
        while prev is not None:
            if isinstance(prev, bs4.NavigableString) and prev.string.strip() == "":
                prev = prev.previous_sibling
                continue
            elif isinstance(prev, bs4.Comment):
                prev = prev.previous_sibling
                continue
            elif isinstance(prev, bs4.Tag) and prev.name == "pre":
                boundary = prev
                prev = prev.previous_sibling
                continue
            else:
                break
        boundaries.append(boundary)
    return boundaries


def _extract_content_before_first_boundary(boundaries: list[bs4.Tag]) -> str:
    """
    Extract all content before the first boundary tag, if such content exists.
    This assumes that boundaries are at the top level of the tree, which
    enables to traverse by siblings.
    So far, this assumption holds true for docx2html output.
    """
    first_boundary = boundaries[0] if boundaries else None
    prev = first_boundary.previous_sibling if first_boundary else None
    prev_nodes = []
    while prev is not None:
        prev_nodes.append(prev)
        prev = prev.previous_sibling
    return "".join(str(n) for n in reversed(prev_nodes))


def _extract_content_between_two_boundaries(
    i: int,
    start_boundary: bs4.Tag,
    end_boundary: bs4.Tag,
) -> str:
    """
    Extract content starting from start_boundary (inclusive) to
    all following nodes until end_boundary (exclusive).
    """
    nodes = []
    nodes.append(start_boundary)
    cur = start_boundary.next_sibling
    while cur is not None and cur is not end_boundary:
        nodes.append(cur)
        cur = cur.next_sibling
    return "".join(str(n) for n in nodes)
