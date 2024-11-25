import bs4
import datetime
import mammoth
import pathlib

from src.preparer.metadata import AssetDatapoint, DocumentMetadata
from src.preparer.metadata_computation import compute_additional_metadata_fields
from src.preparer.metadata_extraction import prepare_metadata_tables
from src.preparer.keys import KeyPath


def is_table(tag: bs4.element.Tag) -> bool:
    return bool(tag.name == "table")


class TestHtml2MdMetadataCoptutation:
    fp = pathlib.Path("tests") / "_fixtures" / "small-example" / "index.docx"

    @classmethod
    def setup_class(cls):
        with open(cls.fp, "rb") as f:
            style_mappings = """
            p[style-name='Quote'] => blockquote:fresh
            p[style-name='Caption'] => p.dgt-mon-caption:fresh
            """
            result = mammoth.convert_to_html(f, style_map=style_mappings)
        cls.html_soup = bs4.BeautifulSoup(result.value, "html.parser")
        cls.metadata = DocumentMetadata(KeyPath(cls.fp))
        tables = []
        classifiers = [
            (is_table, tables),
        ]
        for node in cls.html_soup.descendants:
            for check_if_meets_criteria, container in classifiers:
                if isinstance(node, bs4.element.Tag) and check_if_meets_criteria(node):
                    container.append(node)
        cls.html_soup = prepare_metadata_tables(cls.html_soup, cls.metadata, tables)
        cls.metadata: DocumentMetadata = compute_additional_metadata_fields(
            cls.metadata
        )
        cls.red_square_1: AssetDatapoint = cls.metadata.assets[0]
        cls.red_square_2: AssetDatapoint = cls.metadata.assets[1]

    def test_file_name(self):
        assert self.red_square_1.kwargs.get("digitalname") == "tiny-picture.png"
        assert self.red_square_1.kwargs.get("papername") == "tiny-picture.png"
        assert self.red_square_2.kwargs.get("digitalname") == "tiny-picture.png"
        assert self.red_square_2.kwargs.get("papername") is None

    def test_file_size(self):
        assert self.red_square_1.kwargs.get("digitalsize") == 110
        assert self.red_square_2.kwargs.get("digitalsize") == 110

    def test_last_mod(self):
        mtime = self.red_square_1.kwargs.get("digitalmtime")
        t = datetime.datetime.fromtimestamp(mtime, tz=datetime.timezone.utc)
        assert t.year == 2023
        assert t.month == 12
        assert t.day == 20

    def test_caption(self):
        assert (
            self.red_square_1.kwargs.get("caption")
            == "Figure 1: An example of an image."
        )
        assert (
            self.red_square_2.kwargs.get("caption")
            == "Figure 2: Second example of an image."
        )

    def test_alttext_from_metadata_table(self):
        assert self.red_square_1.kwargs.get("alttext") == "Small red square"

    def test_alttext_from_img_alt_text(self):
        assert (
            self.red_square_2.kwargs.get("alttext")
            == "Second example of a small red square."
        )
