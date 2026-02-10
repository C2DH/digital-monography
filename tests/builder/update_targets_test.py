# preparer should only register refs and targets
# builder should calc the new values and change files

from src._common.constants import DEFAULT_SFS_DIR, JB_DIR
from src._common.keys import KeyPath
from src._common.state import BookState
from src._common.models import Target, TargetService
from src.builderv3.main import update_targets_for_substitutions


def test_update_targets_for_substitutions__different_item_types():
    fm_key = KeyPath(DEFAULT_SFS_DIR) / JB_DIR / "a_slug" / "manuscript.docx"
    jb_key = KeyPath(DEFAULT_SFS_DIR) / JB_DIR / "a_slug" / "manuscript.md"
    cfg_key = KeyPath(DEFAULT_SFS_DIR) / JB_DIR / "a_slug" / "myst.yml"
    bookstate = BookState(cfg_key)
    bookstate.add(
        Target(
            pk="1",
            loc=jb_key,
            fm_key=fm_key,
            html="",
            elem="",
            text="1",
            is_paper=True,
            is_digital=True,
            item_type="figure",
            file_count=1,
            prev_item_num=1,
            new_item_num=None,
            hash="hash1",
        )
    )
    bookstate.add(
        Target(
            pk="2",
            loc=jb_key,
            fm_key=fm_key,
            html="",
            elem="",
            text="1",
            is_paper=True,
            is_digital=True,
            item_type="table",
            file_count=1,
            prev_item_num=1,
            new_item_num=None,
            hash="hash2",
        )
    )
    bookstate.add(
        Target(
            pk="3",
            loc=jb_key,
            fm_key=fm_key,
            html="",
            elem="",
            text="2",
            is_paper=True,
            is_digital=True,
            item_type="figure",
            file_count=1,
            prev_item_num=2,
            new_item_num=None,
            hash="hash3",
        )
    )
    update_targets_for_substitutions(bookstate)
    fig1: Target = bookstate.get("targets", "1")
    tbl1: Target = bookstate.get("targets", "2")
    fig2: Target = bookstate.get("targets", "3")
    assert fig1.new_item_num == 1
    assert fig2.new_item_num == 2
    assert tbl1.new_item_num == 1
    assert TargetService.to_digital_version(fig1) == "1.1"
    assert TargetService.to_digital_version(fig2) == "1.2"
    assert TargetService.to_digital_version(tbl1) == "1.1"


def test_update_targets_for_substitutions__numbered_correctly_despite_targets_reversed_order():
    fm_key = KeyPath(DEFAULT_SFS_DIR) / JB_DIR / "a_slug" / "manuscript.docx"
    jb_key = KeyPath(DEFAULT_SFS_DIR) / JB_DIR / "a_slug" / "chapter1.md"
    jb_key_2 = KeyPath(DEFAULT_SFS_DIR) / JB_DIR / "a_slug" / "chapter2.md"
    cfg_key = KeyPath(DEFAULT_SFS_DIR) / JB_DIR / "a_slug" / "myst.yml"
    bookstate = BookState(cfg_key)
    bookstate.add(
        Target(
            pk="4",
            loc=jb_key,
            fm_key=fm_key,
            html="",
            elem="",
            text="4",
            is_paper=True,
            is_digital=True,
            item_type="figure",
            file_count=2,
            prefix="",
            prev_item_num=4,
            new_item_num=None,
            hash="hash4",
        )
    )
    bookstate.add(
        Target(
            pk="3",
            loc=jb_key,
            fm_key=fm_key,
            html="",
            elem="",
            text="3",
            is_paper=True,
            is_digital=True,
            item_type="figure",
            file_count=1,
            prefix="",
            prev_item_num=3,
            new_item_num=None,
            hash="hash3",
        )
    )
    bookstate.add(
        Target(
            pk="2",
            loc=jb_key,
            fm_key=fm_key,
            html="",
            elem="",
            text="2",
            is_paper=True,
            is_digital=True,
            item_type="figure",
            file_count=1,
            prefix="",
            prev_item_num=2,
            new_item_num=None,
            hash="hash2",
        )
    )
    bookstate.add(
        Target(
            pk="1",
            loc=jb_key,
            fm_key=fm_key,
            html="",
            elem="",
            text="1",
            is_paper=True,
            is_digital=True,
            item_type="figure",
            file_count=1,
            prefix="",
            prev_item_num=1,
            new_item_num=None,
            hash="hash1",
        )
    )
    update_targets_for_substitutions(bookstate)
    fig1: Target = bookstate.get("targets", "1")
    fig2: Target = bookstate.get("targets", "2")
    fig3: Target = bookstate.get("targets", "3")
    fig_from_chpt2: Target = bookstate.get("targets", "4")
    assert fig1.new_item_num == 1
    assert fig2.new_item_num == 2
    assert fig3.new_item_num == 3
    assert fig_from_chpt2.new_item_num == 1  # 1st in chapter2, 4th in book
    assert TargetService.to_digital_version(fig1) == "1.1"
    assert TargetService.to_digital_version(fig2) == "1.2"
    assert TargetService.to_digital_version(fig3) == "1.3"
    assert TargetService.to_digital_version(fig_from_chpt2) == "2.1"


