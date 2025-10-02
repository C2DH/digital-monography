# import bs4

# from src.preparer.refs_rewrite import (
#     is_caption,
#     is_header,
#     is_footnote,
#     is_reference,
#     prepare_references,
# )

# # from src._common.metadata import DocumentMetadata, TargetDatapoint
# from src._common.keys import KeyPath
# from src._common.state import DocumentState
# from src._common.models import Ref, Target


# def test_refs_and_targets():
#     sample_html = (
#         # '<!-- targets -->'
#         '<h1><a id="_Heading"></a><a id="heading_2"></a>Heading</h1>'
#         "<h2>Heading level 2</h2>"
#         '<h3><a id="heading_3"></a>Heading level 3</h3>'
#         # '<!-- references -->'
#         '<p>A <a href="#_Heading">link</a>.</p>'
#         '<p>B <a href="other_file.docx#_Heading">link</a>.</p>'
#     )
#     bs = bs4.BeautifulSoup(sample_html, "html.parser")
#     key = KeyPath("slug/01_file.docx")
#     docstate = DocumentState(key)
#     # metadata = DocumentMetadata(key)
#     # headers = [node for node in bs.children if is_header(node)]
#     references = []
#     classifiers = [
#         (is_reference, references),
#     ]
#     for node in bs.descendants:
#         for check_if_meets_criteria, container in classifiers:
#             if isinstance(node, bs4.element.Tag) and check_if_meets_criteria(node):
#                 container.append(node)
#     # bs = prepare_references(bs, docstate, references)
#     print("docstate.__dict__[docstate]", docstate.__dict__[docstate])
#     target = docstate.get("targets", "f-01-a-a-heading")
#     # check if substitution happened in the html
#     assert 1 == 666


# # def test_target_as_a_user_placed_bookmark(self):
# #     target: Target = self.bookstate[self.fp_a.stem].get(
# #         "targets", "f-01-a-a-heading"
# #     )
# #     assert target
# #     assert target.text == "Heading"
# #     assert target.is_digital == True
# #     assert target.is_paper == True
# #     assert target.filename == "01_a.docx"
# #     assert target.fragment == "a_heading"
# #     assert target.item_type == "heading"
# #     assert target.prefix == ""
# #     assert target.prev_item_num == None
