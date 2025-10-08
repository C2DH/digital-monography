import secrets
import string
import bs4
import docutils.nodes
import typing as t

from src._common.constants import (
    CLS_DIGITAL_ONLY,
    CLS_PAPER_ONLY,
)
from src._common.metadata import (
    DocumentMetadata,
)
from src._common.models import Heading, Substitution, Target
from src._common.metadata import SubstitutionDatapoint, TargetDatapoint
from src._common.keys import KeyPath
from src._common.state import DocumentState


def prepare_ref_targets_in_headers(
    html_soup: bs4.BeautifulSoup,
    metadata: DocumentMetadata,  # TODO: remove metadata
    docstate: DocumentState,
    headers: list[bs4.Tag],
) -> bs4.BeautifulSoup:
    """
    Note targets are handled only for the digital version.
    Hence, if a link leads to `path.md#some-id`, in case of splitting docx into multiple md,
    the path.md might exist only in the digital version.
    """
    heading_count = 0
    for tag in headers:
        anchors: list[bs4.Tag] = []
        target_label = ""
        for child in tag.children:
            if isinstance(child, bs4.Tag) and child.name == "a":
                is_digital, is_paper = _get_isdigital_and_ispaper(tag, "")
                target_label = _get_target_label(docstate.key, child)
                target_tag = _create_pre_elem_for_target_label(html_soup, target_label)
                tag.insert_before(target_tag)
                anchors.append(child)
                targetdata = Target(
                    loc=docstate.key,
                    pk=target_label,  # 'f-01-a-heading'
                    html=str(tag),
                    text=tag.text,  # 'Heading'
                    elem=str(tag),
                    item_type="heading",
                    is_digital=is_digital,
                    is_paper=is_paper,
                    filename=docstate.key.name if docstate.key else None,
                    fragment=child.get("id"),  # '_Heading'
                    prefix="",
                    file_count=metadata.get_chapter_number(),  # 1 # TODO: get from somewhere else
                    prev_item_num=None,
                )
                # print("add_target", targetdata.model_dump())
                docstate.add(targetdata)
        h_lvl = "".join(ch for ch in tag.name if ch.isdigit())
        heading_count += 1
        hdata: Heading = Heading(
            loc=docstate.key,
            slug=docstate.metadata.slug,
            file_name=docstate.key.name if docstate.key else "",  # 1
            h_num=heading_count,  # 2
            text=tag.text,  # 'Heading'
            target=target_label,  # 'f-01-a-a-heading'
            word_count=metadata.word_count,  # 258
            char_count=metadata.char_count,  # 1039
            level=h_lvl,  # 2
            elem=str(tag),
        )
        docstate.add(hdata)
        for a in anchors:
            a.extract()
    return html_soup


