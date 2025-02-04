# import collections
# import pathlib
# from pprint import pprint

# import yaml

# from src.builder.keys import KeyPath
# from src.builder.struct_verifier import StructVerifier
# from src.builder.main import _fromtimestamp

# # from src.verifier.html_verifier import HtmlVerifier
# # from src.verifier.path_handler import PathHandler


# class TestStructBreakingVerificationRules:
#     dirpath = pathlib.Path("examples")

#     @classmethod
#     def setup_class(cls):
#         cls.warnings = collections.defaultdict(list)
#         cls.verifier = StructVerifier()
#         # timestamp = _fromtimestamp("2024-06-26T09:53:49.380Z")
#         # key = KeyPath(cls.dirpath / "_toc.yml")

#     def test_testting(self):
#         key = KeyPath(self.dirpath / "_toc.yml")
#         fp = key.efs_slug_dir / "_config.yml"
#         fp = key.efs_slug_dir / "_toc.yml"
#         print("fp", fp)
#         with open(fp, "r") as f:
#             toc = yaml.safe_load(f)
#         pprint(toc)

#         # toc = self.verifier._get_toc()
#         # pprint(toc)
#         assert 1 == 2
