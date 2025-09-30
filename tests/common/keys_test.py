from src._common.keys import KeyPath
from src._common.constants import JB_DIR, PAPER_DIR, STATE_DIR, WORK_DIR


## short file path example


def test_short_efs_filepath():
    key = KeyPath("myslug/text.md")
    assert key.efs_filepath == KeyPath("/tmp/efs/myslug/text.md")


def test_short_efs_slug_dir():
    key = KeyPath("myslug/text.md")
    assert key.efs_slug_dir == KeyPath(f"/tmp/efs/{WORK_DIR}/myslug")


def test_short_efs_paper_dir():
    key = KeyPath("myslug/text.md")
    assert key.efs_paper_dir == KeyPath("/tmp/efs/_PAPER/myslug")


def test_short_efs_paper_path():
    key = KeyPath("myslug/text.md")
    assert key.efs_paper_path == KeyPath("/tmp/efs/_PAPER/myslug/text.md")


def test_short_efs_jb_dir():
    key = KeyPath("myslug/text.md")
    assert key.efs_jb_dir == KeyPath("/tmp/efs/_JB/myslug")


def test_short_efs_jb_path():
    key = KeyPath("myslug/text.md")
    assert key.efs_jb_path == KeyPath("/tmp/efs/_JB/myslug/text.md")


def test_short_efs_state_dir():
    key = KeyPath("myslug/text.md")
    assert key.efs_state_dir == KeyPath("/tmp/efs/_STATE/myslug")


def test_short_efs_state_path():
    key = KeyPath("myslug/text.md")
    assert key.efs_state_path == KeyPath("/tmp/efs/_STATE/myslug/text.md")


def test_short_efs_filepath():
    key = KeyPath("myslug/text.md")
    assert key.efs_filepath.s3_key == KeyPath("myslug/text.md")


def test_short_github_path():
    key = KeyPath("myslug/text.md")
    assert key.github_path == KeyPath("text.md")


def test_short_slug():
    key = KeyPath("myslug/text.md")
    assert key.slug == "myslug"


def test_short_efs_slug_jb():
    key = KeyPath("myslug/text.md")
    assert key.efs_jb_path == KeyPath(f"/tmp/efs/{JB_DIR}/myslug/text.md")
    assert key.efs_jb_dir == KeyPath(f"/tmp/efs/{JB_DIR}/myslug")
    assert key.efs_jb_path.slug == "myslug"
    assert key.efs_jb_dir.slug == "myslug"


def test_short_efs_paper():
    key = KeyPath("myslug/text.md")
    assert key.efs_paper_path == KeyPath(f"/tmp/efs/{PAPER_DIR}/myslug/text.md")
    assert key.efs_paper_dir == KeyPath(f"/tmp/efs/{PAPER_DIR}/myslug")
    assert key.efs_paper_path.slug == "myslug"
    assert key.efs_paper_dir.slug == "myslug"


def test_short_efs_state():
    key = KeyPath("myslug/text.md")
    assert key.efs_state_path == KeyPath(f"/tmp/efs/{STATE_DIR}/myslug/text.md")
    assert key.efs_state_dir == KeyPath(f"/tmp/efs/{STATE_DIR}/myslug")
    assert key.efs_state_path.s3_key == KeyPath("myslug/text.md")
    assert key.efs_state_dir.s3_key == KeyPath("myslug")
    assert key.efs_state_path.slug == "myslug"
    assert key.efs_state_dir.slug == "myslug"


def test_short_efs_work():
    key = KeyPath("myslug/text.md")
    assert key.efs_work_path == KeyPath(f"/tmp/efs/{WORK_DIR}/myslug/text.md")
    assert key.efs_work_dir == KeyPath(f"/tmp/efs/{WORK_DIR}/myslug")
    assert key.efs_work_path.s3_key == KeyPath("myslug/text.md")
    assert key.efs_work_dir.s3_key == KeyPath("myslug")
    assert key.efs_work_path.slug == "myslug"
    assert key.efs_work_dir.slug == "myslug"


## long file path examples


def test_long_n_nested_efs_filepath():
    key = KeyPath("myslug/path/to/text.pdf.xmld")
    assert key.efs_filepath == KeyPath("/tmp/efs/myslug/path/to/text.pdf.xmld")


def test_long_n_nested_efs_slug_dir():
    key = KeyPath("myslug/path/to/text.pdf.xmld")
    assert key.efs_slug_dir == KeyPath(f"/tmp/efs/{WORK_DIR}/myslug")


def test_long_n_nested_efs_filepath():
    key = KeyPath("myslug/path/to/text.pdf.xmld")
    assert key.efs_filepath.s3_key == KeyPath("myslug/path/to/text.pdf.xmld")


def test_long_n_nested_github_path():
    key = KeyPath("myslug/path/to/text.pdf.xmld")
    assert key.github_path == KeyPath("path/to/text.pdf.xmld")


def test_long_n_nested_slug():
    key = KeyPath("myslug/path/to/text.pdf.xmld")
    assert key.slug == "myslug"


def test_long_n_efs_slug_jb():
    key = KeyPath("myslug/path/to/text.pdf.xmld")
    assert key.efs_jb_path == KeyPath(f"/tmp/efs/{JB_DIR}/myslug/path/to/text.pdf.xmld")
    assert key.efs_jb_dir == KeyPath(f"/tmp/efs/{JB_DIR}/myslug")
    assert key.efs_jb_path.slug == "myslug"
    assert key.efs_jb_dir.slug == "myslug"