def prepare_ref_targets_in_captions(
    html_soup: bs4.BeautifulSoup,
    metadata: DocumentMetadata,
    docstate: DocumentState,
    captions: list[bs4.Tag],
) -> bs4.BeautifulSoup:
    """
    Iterate over captions.
    """
    for caption in captions:
        print("=" * 75)
        print("caption", caption)
        """
        <p class="dgt-mon-caption">
        <a id="_Ref193102947"></a>
        <a id="figForDigital"></a>
        <strong>
        <span class="dgt-mon-digital-only">Figure <data value=" SEQ Figure \* ARABIC ">1</data>:</span>
        </strong>
        <span class="dgt-mon-digital-only"> Drawing of an orange by Franz Eugen Köhler, 1887.</span>
        </p>
        """
        anchors = _extract_anchor_tags(html_soup, caption)
        print(
            "anchors", anchors
        )  # [<a id="_Ref193102947"></a>, <a id="figForDigital"></a>]
        # item_type = _get_item_type(caption)
        unique_id = []
        ref_stack = []

        def _replace_data_tag(
            tag: bs4.PageElement,
            prev: t.Optional[bs4.PageElement],
            sep: str,
            a_id: str,
        ) -> None:
            """
            Imagine we have a complex caption like this:
                Equation I.A: Text.
            e.g.
            <p class="dgt-mon-caption">
                <a id="equationWithComplexNumbering"></a>
                <strong>Equation
                <data value=" STYLEREF 1 \s ">I</data>
                .
                <data value=" SEQ Equation \* ALPHABETIC \s 1 ">A</data>
                :
                </strong>
                Caption with chapter number and non-digit item number.
            </p>
            In the output markdown, we want to have:
                ```
                Equation {{ f01aequationwithcomplexnumbering }}:
                Caption with chapter number and non-digit item number.
                ```

            So we recurse over the caption's elements to replace bookmarks,
            extract information from `<data value=" SEQ Figure \\* ARABIC ">1</data>`,
            replace first data tag with substitution id, remove other data tags.
            """
            # if not hasattr(tag, "children"):
            #     return
            if not isinstance(tag, bs4.Tag):
                return
            # assert hasattr(tag, "children"), "Every bs4.Tag has children"
            for child in tag.children:
                print("-" * 75)
                # if not isinstance(child, bs4.Tag):
                #     continue
                # if not hasattr(child, "name"):
                #     continue
                if (
                    isinstance(child, bs4.Tag)
                    and child.name == "data"
                    and not ref_stack
                ):
                    print(
                        "1-st data tag", child
                    )  # <data value=" SEQ Figure \* ARABIC ">1</data>
                    # handle 1-st <data> tag
                    # TODO: instead of passing a_id, pass processed escaped_id
                    # e.g. f05conditionalrenderingref193102947
                    # instead of f-05-conditional-rendering-ref193102947
                    escaped_id = (
                        a_id.replace("-", "")
                        .replace(".", "")
                        .replace("#", "")
                        .replace("_", "")
                    )
                    print(
                        "escaped_id", escaped_id
                    )  # f05conditionalrenderingref193102947
                    child.replace_with("{{ %s }}" % escaped_id)
                    unique_id.append(escaped_id)
                    sep = ""
                    ref_stack.append(child)
                elif isinstance(child, bs4.Tag) and child.name == "data":
                    print("n-th data tag", child)
                    # handle separator
                    if len(sep) > 0 and len(sep) < 3:
                        prev.extract()
                        ref_stack.append(sep)
                    # handle n-th <data> tag to the stack
                    ref_stack.append(child)
                    child.extract()
                elif isinstance(prev, bs4.Tag) and prev.name == "data":
                    # elif prev and prev.name == "data":
                    print("after data tag", child)
                    sep += child.string
                prev = child
                print("prev", prev)
                _replace_data_tag(child, prev, sep, a_id)
                print("-" * 75)

        first_anchor_label = _get_target_label(docstate.key, anchors[0])
        # link = LinkMystifier()
        # we init LinkMystifier for each caption and for each <a> tag inside the caption
        # for caption we input current file and first <a> tag id
        # and get out link.id == fragment == f-05-conditional-rendering-ref193102947
        # link.set_filepath(metadata.filepath)
        # print('anchors[0]["id"]', anchors[0]["id"])  # _Ref193102947
        # link.set_from_id(anchors[0]["id"])
        # print("link.id", link.id)  # f-05-conditional-rendering-ref193102947
        _replace_data_tag(caption, None, "", first_anchor_label)
        # _replace_data_tag(caption, None, "", link.id)

        # TODO: maybe there should be some id for the caption
        # to group bookmarks that relate to the same object
        # breakpoint()
        for a in anchors:
            print("." * 75)
            print("a", a)  # <a id="_Ref193102947"></a>

            anchor_label = _get_target_label(docstate.key, a)
            # link = LinkMystifier()
            # link.set_filepath(metadata.filepath)
            # LinkMystifier gets current file and id from <a> tag
            # it generates:
            #  * id == fragment
            #  * identifier == id without special chars
            #  * (fragment)=
            # print('a["id"]', a["id"])  # _Ref193102947
            # link.set_from_id(a["id"])
            # print("link.id", link.id)  # f-05-conditional-rendering-ref193102947
            # identifier = link.id.replace("-", "") if not unique_id else unique_id[0]
            identifier = (
                anchor_label.replace("-", "") if not unique_id else unique_id[0]
            )
            print("identifier", identifier)  # f05conditionalrenderingref193102947
            is_digital, is_paper = _get_isdigital_and_ispaper(caption, identifier)
            # plain_text_num = _get_plain_text_numbering(ref_stack)

            # print("metadata.filepath", metadata.filepath)
            # print('a["id"]', a["id"])
            # print("caption", caption)
            # # print("link.FRAGMENT????", link)
            # print("-" * 50)

            seq = TargetDatapoint.parse_ref_stack(ref_stack)
            print("seq", seq)
            target = TargetDatapoint(
                # html="".join(str(elem) for elem in ref_stack),
                # pk=link.id,
                pk=anchor_label,
                html=seq["html"],
                text=seq["plain_text_num"],  # calc from ref_stack
                elem=str(caption),
                item_type=seq["item_type"],
                is_digital=is_digital,  # calc from caption and identifier
                is_paper=is_paper,  # calc from caption and identifier
                filename=metadata.filepath.name if metadata.filepath else None,
                fragment=a["id"],
                file_count=metadata.get_chapter_number(),
                prefix=seq["prefix"],  # calc from ref_stack
                prev_item_num=seq["prev_item_num"],  # calc from ref_stack
            )
            print("TargetDatapoint", target)
            metadata.add_target(target)
            ntarget = Target(
                # html="".join(str(elem) for elem in ref_stack),
                loc=docstate.key,
                pk=anchor_label,
                # pk=link.id,
                html=seq["html"],
                text=seq["plain_text_num"],  # calc from ref_stack
                elem=str(caption),
                item_type=seq["item_type"],
                is_digital=is_digital,  # calc from caption and identifier
                is_paper=is_paper,  # calc from caption and identifier
                filename=docstate.key.name if docstate.key else None,
                fragment=a["id"],
                file_count=metadata.get_chapter_number(),  # TODO: get from somewhere else
                prefix=seq["prefix"],  # calc from ref_stack
                prev_item_num=seq["prev_item_num"],  # calc from ref_stack
            )
            print("ntarget.model_dump()", ntarget.model_dump())
            targeet_dump = """{
            'pk': 'f-05-conditional-rendering-ref193102947',
            'html': '<data value=" SEQ Figure \\* ARABIC ">1</data>',
            'text': '1',
            'elem': '''<p class="dgt-mon-caption">
                <strong><span class="dgt-mon-digital-only">Figure {{ f05conditionalrenderingref193102947 }}:</span></strong>
                <span class="dgt-mon-digital-only"> Drawing of an orange by Franz Eugen Köhler, 1887.</span>
            </p>''',
            'is_paper': False,
            'is_digital': True,
            'filename': '05_conditional_rendering.md',
            'fragment': '_Ref193102947',
            'item_type': 'figure',
            'file_count': 5,
            'prefix': '',
            'prev_item_num': 1,
            'new_item_num': None,
            'loc': '/tmp/efs/_JB/a_book/05_conditional_rendering.md'
            }"""
            docstate.add(ntarget)
            print("unique_id", unique_id)  # ['f05conditionalrenderingref193102947']
            print("unique_id[0]", unique_id[0])  # f05conditionalrenderingref193102947
            print(
                "metadata.get_substitution(unique_id[0])",
                metadata.get_substitution(unique_id[0]),
            )  # None
            print(
                "docstate.get('substitutions', unique_id[0])",
                docstate.get("substitutions", unique_id[0]),
            )  # None
            # if unique_id and metadata.get_substitution(unique_id[0]) is None:
            if unique_id and docstate.get("substitutions", unique_id[0]) is None:
                target_fn = docstate.key.name if docstate.key else None
                print(
                    "target_fn", target_fn, type(target_fn)
                )  # 05_conditional_rendering.md <class 'str'>
                # assert isinstance(target_fn, str)
                metadata.add_substitution(
                    SubstitutionDatapoint(
                        pk=unique_id[
                            0
                        ],  # why substitution pk is different from target pk?
                        was=target.text,
                        placeholder=target.pk,
                        # placeholder=unique_id[0],
                        # item_type=item_type,
                        item_type=target.item_type,
                        is_digital=is_digital,
                        is_paper=is_paper,
                        file_count=metadata.get_chapter_number(),
                        # new
                        location=metadata.filepath,
                        target_fn=target_fn,
                        prefix=target.prefix,
                        prev_item_num=target.prev_item_num,
                    )
                )
                subst1: Substitution = Substitution(
                    loc=docstate.key,
                    pk=unique_id[0],
                    was=target.text,
                    placeholder=target.pk,
                    # placeholder=unique_id[0],
                    # item_type=item_type,
                    item_type=target.item_type,
                    is_digital=is_digital,
                    is_paper=is_paper,
                    file_count=metadata.get_chapter_number(),
                    # new
                    location=metadata.filepath,
                    target_fn=target_fn,
                    prefix=target.prefix,
                    prev_item_num=target.prev_item_num,
                )
                print("Substitution", subst1.model_dump())
                subst_dump = """{
                'pk': 'f05conditionalrenderingref193102947',
                'was': '1',
                'placeholder': 'f-05-conditional-rendering-ref193102947',
                'is_digital': True,
                'is_paper': False,
                'item_type': 'figure',
                'target_fn': '05_conditional_rendering.md',
                'file_count': 5,
                'prefix': '',
                'prev_item_num': 1,
                'new_item_num': None,
                'fprefix': None,
                'loc': '/tmp/efs/_JB/a_book/05_conditional_rendering.md',
                'location': '/tmp/efs/_JB/a_book/05_conditional_rendering.md'}"""
                docstate.add(subst1)

            target_tag = _create_pre_elem_for_target_label(html_soup, anchor_label)
            # target_tag = html_soup.new_tag("pre")
            # target_tag.string = link.mystify_target()
            print(
                "target_tag.string", target_tag.string
            )  # (f-05-conditional-rendering-ref193102947)=
            print(
                "target_tag", target_tag
            )  # <pre>(f-05-conditional-rendering-ref193102947)=</pre>
            try:
                caption.insert_before(target_tag)
            except ValueError:
                caption.insert(0, target_tag)
    return html_soup