def test_update_targets_for_substitutions__conditional_rendering():
    fm_key = KeyPath(DEFAULT_SFS_DIR) / JB_DIR / "a_slug" / "manuscript.docx"
    jb_key = KeyPath(DEFAULT_SFS_DIR) / JB_DIR / "a_slug" / "manuscript.md"
    cfg_key = KeyPath(DEFAULT_SFS_DIR) / JB_DIR / "a_slug" / "myst.yml"
    bookstate = BookState(cfg_key)
    bookstate.add(
        Target(
            pk="1",
            loc=jb_key,
            fm_key=fm_key,
            html="",
            elem="",
            text="1",
            is_paper=True,
            is_digital=False,  # omit counting in builder
            item_type="figure",
            file_count=1,
            prefix="",
            prev_item_num=1,
            new_item_num=None,
            hash="hash1",
        )
    )
    bookstate.add(
        Target(
            pk="2",
            loc=jb_key,  # chapter 2
            fm_key=fm_key,
            html="",
            elem="",
            text="2",
            is_paper=True,
            is_digital=True,
            item_type="figure",
            file_count=1,
            prefix="",
            prev_item_num=2,
            new_item_num=None,
            hash="hash2",
        )
    )
    update_targets_for_substitutions(bookstate)
    target_paperonly: Target = bookstate.get("targets", "1")
    target: Target = bookstate.get("targets", "2")
    assert target_paperonly.new_item_num == None  # omit because it's paper only
    assert target.new_item_num == 1  # first counted target in the chapter
    assert TargetService.to_digital_version(target_paperonly) == ""
    assert TargetService.to_digital_version(target) == "1.1"


def test_update_targets_for_substitutions__splitted_chapter2_starts_at_2():
    fm_key = KeyPath(DEFAULT_SFS_DIR) / JB_DIR / "a_slug" / "doc_before_split.docx"
    jb_key1 = KeyPath(DEFAULT_SFS_DIR) / JB_DIR / "a_slug" / "chapter1_after_split.md"
    jb_key2 = KeyPath(DEFAULT_SFS_DIR) / JB_DIR / "a_slug" / "chapter2_after_split.md"
    cfg_key = KeyPath(DEFAULT_SFS_DIR) / JB_DIR / "a_slug" / "myst.yml"
    bookstate = BookState(cfg_key)
    bookstate.add(
        Target(
            pk="1",
            loc=jb_key1,  # chapter 1
            fm_key=fm_key,
            html="",
            elem="",
            text="1",
            is_paper=True,
            is_digital=True,
            item_type="figure",
            file_count=1,
            prev_item_num=1,  # 1st in book and in chapter
            new_item_num=None,
            hash="hash1",
        )
    )
    bookstate.add(
        Target(
            pk="2",
            loc=jb_key2,  # chapter 2
            fm_key=fm_key,
            html="",
            elem="",
            text="2",
            is_paper=True,
            is_digital=True,
            item_type="figure",
            file_count=2,
            prev_item_num=2,  # It's 2nd in book, but 1st in chapter
            new_item_num=None,
            hash="hash2",
        )
    )
    bookstate.add(
        Target(
            pk="3",
            loc=jb_key2,  # chapter 2
            fm_key=fm_key,
            html="",
            elem="",
            text="3",
            is_paper=True,
            is_digital=True,
            item_type="figure",
            file_count=2,
            prev_item_num=3,  # It's 3rd in book, but 2nd in chapter
            new_item_num=None,
            hash="hash3",
        )
    )
    update_targets_for_substitutions(bookstate)
    target1: Target = bookstate.get("targets", "1")
    target2: Target = bookstate.get("targets", "2")
    target3: Target = bookstate.get("targets", "3")
    assert target1.new_item_num == 1  # chapter 1, figure 1
    assert target2.new_item_num == 1  # chapter 2, figure 1
    assert target3.new_item_num == 2  # chapter 2, figure 2
    assert TargetService.to_digital_version(target1) == "1.1"
    assert TargetService.to_digital_version(target2) == "2.1"
    assert TargetService.to_digital_version(target3) == "2.2"


def test_update_targets_for_substitutions__conditional_rendering_starting_at_2():
    fm_key = KeyPath(DEFAULT_SFS_DIR) / JB_DIR / "a_slug" / "doc_before_split.docx"
    jb_key = KeyPath(DEFAULT_SFS_DIR) / JB_DIR / "a_slug" / "chapter2_after_split.md"
    cfg_key = KeyPath(DEFAULT_SFS_DIR) / JB_DIR / "a_slug" / "myst.yml"
    bookstate = BookState(cfg_key)
    bookstate.add(
        Target(
            pk="2",
            loc=jb_key,
            fm_key=fm_key,
            html="",
            elem="",
            text="2",
            is_paper=True,
            is_digital=False,  # omit counting in builder
            item_type="figure",
            file_count=2,
            prev_item_num=2,  # It's 2nd in book, but 1st in chapter
            new_item_num=None,
            hash="hash2",
        )
    )
    bookstate.add(
        Target(
            pk="3",
            loc=jb_key,  # chapter 2
            fm_key=fm_key,
            html="",
            elem="",
            text="3",
            is_paper=True,
            is_digital=True,
            item_type="figure",
            file_count=2,
            prev_item_num=3,
            new_item_num=None,
            hash="hash3",
        )
    )
    update_targets_for_substitutions(bookstate)
    target_paperonly: Target = bookstate.get("targets", "2")
    target: Target = bookstate.get("targets", "3")
    assert target_paperonly.new_item_num == None  # omit because it's paper only
    assert target.new_item_num == 1  # first counted target in the chapter
    assert TargetService.to_digital_version(target_paperonly) == ""
    assert TargetService.to_digital_version(target) == "2.1"