def test_long_n_efs_paper():
    key = KeyPath("myslug/path/to/text.pdf.xmld")
    assert key.efs_paper_path == KeyPath(
        f"/tmp/efs/{PAPER_DIR}/myslug/path/to/text.pdf.xmld"
    )
    assert key.efs_paper_dir == KeyPath(f"/tmp/efs/{PAPER_DIR}/myslug")
    assert key.efs_paper_path.slug == "myslug"
    assert key.efs_paper_dir.slug == "myslug"


def test_long_n_efs_state():
    key = KeyPath("myslug/path/to/text.pdf.xmld")
    assert key.efs_state_path == KeyPath(
        f"/tmp/efs/{STATE_DIR}/myslug/path/to/text.pdf.xmld"
    )
    assert key.efs_state_dir == KeyPath(f"/tmp/efs/{STATE_DIR}/myslug")
    assert key.efs_state_path.s3_key == KeyPath("myslug/path/to/text.pdf.xmld")
    assert key.efs_state_dir.s3_key == KeyPath("myslug")
    assert key.efs_state_path.slug == "myslug"
    assert key.efs_state_dir.slug == "myslug"


def test_long_n_efs_work():
    key = KeyPath("myslug/path/to/text.pdf.xmld")
    assert key.efs_work_path == KeyPath(
        f"/tmp/efs/{WORK_DIR}/myslug/path/to/text.pdf.xmld"
    )
    assert key.efs_work_dir == KeyPath(f"/tmp/efs/{WORK_DIR}/myslug")
    assert key.efs_work_path.s3_key == KeyPath("myslug/path/to/text.pdf.xmld")
    assert key.efs_work_dir.s3_key == KeyPath("myslug")
    assert key.efs_work_path.slug == "myslug"
    assert key.efs_work_dir.slug == "myslug"


## tmp root examples


def test_tmprootpath_efs_filepath():
    key = KeyPath("/tmp/efs/myslug/path/to/text.pdf.xmld")
    assert key.efs_filepath == KeyPath("/tmp/efs/myslug/path/to/text.pdf.xmld")


def test_tmprootpath_efs_slug_dir():
    key = KeyPath("/tmp/efs/myslug/path/to/text.pdf.xmld")
    assert key.efs_slug_dir == KeyPath(f"/tmp/efs/{WORK_DIR}/myslug")


def test_tmprootpath_efs_filepath():
    key = KeyPath("/tmp/efs/myslug/path/to/text.pdf.xmld")
    assert key.efs_filepath.s3_key == KeyPath("myslug/path/to/text.pdf.xmld")


def test_tmprootpath_github_path():
    key = KeyPath("/tmp/efs/myslug/path/to/text.pdf.xmld")
    assert key.github_path == KeyPath("path/to/text.pdf.xmld")


def test_tmprootpath_slug():
    key = KeyPath("/tmp/efs/myslug/path/to/text.pdf.xmld")
    assert key.slug == "myslug"


def test_tmprootpath_efs_slug_jb():
    key = KeyPath("/tmp/efs/myslug/path/to/text.pdf.xmld")
    assert key.efs_jb_path == KeyPath(f"/tmp/efs/{JB_DIR}/myslug/path/to/text.pdf.xmld")
    assert key.efs_jb_dir == KeyPath(f"/tmp/efs/{JB_DIR}/myslug")
    assert key.efs_jb_path.slug == "myslug"
    assert key.efs_jb_dir.slug == "myslug"


def test_tmprootpath_efs_paper():
    key = KeyPath("/tmp/efs/myslug/path/to/text.pdf.xmld")
    assert key.efs_paper_path == KeyPath(
        f"/tmp/efs/{PAPER_DIR}/myslug/path/to/text.pdf.xmld"
    )
    assert key.efs_paper_dir == KeyPath(f"/tmp/efs/{PAPER_DIR}/myslug")
    assert key.efs_paper_path.slug == "myslug"
    assert key.efs_paper_dir.slug == "myslug"


def test_tmprootpath_efs_state():
    key = KeyPath("/tmp/efs/myslug/path/to/text.pdf.xmld")
    assert key.efs_state_path == KeyPath(
        f"/tmp/efs/{STATE_DIR}/myslug/path/to/text.pdf.xmld"
    )
    assert key.efs_state_dir == KeyPath(f"/tmp/efs/{STATE_DIR}/myslug")
    assert key.efs_state_path.s3_key == KeyPath("myslug/path/to/text.pdf.xmld")
    assert key.efs_state_dir.s3_key == KeyPath("myslug")
    assert key.efs_state_path.slug == "myslug"
    assert key.efs_state_dir.slug == "myslug"


def test_tmprootpath_efs_work():
    key = KeyPath("/tmp/efs/myslug/path/to/text.pdf.xmld")
    assert key.efs_work_path == KeyPath(
        f"/tmp/efs/{WORK_DIR}/myslug/path/to/text.pdf.xmld"
    )
    assert key.efs_work_dir == KeyPath(f"/tmp/efs/{WORK_DIR}/myslug")
    assert key.efs_work_path.s3_key == KeyPath("myslug/path/to/text.pdf.xmld")
    assert key.efs_work_dir.s3_key == KeyPath("myslug")
    assert key.efs_work_path.slug == "myslug"
    assert key.efs_work_dir.slug == "myslug"