def _get_isdigital_and_ispaper(
    partent_tag: bs4.Tag, identifier: str
) -> tuple[bool, bool]:
    """
    When a user highlights some text with a color set in constants.MAMMOTH_STYLE_MAP,
    mammoth sets an appropriate css class to the outputed html.
    This function iterates over descendant elements looking for the said css classes.
    """
    css_classes = [
        tag.get("class", [])
        for tag in partent_tag.descendants
        if isinstance(tag, bs4.Tag) and (identifier in tag.text)
    ]
    css_classes: list[str] = [item for sublist in css_classes for item in sublist]
    is_digital = is_paper = True
    if CLS_DIGITAL_ONLY in css_classes and CLS_PAPER_ONLY in css_classes:
        is_digital = is_paper = None
    elif CLS_DIGITAL_ONLY in css_classes:
        is_paper = False
    elif CLS_PAPER_ONLY in css_classes:
        is_digital = False
    return is_digital, is_paper


def _get_target_label(curr_key: KeyPath, elem: bs4.Tag) -> str:
    """
    If we have `<a id="_Heading"></a>` in `01_a.md` file, the return value is
    `f-01-a-heading`.

    Where
        `f` is a prefix, needed so that label doesn't start with a number,
        `01-a` is slugified name of the current file where a target is placed,
        `heading` is slugified id from <a> tag.
    """
    prefix = "f"
    path = curr_key.stem
    tag_id = elem.get("id", "").replace("_", "-")
    assert tag_id, "Unknown situation where <a> tag has no id attribute"
    fragment_before_slugification = f"{prefix}-{path}-{tag_id}"
    return docutils.nodes.make_id(fragment_before_slugification)


