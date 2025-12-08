import json
import bs4
import pytest

from src._common.constants import (
    DEFAULT_SFS_DIR,
    CHAPTERS_DIR,
    CLS_STATE_TABLE_JSONDATA,
    INPUT_DIR,
)
from src._common.keys import KeyPath
from src._common.state import DocumentState
from src._common.models import (
    FileService,
    Ref,
    Substitution,
    SubstitutionService,
    Target,
)

# TODO: check _STATE after preparer

_CHAPTERS_DIR = KeyPath(DEFAULT_SFS_DIR) / CHAPTERS_DIR


class TestRefsAndTargetsInHTMLAfterPreparer_MultipleDocsExample:
    key_a = _CHAPTERS_DIR / "a_book" / "01_a.html"
    key_b = _CHAPTERS_DIR / "a_book" / "02_b.html"
    key_cr = _CHAPTERS_DIR / "a_book" / "05_conditional_rendering.html"

    @classmethod
    def setup_class(cls):
        cls.html: dict[KeyPath, bs4.BeautifulSoup] = {}
        cls.docstates: dict[str, DocumentState] = {}
        for key in [cls.key_a, cls.key_b, cls.key_cr]:
            assert key.exists(), f"Expected {key} to exist but it does not."
            with open(key, "r") as f:
                cls.html[key] = bs4.BeautifulSoup(f.read(), "html.parser")
                script_tag = cls.html[key].find(
                    "script", {"class": CLS_STATE_TABLE_JSONDATA}
                )
                docstate = DocumentState(key)
                docstate.from_dict(json.loads(script_tag.string))
                cls.docstates[key.stem] = docstate

    @pytest.mark.parametrize(
        "target_data",
        [
            {
                "stem": "01_a",
                "target_hash": "80e6a4726eb7b446",
                "item_type": "heading",
                "is_digital": True,
                "is_paper": True,
                "file_count": 1,
                "prefix": "",
                "prev_item_num": None,
                "exp_targets_len": 4,
            },
            {
                "stem": "01_a",
                "target_hash": "8edfc0e04a18c2c0",
                "item_type": "figure",
                "is_digital": True,
                "is_paper": True,
                "file_count": 1,
                "prefix": "",
                "prev_item_num": 1,
                "exp_targets_len": 4,
            },
            {
                "stem": "01_a",
                "target_hash": "a4f96fb446ed2877",
                "item_type": "table",
                "is_digital": True,
                "is_paper": True,
                "file_count": 1,
                "prefix": "",
                "prev_item_num": 1,
                "exp_targets_len": 4,
            },
            {
                "stem": "01_a",
                "target_hash": "a375f52f5509ade4",
                "item_type": "equation",
                "is_digital": True,
                "is_paper": True,
                "file_count": 1,
                "prefix": "I.",
                "prev_item_num": 1,
                "exp_targets_len": 4,
            },
            {
                "stem": "02_b",
                "target_hash": "da4fc665d86e91cb",
                "item_type": "heading",
                "is_digital": True,
                "is_paper": True,
                "file_count": 2,
                "prefix": "",
                "prev_item_num": None,
                "exp_targets_len": 4,
            },
            {
                "stem": "02_b",
                "target_hash": "5cafe92e61b687b7",
                "item_type": "heading",
                "is_digital": True,
                "is_paper": True,
                "file_count": 2,
                "prefix": "",
                "prev_item_num": None,
                "exp_targets_len": 4,
            },
            {
                "stem": "02_b",
                "target_hash": "b8a8d8f455fe9d01",
                "item_type": "figure",
                "is_digital": True,
                "is_paper": True,
                "file_count": 2,
                "prefix": "",
                "prev_item_num": 1,
                "exp_targets_len": 4,
            },
            {
                "stem": "02_b",
                "target_hash": "de476b0c0bfbc457",
                "item_type": "table",
                "is_digital": True,
                "is_paper": True,
                "file_count": 2,
                "prefix": "",
                "prev_item_num": 1,
                "exp_targets_len": 4,
            },
            {
                "stem": "05_conditional_rendering",
                "target_hash": "cad1981cd241e21a",
                "item_type": "figure",
                "is_digital": True,
                "is_paper": False,
                "file_count": 5,
                "prefix": "",
                "prev_item_num": 1,
                "exp_targets_len": 4,
            },
            {
                "stem": "05_conditional_rendering",
                "target_hash": "695b2635ac6087f9",
                "item_type": "figure",
                "is_digital": False,
                "is_paper": True,
                "file_count": 5,
                "prefix": "",
                "prev_item_num": 2,
                "exp_targets_len": 4,
            },
            {
                "stem": "05_conditional_rendering",
                "target_hash": "50c332fa0edff8a8",
                "item_type": "figure",
                "is_digital": True,
                "is_paper": True,
                "file_count": 5,
                "prefix": "",
                "prev_item_num": 3,
                "exp_targets_len": 4,
            },
            {
                "stem": "05_conditional_rendering",
                "target_hash": "1ecb9f4f0fe2e53d",
                "item_type": "figure",
                "is_digital": True,
                "is_paper": True,
                "file_count": 5,
                "prefix": "",
                "prev_item_num": 4,
                "exp_targets_len": 4,
            },
        ],
    )
    def test_targets_properly_registered(
        self,
        target_data: dict[str, str | int | bool],
    ):
        # targets are found by hash and fm_key
        docstate = self.docstates[target_data["stem"]]
        target: Target | None = docstate.get(
            "targets", target_data["target_hash"], attrib="hash"
        )
        assert (
            docstate.len("targets") == target_data["exp_targets_len"]
        ), f"There should be only {target_data['exp_targets_len']} targets in '{target_data['stem']}.html'."
        assert isinstance(
            target, Target
        ), "Did not find target by hash. Possible that the hash has changed after docx was modified."
        assert target.item_type == target_data["item_type"]
        assert target.is_digital == target_data["is_digital"]
        assert target.is_paper == target_data["is_paper"]
        assert target.fm_key.parts[-1] == f"{target_data['stem']}.docx"
        assert target.fm_key.parts[-3] == INPUT_DIR
        assert target.file_count == target_data["file_count"]
        assert target.prefix == target_data["prefix"]
        assert target.prev_item_num == target_data["prev_item_num"]
        assert (
            target.new_item_num == None
        ), "preparer should only register targets, updating new_item_num should be done by builder and wordprocessor"


class TestRefsAndTargetsInHTMLAfterPreparer_SplitDocExample:
    key_idx = _CHAPTERS_DIR / "split-to-multiple-chapters" / "00_index.html"
    key_inf = _CHAPTERS_DIR / "split-to-multiple-chapters" / "01_infile.html"
    key_uni = (
        _CHAPTERS_DIR
        / "split-to-multiple-chapters"
        / "02_is_unicode_with_custom_file_name.html"
    )

    @classmethod
    def setup_class(cls):
        cls.html: dict[KeyPath, bs4.BeautifulSoup] = {}
        for key in [cls.key_idx, cls.key_inf, cls.key_uni]:
            assert key.exists(), f"Expected {key} to exist but it does not."
            with open(key, "r") as f:
                cls.html[key] = bs4.BeautifulSoup(f.read(), "html.parser")
                script_tag = cls.html[key].find(
                    "script", {"class": CLS_STATE_TABLE_JSONDATA}
                )
                docstate = DocumentState(key)
                docstate.from_dict(json.loads(script_tag.string))
                cls.docstates[key] = docstate
