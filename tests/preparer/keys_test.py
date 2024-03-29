import pytest


from src.preparer.keys import Key, InvalidKey


def test_flat_key():
    key = Key("slug/text.md", is_upload=True)
    assert key.root == ""
    assert key.phase == ""
    assert key.slug == "slug"
    assert key.path == "text.md"
    assert key.filename == "text.md"


def test_nested_key():
    key = Key("tmp/input/slug/path/to/text.pdf.xml", is_upload=False)
    assert key.root == "tmp"
    assert key.phase == "input"
    assert key.slug == "slug"
    assert key.path == "path/to/text.pdf.xml"
    assert key.filename == "text.pdf.xml"


def test_root_in_mnt():
    # TODO: implement /mnt/efs/...
    UNIMPLEMENTED = """
    key = Key("/mnt/efs/input/slug/file.txt", is_upload=False)
    assert key.root == "/mnt/efs"  # ?
    assert key.phase == "input"
    assert key.slug == "slug"
    assert key.path == "file.txt"
    assert key.filename == "file.txt"
    assert str(key.filepath.parent) == "/mnt/efs/input/slug/"
    """


def test_filepath():
    key = Key("slug/path/to/text.md", is_upload=True)
    assert hasattr(key.filepath, "parent")
    assert str(key.filepath.parent) == "slug/path/to"


# def test_mkdir():
#     key = Key("/tmp/html/slug/path/to/text.html", is_upload=False)
#     assert key.mkdir()


def test_stringification():
    key = Key("tmp/input/slug/path/to/text.docx", is_upload=False)
    assert str(key) == "tmp/input/slug/path/to/text.docx"


def test_simple_with_suffix():
    key = Key("slug/text.docx", is_upload=True)
    assert str(key.with_suffix(".md")) == "slug/text.md"


def test_nested_with_suffix():
    key = Key("tmp/input/slug/path/to/text.pdf.xml", is_upload=False)
    assert str(key.with_suffix(".html")) == "tmp/input/slug/path/to/text.pdf.html"


def test_as_input_dir():
    key = Key("tmp/input/slug/assets/a-chapter/text.docx", is_upload=False)
    new_key = key.as_input_dir(suffix=".txt")
    assert str(new_key) == "tmp/input/slug/assets/a-chapter/text.txt"


def test_as_html_dir():
    key = Key("tmp/input/slug/assets/a-chapter/text.docx", is_upload=False)
    new_key = key.as_html_dir(suffix=".html")
    assert str(new_key) == "tmp/html/slug/assets/a-chapter/text.html"


def test_as_md_dir():
    key = Key("tmp/input/slug/assets/a-chapter/text.docx", is_upload=False)
    new_key = key.as_md_dir(suffix=".md")
    assert str(new_key) == "tmp/md/slug/assets/a-chapter/text.md"


def test_as_jb_dir():
    key = Key("tmp/input/slug/assets/a-chapter/text.docx", is_upload=False)
    new_key = key.as_jb_dir(suffix=".md")
    assert str(new_key) == "tmp/jb/slug/assets/a-chapter/text.md"


def test_missing_slug_dir():
    with pytest.raises(InvalidKey):
        Key("text.docx", is_upload=True)


def test_missing_slug_dir_in_longer_filepaths():
    with pytest.raises(InvalidKey):
        Key("tmp/input/text.docx", is_upload=False)


def test_invalid_suffix_argument():
    with pytest.raises(ValueError):
        key = Key("tmp/input/slug/assets/a-chapter/text.docx", is_upload=False)
        key.as_html_dir(suffix="html")