def _create_pre_elem_for_target_label(
    html_soup: bs4.BeautifulSoup, label: str
) -> bs4.Tag:
    """
    Creates `<pre>(f-file-heading-3)=</pre>` tag.
    This is meant to be inserted just before the targeted html element.
    <pre> tags (preformatted text elements) are meant to be presented exactly as is,
    so they are not processed by html2md converter.
    """
    new_tag = html_soup.new_tag("pre")
    new_tag.string = f"({label})="
    return new_tag


def _extract_anchor_tags(
    html_soup: bs4.BeautifulSoup, caption: bs4.Tag
) -> list[bs4.Tag]:
    """
    Return a list of anchor tags like
        [<a id="_Ref193102947"></a>, <a id="someCustomBookmark"></a>]
    If a caption has no bookmark, return a list with a single autogenerated anchor, e.g.
        [<a id="_Unref723089458">]
    Note that anchors are getting removed (extracted) from the caption.
    In later steps, the contents of anchor tag will be wrapped in an anchor html tag.
    """
    anchors: bs4.ResultSet[bs4.Tag] = caption.find_all("a", id=True)
    if not anchors:
        a = html_soup.new_tag("a")
        a_id = "".join(secrets.choice(string.digits) for i in range(9))
        a["id"] = "_Unref" + a_id
        return [a]
    else:
        for a in anchors:
            a = a.extract()
    return anchors
