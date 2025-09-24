from src._common.keys import KeyPath


def test_short_efs_filepath():
    key = KeyPath("myslug/text.md")
    assert key.efs_filepath == KeyPath("/tmp/efs/myslug/text.md")


def test_short_efs_slug_dir():
    key = KeyPath("myslug/text.md")
    assert key.efs_slug_dir == KeyPath("/tmp/efs/myslug")


def test_short_efs_paper_dir():
    key = KeyPath("myslug/text.md")
    assert key.efs_paper_dir == KeyPath("/tmp/efs/_PAPER/myslug")


def test_short_efs_jb_dir():
    key = KeyPath("myslug/text.md")
    assert key.efs_jb_dir == KeyPath("/tmp/efs/_JB/myslug")


def test_short_efs_jb_path():
    key = KeyPath("myslug/text.md")
    assert key.efs_jb_path == KeyPath("/tmp/efs/_JB/myslug/text.md")


def test_short_efs_paper_path():
    key = KeyPath("myslug/text.md")
    assert key.efs_paper_path == KeyPath("/tmp/efs/_PAPER/myslug/text.md")


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


def test_long_n_nested_efs_filepath():
    key = KeyPath("myslug/path/to/text.pdf.xmld")
    assert key.efs_filepath == KeyPath("/tmp/efs/myslug/path/to/text.pdf.xmld")


def test_long_n_nested_efs_slug_dir():
    key = KeyPath("myslug/path/to/text.pdf.xmld")
    assert key.efs_slug_dir == KeyPath("/tmp/efs/myslug")


def test_long_n_nested_efs_filepath():
    key = KeyPath("myslug/path/to/text.pdf.xmld")
    assert key.efs_filepath.s3_key == KeyPath("myslug/path/to/text.pdf.xmld")


def test_long_n_nested_github_path():
    key = KeyPath("myslug/path/to/text.pdf.xmld")
    assert key.github_path == KeyPath("path/to/text.pdf.xmld")


def test_long_n_nested_slug():
    key = KeyPath("myslug/path/to/text.pdf.xmld")
    assert key.slug == "myslug"


def test_long_n_nested_efs_slug_html_path():
    key = KeyPath("myslug/path/to/text.pdf.xmld")


def test_tmprootpath_efs_filepath():
    key = KeyPath("/tmp/efs/myslug/path/to/text.pdf.xmld")
    assert key.efs_filepath == KeyPath("/tmp/efs/myslug/path/to/text.pdf.xmld")


def test_tmprootpath_efs_slug_dir():
    key = KeyPath("/tmp/efs/myslug/path/to/text.pdf.xmld")
    assert key.efs_slug_dir == KeyPath("/tmp/efs/myslug")


def test_tmprootpath_efs_filepath():
    key = KeyPath("/tmp/efs/myslug/path/to/text.pdf.xmld")
    assert key.efs_filepath.s3_key == KeyPath("myslug/path/to/text.pdf.xmld")


def test_tmprootpath_github_path():
    key = KeyPath("/tmp/efs/myslug/path/to/text.pdf.xmld")
    assert key.github_path == KeyPath("path/to/text.pdf.xmld")


def test_tmprootpath_slug():
    key = KeyPath("/tmp/efs/myslug/path/to/text.pdf.xmld")
    assert key.slug == "myslug"


def test_tmprootpath_efs_slug_html_path():
    key = KeyPath("/tmp/efs/myslug/path/to/text.pdf.xmld")
