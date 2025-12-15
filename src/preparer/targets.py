import bs4
import docutils.nodes
import re
import secrets
import string
import typing as t
import xxhash

from src._common.constants import (
    CLS_CAPTION,
    CLS_DIGITAL_ONLY,
    CLS_PAPER_ONLY,
    REF_PREFIX,
)
from src._common.metadata import (
    DocumentMetadata,
)
from src._common.models import Chapter, Heading, RefTarget, Target
from src._common.keys import KeyPath
from src._common.state import DocumentState


# NOTE
# Note targets are handled only for the digital version.
# Hence, if a link leads to `path.md#some-id`, in case of splitting docx into multiple md,
# the path.md might exist only in the digital version.


def is_header(tag: bs4.element.Tag) -> bool:
    return bool(re.match(r"^h[1-6]$", tag.name))


def is_caption(tag: bs4.element.Tag) -> bool:
    return bool(tag.name == "p" and CLS_CAPTION in tag.attrs.get("class", []))


def prepare_ref_targets_in_headers(
    html_soup: bs4.BeautifulSoup,
    metadata: DocumentMetadata,  # TODO: remove metadata
    docstate: DocumentState,
    headers: list[bs4.Tag],
) -> bs4.BeautifulSoup:
    """
    Iterate over header tags and, if there is an anchor tag,
    add a target label before each element. The label is the hash of the element.
    For example, the following html in '01_a.md' file:
        <h2>Heading</h2>
    becomes:
        <pre>(35110f86aeaa2f35)=</pre>
        <h2>Heading</h2>
    In addition, the function registers a Target and Heading objects.
    """
    chapter: Chapter | None = docstate.first("chapters")
    assert (
        docstate.len("chapters") == 1
    ), "Expected docstate to have exactly one chapter"
    # chapter = docstate.get("chapters", attrib="fm_key", val=docstate.key)
    assert chapter is not None, "Expected to find a Chapter in the docstate"
    src_key = chapter.fm_key if chapter else None
    jb_key = chapter.jb_key if chapter else None

    heading_count = 0
    for h_tag in headers:
        # anchors: list[bs4.Tag] = []
        # target_label = ""
        # print("hash(tag)", hash(h_tag), h_tag)
        # target_hash = hash(h_tag)
        # target_label = str(target_hash) if target_hash >= 0 else str(target_hash * -1)

        str_h_tag = str(h_tag)
        target_label = _hash_html(str_h_tag)
        # print('_hash_html("<h2>Heading</h2>")', _hash_html("<h2>Heading</h2>"))
        anchors: bs4.ResultSet[bs4.Tag] = h_tag.find_all("a", id=True)
        if anchors:
            target_tag = _create_pre_elem_for_target_label(html_soup, target_label)
            is_digital, is_paper = _get_isdigital_and_ispaper(h_tag, "")
            h_tag.insert_before(target_tag)
            targetdata = Target(
                loc=docstate.key,  # TODO: maybe path in _JB dir?
                hash=target_label,  # 16-char hex string
                html=str_h_tag,
                text=h_tag.text,  # 'Heading'
                elem=str_h_tag,
                item_type="heading",
                is_digital=is_digital,
                is_paper=is_paper,
                fm_key=src_key,
                prefix="",
                file_count=metadata.get_chapter_number(),  # 1 # TODO: get from somewhere else
                prev_item_num=None,
            )
            docstate.add(targetdata)

        # for child in h_tag.children:
        #     if isinstance(child, bs4.Tag) and child.name == "a":
        #         is_digital, is_paper = _get_isdigital_and_ispaper(h_tag, "")
        #         target_label = _get_target_label(docstate.key, child)
        #         # target_tag = _create_pre_elem_for_target_label(html_soup, target_label)
        #         # print("hash(child)", hash(child), child)
        #         h_tag.insert_before(target_tag)
        #         anchors.append(child)
        #         targetdata = Target(
        #             loc=docstate.key,
        #             pk=target_label,  # 'f-01-a-heading'
        #             html=str(h_tag),
        #             text=h_tag.text,  # 'Heading'
        #             elem=str(h_tag),
        #             item_type="heading",
        #             is_digital=is_digital,
        #             is_paper=is_paper,
        #             filename=docstate.key.name if docstate.key else None,
        #             fragment=child.get("id"),  # '_Heading'
        #             prefix="",
        #             file_count=metadata.get_chapter_number(),  # 1 # TODO: get from somewhere else
        #             prev_item_num=None,
        #         )
        #         docstate.add(targetdata)
        h_lvl = "".join(ch for ch in h_tag.name if ch.isdigit())
        heading_count += 1
        # Since not every Heading has an anchor tag, not every Heading creates a Target.
        headingdata: Heading = Heading(
            loc=docstate.key,
            slug=docstate.metadata.slug,
            file_name=docstate.key.name if docstate.key else "",  # 1
            h_num=heading_count,  # 2
            text=h_tag.text,  # 'Heading'
            target=target_label,  # 'f-01-a-a-heading'
            word_count=metadata.word_count,  # 258
            char_count=metadata.char_count,  # 1039
            level=h_lvl,  # 2
            elem=str(h_tag),
        )
        docstate.add(headingdata)
        # for a in anchors:
        #     a.extract()

        # register RefTargets, same for headings and captions
        for a_tag in anchors:
            processed_href = _process_href(docstate.key, a_tag)
            fragment = _get_fragment_from_anchor_id(a_tag)
            ref_target = RefTarget(
                loc=docstate.key,
                target_id=target_label,
                proc_href=processed_href,
                fm_key=src_key,
                jb_key=jb_key,
                fragment=fragment,
            )
            docstate.add(ref_target)
        # remove anchor tags from the header
        for a_tag in anchors:
            a_tag.extract()
    return html_soup


