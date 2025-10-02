import bs4

from src._common.keys import KeyPath
from src._common.state import DocumentState
from src.preparer.footnotes import (
    is_ref_footnote,
    is_target_footnote,
    prepare_targets_in_footnotes,
    prepare_refs_in_footnotes,
)


def test_preparing_ref_and_target_from_footnote():
    sample_html = (
        '<sup><a href="#footnote-1" id="footnote-ref-1">[1]</a></sup>'
        '<ol><li id="footnote-1">'
        "<p>"
        " Standard footnote without links."
        ' <a href="#footnote-ref-1">↑</a>'
        "</p>"
        "</li></ol>"
    )
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    key = KeyPath("sth/file.docx")
    docstate = DocumentState(key)
    ref_footnotes = []
    target_footnotes = []
    classifiers = [
        (is_ref_footnote, ref_footnotes),
        (is_target_footnote, target_footnotes),
    ]
    for node in bs.descendants:
        for check_if_meets_criteria, container in classifiers:
            if isinstance(node, bs4.element.Tag) and check_if_meets_criteria(node):
                container.append(node)
    bs = prepare_targets_in_footnotes(bs, docstate, target_footnotes)
    bs = prepare_refs_in_footnotes(bs, docstate, ref_footnotes)
    # ref footnote
    sup = bs.find("sup")
    assert sup.a.text == r"[fn-file-1]"
    assert sup.a["href"] == "#footnote-fn-file-1"
    assert sup.a["id"] == "footnote-ref-fn-file-1"
    # target footnote
    li = bs.find("li")
    assert li["id"] == "footnote-fn-file-1"
    a = li.find("a")
    assert a["href"] == "#footnote-ref-fn-file-1"
    # not added to refs nor targets
    assert len(docstate.__dict__.get("refs", [])) == 0
    assert len(docstate.__dict__.get("targets", [])) == 0
