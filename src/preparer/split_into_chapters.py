import bs4

from frontmatter import FrontmatterBlob


def split_docx_into_multiple_chapters_2(
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
        print("\n> elem", elem)
        print("> current_bs", current_bs, html_soups)
        if current_bs is None:
            current_bs = bs4.BeautifulSoup("", "html.parser")
            html_soups.append(current_bs)
        elif isinstance(elem, bs4.Tag) and elem.name == "h1" and elem.text.strip():
            print(
                'elif isinstance(elem, bs4.Tag) and elem.name == "h1" and elem.text.strip()'
            )
            # Handle <pre> tags (bookmarks) before <h1> elements.
            prevs = []
            prev = elem.previous_element
            while isinstance(prev, bs4.Tag) and prev.name == "pre":
                prevs.append(prev)
                prev = prev.previous_element

            if not current_bs.contents:
                print("if not current_bs.contents")
                # Include the first <h1> tag.
                for pre in prevs:
                    current_bs.append(pre.__copy__())
                current_bs.append(elem.__copy__())
            else:
                print("elif current_bs.contents")
                # current_bs has content before the first <h1> tag.
                current_bs = bs4.BeautifulSoup("", "html.parser")
                for pre in prevs:
                    current_bs.append(pre.__copy__())
                current_bs.append(elem.__copy__())
                html_soups.append(current_bs)
        else:
            print("else")
            # Append non-<h1> node to a current chapter.
            current_bs.append(elem.__copy__())
    return html_soups


def split_docx_into_multiple_chapters(
    html_soup: bs4.BeautifulSoup, frontmatter: FrontmatterBlob | None
) -> list[bs4.BeautifulSoup]:
    """
    Split the HTML document into multiple chapters based on <h1> tags.
    """
    if frontmatter is None or frontmatter.should_be_splitted is False:
        return [html_soup]
    groups = []

    # find all h1 elements in document order
    boundaries = _find_boundaries_where_to_split(html_soup)
    # h1s: bs4.ResultSet[bs4.Tag] = html_soup.find_all("h1")
    # boundaries: list[bs4.Tag] = []
    # for h1 in h1s:
    #     print("*" * 25)
    #     boundary = h1
    #     prev = h1.previous_sibling
    #     while prev is not None:
    #         print("\tboundary", repr(boundary))
    #         if isinstance(prev, bs4.NavigableString) and prev.string.strip() == "":
    #             prev = prev.previous_sibling
    #             continue
    #         elif isinstance(prev, bs4.Comment):
    #             prev = prev.previous_sibling
    #             continue
    #         elif isinstance(prev, bs4.Tag) and prev.name == "pre":
    #             boundary = prev
    #             prev = prev.previous_sibling
    #             continue
    #         else:
    #             print(".. prev", repr(prev), type(prev))
    #             break
    #             # is_directly_before_h1 = False
    #             # prev_nodes.append(prev)
    #             # prev = prev.previous_sibling
    #     print("appending boundary")
    #     boundaries.append(boundary)
    #     print("\tboundaries", boundaries)

    #######################################################
    # Include everything before the first <h1> as the first group.
    include_everything_before_the_first_h1 = """
    first_h1 = h1s[0] if h1s else None
    # print("first_h1", repr(first_h1), type(first_h1))
    prev_nodes = []
    prev = first_h1.previous_sibling if first_h1 else None
    is_directly_before_h1 = True
    while prev is not None:
        # print("-" * 15)
        # print("prev", repr(prev), type(prev))
        if isinstance(prev, bs4.NavigableString) and prev.string.strip() == "":
            # print("whitespace")
            prev_nodes.append(prev)
            prev = prev.previous_sibling
            continue
        elif isinstance(prev, bs4.Comment):
            # print("comment")
            prev_nodes.append(prev)
            prev = prev.previous_sibling
            continue
        elif isinstance(prev, bs4.Tag) and prev.name == "pre" and is_directly_before_h1:
            # print("pre")
            prev = prev.previous_sibling
            continue
        else:
            # print("else")
            is_directly_before_h1 = False
            prev_nodes.append(prev)
            prev = prev.previous_sibling
    # print("last prev", repr(prev), type(prev))

    fragment_html = "".join(str(n) for n in reversed(prev_nodes))
    # print("fragment_html", repr(fragment_html))
    if fragment_html.strip():
        groups.append(bs4.BeautifulSoup(fragment_html, "html.parser"))
    """
    # print("&" * 75)
    # print("&" * 75)

    ##################
    # first_boundary = boundaries[0] if boundaries else None
    # prev = first_boundary.previous_sibling if first_boundary else None
    # prev_nodes = []
    # while prev is not None:
    #     prev_nodes.append(prev)
    #     prev = prev.previous_sibling
    # print("prev_nodes", prev_nodes)
    # fragment_html = "".join(str(n) for n in reversed(prev_nodes))
    # print("fragment_html", repr(fragment_html))
    # if fragment_html.strip():
    #     groups.append(bs4.BeautifulSoup(fragment_html, "html.parser"))

    html_before_first_boundary = _extract_content_before_first_boundary(boundaries)
    if html_before_first_boundary.strip():
        groups.append(bs4.BeautifulSoup(html_before_first_boundary, "html.parser"))

    # for elem in html_soup.contents:
    #     if elem is first_h1:
    #         print("\n\nnodes", nodes, "\n\n")
    #         for i in range(-1, -len(nodes), -1):
    #             # Remove trailing <pre> tags from the initial group.
    #             print("i", i, repr(nodes[i]), type(nodes[i]))
    #             if isinstance(nodes[i], bs4.NavigableString) and nodes[i].strip() == "":
    #                 # Skip if a non-whitespace text node is encountered.
    #                 pass
    #             elif isinstance(nodes[i], bs4.Tag) and nodes[i].name == "pre":
    #                 nodes[i] = ""
    #             else:
    #                 break
    #         break
    #     nodes.append(elem)
    # Build a new BeautifulSoup object containing these nodes.
    # fragment_html = "".join(str(n) for n in nodes)
    # tags = {n.name for n in nodes if isinstance(n, bs4.Tag)}
    # print("tags", tags)
    # print("fragment_html", repr(fragment_html))
    # if fragment_html.strip() and tags != {"pre"}:
    #     groups.append(bs4.BeautifulSoup(fragment_html, "html.parser"))
    #######################################################
    for i, start_boundary in enumerate(boundaries):
        end_boundary = boundaries[i + 1] if i + 1 < len(boundaries) else None
        fragment_html = _extract_content_between_two_boundaries(
            i, start_boundary, end_boundary
        )
        """
        next_boundary = boundaries[i + 1] if i + 1 < len(boundaries) else None
        # collect nodes that belong to this group
        nodes = []
        # Now add the h1 itself
        nodes.append(boundary)
        # Then add all following siblings until (but not including) next_boundary
        cur = boundary.next_sibling
        while cur is not None and cur is not next_boundary:
            # include everything (tags, strings, comments)
            nodes.append(cur)
            cur = cur.next_sibling

        # Build a new BeautifulSoup object containing these nodes
        fragment_html = "".join(str(n) for n in nodes)
        """
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
    # i: int, start_boundary: bs4.Tag, boundaries: list[bs4.Tag]
) -> str:
    # end_boundary = boundaries[i + 1] if i + 1 < len(boundaries) else None
    nodes = []
    nodes.append(start_boundary)
    # Then add all following siblings until (but not including) end_boundary
    cur = start_boundary.next_sibling
    while cur is not None and cur is not end_boundary:
        # include everything (tags, strings, comments)
        nodes.append(cur)
        cur = cur.next_sibling
    return "".join(str(n) for n in nodes)