def prepare_ref_targets_in_captions(
    html_soup: bs4.BeautifulSoup,
    metadata: DocumentMetadata,
    docstate: DocumentState,
    captions: list[bs4.Tag],
) -> bs4.BeautifulSoup:
    """
    Iterate over captions, register a Target and Substitution objects,
    add a substitution placeholder to be replaced with desired value at later stages.

    A) Example caption in "02_b.docx" file, referenced via a bookmark "tblSimpleTable"
    and a cross-reference (hence automatic reference "_Ref177053494"):
        <p class="dgt-mon-caption">
        <a id="_Ref177053494"></a>
        <a id="tblSimpleTable"></a>
        <strong>Table <data value=" SEQ Table \* ARABIC ">1</data>:</strong>
        Table.
        </p>
    This function makes it into:
        <pre>(f-02-b-ref177053494)=</pre>
        <pre>(f-02-b-tblsimpletable)=</pre>
        <p class="dgt-mon-caption">
        <strong>Table {{ f02bref177053494 }}:</strong>
        Table.
        </p>
    (note only first target label is used for substitution id).
    After html2md conversion, we want to have:
        (f-02-b-ref177053494)=
        (f-02-b-tblsimpletable)=
        **Table {{ f02bref177053494 }}:** Table.

    B) Example caption in "00_index.docx" file, to which no reference is pointing to:
        <p class="dgt-mon-caption">
        <strong>Table <data value=" SEQ Table \* ARABIC ">1</data>:</strong>
        A sample table.
        </p>
    This function makes it into:
        <pre>(f-00-index-unref341190179)=</pre>
        <p class="dgt-mon-caption">
        <strong>Table {{ f00indexunref341190179 }}:</strong> A sample table.
        </p>
    After html2md conversion, we want to have:
        (f-00-index-unref341190179)=
        **Table {{ f00indexunref341190179 }}:** A sample table.
    """
    # print(
    #     '\n\n\n\ndocstate.__dict__["chapters"]',
    #     docstate.__dict__["chapters"],
    #     "\n\n\n\n",
    # )
    chapter: Chapter | None = docstate.first("chapters")
    assert (
        docstate.len("chapters") == 1
    ), "Expected docstate to have exactly one chapter"
    # chapter = docstate.get("chapters", attrib="fm_key", val=docstate.key)
    assert chapter is not None, "Expected to find a Chapter in the docstate"
    src_key = chapter.fm_key if chapter else None
    jb_key = chapter.jb_key if chapter else None
    # print(f"src_key: {src_key}, jb_key: {jb_key}")
    # assert src_key is not None, "Expected chapter to have fm_key"
    # assert jb_key is not None, "Expected chapter to have jb_key"

    for caption in captions:
        anchors = _extract_anchor_tags(html_soup, caption)
        caption_as_str = str(caption)
        caption_hash = _hash_html(caption_as_str)
        unique_id = []
        ref_stack = []

        def _replace_data_tag(
            tag: bs4.PageElement,
            prev: t.Optional[bs4.PageElement],
            sep: str,
            # a_id: str,
            # caption_hash: str,
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
            if not isinstance(tag, bs4.Tag):
                return
            for child in tag.children:
                if (
                    isinstance(child, bs4.Tag)
                    and child.name == "data"
                    and not ref_stack
                ):
                    # handle 1-st <data> tag
                    OLD_SUBST_HANDLING = """
                    # TODO: instead of passing a_id, pass processed escaped_id
                    # e.g. f05conditionalrenderingref193102947
                    # instead of f-05-conditional-rendering-ref193102947
                    escaped_id = (
                        a_id.replace("-", "")
                        .replace(".", "")
                        .replace("#", "")
                        .replace("_", "")
                    )  # f05conditionalrenderingref193102947
                    child.replace_with("{{ %s }}" % escaped_id)
                    unique_id.append(escaped_id)
                    """
                    child.replace_with("{{ %s }}" % caption_hash)
                    # unique_id.append(caption_hash)
                    sep = ""
                    ref_stack.append(child)
                elif isinstance(child, bs4.Tag) and child.name == "data":
                    # handle non-first <data> tag
                    if len(sep) > 0 and len(sep) < 3:
                        prev.extract()
                        ref_stack.append(sep)
                    ref_stack.append(child)
                    child.extract()
                elif isinstance(prev, bs4.Tag) and prev.name == "data":
                    sep += child.string
                prev = child
                _replace_data_tag(child, prev, sep)
                # _replace_data_tag(child, prev, sep, caption_hash)

        # first_anchor_label = _get_target_label(docstate.key, anchors[0])

        # _replace_data_tag(caption, None, "", caption_hash)
        _replace_data_tag(caption, None, "")
        if anchors:
            is_digital, is_paper = _get_isdigital_and_ispaper(caption, caption_hash)
            seq = parse_ref_stack(ref_stack)
            target = Target(
                loc=docstate.key,
                hash=caption_hash,
                html=seq["html"],
                text=seq["plain_text_num"],  # calc from ref_stack
                elem=caption_as_str,
                item_type=seq["item_type"],
                is_digital=is_digital,  # calc from caption and identifier
                is_paper=is_paper,  # calc from caption and identifier
                fm_key=src_key,
                file_count=metadata.get_chapter_number(),  # TODO: get from somewhere else
                prefix=seq["prefix"],  # calc from ref_stack
                prev_item_num=seq["prev_item_num"],  # calc from ref_stack
            )
            docstate.add(target)
            # if anchors and docstate.get("substitutions", caption_hash) is None:
            # TODO: consider target_fn=s3_key just in case some fn are duplicated
            # in nested file structure, e.g. index.docx and chapter1/index.docx
            # target_fn = docstate.key.name if docstate.key else None
            # metadata.add_substitution(
            #     SubstitutionDatapoint(
            #         # pk=unique_id[
            #         #     0
            #         # ],  # why substitution pk is different from target pk?
            #         # pk=caption_hash,
            #         was=target.text,
            #         placeholder=target.pk,
            #         item_type=target.item_type,
            #         is_digital=is_digital,
            #         is_paper=is_paper,
            #         file_count=metadata.get_chapter_number(),
            #         location=metadata.filepath,
            #         target_fn=target_fn,
            #         prefix=target.prefix,
            #         prev_item_num=target.prev_item_num,
            #     )
            # )
            # TODO: consider if a Substitution and Target can be the same object?
            # subst: Substitution = Substitution(
            #     hash=caption_hash,
            #     loc=docstate.key,
            #     was=target.text,
            #     placeholder=target.hash,
            #     item_type=target.item_type,
            #     is_digital=is_digital,
            #     is_paper=is_paper,
            #     file_count=metadata.get_chapter_number(),
            #     location=metadata.filepath,
            #     target_fn=target_fn,
            #     prefix=target.prefix,
            #     prev_item_num=target.prev_item_num,
            # )
            # print("Substitution", subst.model_dump())
            # docstate.add(subst)
        # register RefTargets, same for headings and captions
        for a_tag in anchors:
            processed_href = _process_href(docstate.key, a_tag)
            fragment = _get_fragment_from_anchor_id(a_tag)
            ref_target = RefTarget(
                loc=docstate.key,
                target_id=caption_hash,
                proc_href=processed_href,
                fm_key=src_key,
                jb_key=jb_key,
                fragment=fragment,
            )
            docstate.add(ref_target)
        target_tag = _create_pre_elem_for_target_label(html_soup, caption_hash)
        try:
            caption.insert_before(target_tag)
        except ValueError:
            caption.insert(0, target_tag)

        OLD_SUBST_HANDLING_2 = """
        for a in anchors:
            # anchor_label = _get_target_label(docstate.key, a)  # f-05-conditional-rendering-ref193102947
            anchor_label = _get_target_label(
                docstate.key, a
            )  # f-05-conditional-rendering-ref193102947
            identifier = (
                anchor_label.replace("-", "") if not unique_id else unique_id[0]
            )  # f05conditionalrenderingref193102947
            is_digital, is_paper = _get_isdigital_and_ispaper(caption, identifier)
            seq = parse_ref_stack(ref_stack)
            target = TargetDatapoint(
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
            metadata.add_target(target)
            ntarget = Target(
                loc=docstate.key,
                pk=anchor_label,
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
            docstate.add(ntarget)
            if unique_id and docstate.get("substitutions", unique_id[0]) is None:
                target_fn = docstate.key.name if docstate.key else None
                metadata.add_substitution(
                    SubstitutionDatapoint(
                        pk=unique_id[
                            0
                        ],  # why substitution pk is different from target pk?
                        was=target.text,
                        placeholder=target.pk,
                        item_type=target.item_type,
                        is_digital=is_digital,
                        is_paper=is_paper,
                        file_count=metadata.get_chapter_number(),
                        location=metadata.filepath,
                        target_fn=target_fn,
                        prefix=target.prefix,
                        prev_item_num=target.prev_item_num,
                    )
                )
                subst: Substitution = Substitution(
                    loc=docstate.key,
                    pk=unique_id[0],
                    was=target.text,
                    placeholder=target.pk,
                    item_type=target.item_type,
                    is_digital=is_digital,
                    is_paper=is_paper,
                    file_count=metadata.get_chapter_number(),
                    location=metadata.filepath,
                    target_fn=target_fn,
                    prefix=target.prefix,
                    prev_item_num=target.prev_item_num,
                )
                docstate.add(subst)

            target_tag = _create_pre_elem_for_target_label(html_soup, anchor_label)
            try:
                caption.insert_before(target_tag)
            except ValueError:
                caption.insert(0, target_tag)
        """
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


def _process_href(curr_key: KeyPath, elem: bs4.Tag) -> str:
    """
    If we have `<a id="_Heading"></a>` in `01_a.md` file, the return value is
    `f-01-a-heading`.

    Where
        `f` is a prefix, needed so that label doesn't start with a number,
        `01-a` is slugified name of the current file where a target is placed,
        `heading` is slugified id from <a> tag.
    """
    path = curr_key.stem
    tag_id = elem.get("id", "").replace("_", "-")
    assert tag_id, "Unknown situation where <a> tag has no id attribute"
    fragment_before_slugification = f"{REF_PREFIX}-{path}-{tag_id}"
    return docutils.nodes.make_id(fragment_before_slugification)


def _get_fragment_from_anchor_id(a_tag: bs4.Tag) -> str:
    """
    Given an anchor tag id like `<a id="_Ref193102947"></a>` or `<a id="a_Heading"></a>`,
    return the fragment identifier, e.g. `ref193102947` or `a-heading`.
    Make sure fragment slugification is consistent with reference preparation.
    """
    tag_id = a_tag.get("id", "")
    assert tag_id, "Unknown situation where <a> tag has no id attribute"
    return tag_id  # maybe slugification is not needed since we are using hash as id anyway?
    # return docutils.nodes.make_id(tag_id)


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


class IRefStack(t.TypedDict):
    html: str
    plain_text_num: str
    prefix: str
    prev_item_num: int | None
    item_type: str


def parse_ref_stack(
    ref_stack: list[bs4.PageElement],
) -> IRefStack:
    res = {
        "html": "",
        "plain_text_num": "",
        "item_type": "",
        "prefix": "",
        "prev_item_num": None,
    }
    for elem in ref_stack:
        res["html"] += str(elem)
        res["plain_text_num"] += elem.string if hasattr(elem, "string") else str(elem)
        if isinstance(elem, bs4.element.NavigableString) or isinstance(elem, str):
            res["prefix"] += elem.strip()
        elif not isinstance(elem, bs4.element.Tag):
            pass
        elif "SEQ " in elem.get("value", "").upper():
            """
            SEQ denotes describes sequential numbers of chapters, tables, figures,
            and other user-defined lists of items in a document.
            See ECMA-376 17.16.5.56 for more details.

            Alternatively, I could parse the value to get other useful information,
            like item type. However, parsing OOXML syntax seems full of unnecessary
            edge cases.
            """
            text = elem.text.strip().upper()
            if _is_roman_numeral(text):
                res["prev_item_num"] = _roman_to_int(text)
            elif text.isdigit():
                res["prev_item_num"] = int(text)
            elif text.isalpha() and len(text) == 1:
                res["prev_item_num"] = string.ascii_uppercase.index(text) + 1
            else:
                raise NotImplementedError(
                    f"Alphabet sequential numbering is not implemented for "
                    "numbers bigger than 26. Text: {text}"
                )

            for w in elem.get("value", "").split():
                word = w.lower()
                if word in ["equation", "figure", "table"]:
                    res["item_type"] = word
        elif "STYLEREF " in elem.get("value", ""):
            r"""
            STYLEREF inserts the nearest text that is formatted by the style
            whose name is specified by the argument. In most cases, it the search goes
            backwards. Commonly used with "\s" field argument, which includes a case
            or section number. E.g. ` STYLEREF 1 \s ` inserts the number of the previous
            Heading1 styled text.
            See ECMA-376 17.16.5.59 for more details.
            """
            res["prefix"] += elem.text
        else:
            res["prev_item_num"] = None
    return res


def _is_roman_numeral(text: str) -> bool:
    roman_num_chars = ["I", "V", "X", "L", "C", "D", "M"]
    if not text:
        return False
    for ch in text:
        if ch not in roman_num_chars:
            return False
    return True


def _roman_to_int(text: str) -> int:
    nums = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    res = 0
    for i in range(len(text)):
        if text[i] in nums:
            if i + 1 < len(text) and nums[text[i]] < nums[text[i + 1]]:
                res -= nums[text[i]]
            else:
                res += nums[text[i]]
    return res


def _hash_html(html_elem: str | bs4.PageElement, seed: int = 0) -> str:
    """
    Returns 16-char hex lowercase string using 64-bit arithmetic operation.
    For example, for string "<h2>Heading</h2>" it returns "35110f86aeaa2f35".
    """
    if isinstance(html_elem, bs4.PageElement):
        html_elem = str(html_elem)
    return xxhash.xxh64(html_elem, seed=seed).hexdigest()
