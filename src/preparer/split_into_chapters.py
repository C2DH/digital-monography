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
    h1s = html_soup.find_all("h1")

    #######################################################
    # Include everything before the first <h1> as the first group.
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
    # print("&" * 75)
    # print("&" * 75)

    ##################
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
    for i, h1 in enumerate(h1s):

        # determine end boundary: next h1 or None
        next_h1 = h1s[i + 1] if i + 1 < len(h1s) else None

        # collect nodes that belong to this group
        nodes = []

        # First, capture any preceding consecutive <pre> siblings immediately before this h1.
        # Walk backwards through previous_sibling while siblings are <pre> (and possibly whitespace text nodes).
        prev = h1.previous_sibling
        # Collect candidate <pre> elements in reverse order then reverse at the end
        pre_stack = []
        while prev is not None:
            # skip pure-whitespace text nodes and comments between elements
            if isinstance(prev, bs4.NavigableString) and prev.string.strip() == "":
                pre_stack.append(prev)
                prev = prev.previous_sibling
                continue
            if isinstance(prev, bs4.Comment):
                prev = prev.previous_sibling
                continue
            if isinstance(prev, bs4.Tag) and prev.name == "pre":
                pre_stack.append(prev)
                prev = prev.previous_sibling
                continue
            # stop if any non-<pre> element encountered
            break
        # add the collected <pre> tags in document order
        # print("reversed(pre_stack)", list(reversed(pre_stack)))
        nodes.extend(reversed(pre_stack))

        # Now add the h1 itself
        # print(h1)
        nodes.append(h1)
        # print("nodes after adding h1", nodes)

        # Then add all following siblings until (but not including) next_h1
        cur = h1.next_sibling
        while cur is not None and cur is not next_h1:
            # include everything (tags, strings, comments)
            nodes.append(cur)
            cur = cur.next_sibling

            # TODO: Remove trailing <pre> tags from each group, otherwise
            # we have duplicates.

        # Build a new BeautifulSoup object containing these nodes
        fragment_html = "".join(str(n) for n in nodes)
        groups.append(bs4.BeautifulSoup(fragment_html, "html.parser"))

    return groups
