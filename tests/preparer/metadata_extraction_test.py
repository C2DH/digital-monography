import bs4
import mammoth
import pathlib

from src.preparer.metadata_extraction import prepare_metadata_tables
from src.preparer.html2md import convert_to_md
from src.preparer.metadata import DocumentMetadata
from src.preparer.constants import (
    FIELD_DELETE_PREVIOUS,
    FIELD_DIGITAL_SOURCE,
    FIELD_PAPER_SOURCE,
    FIELD_LICENSE_NAME,
)


class TestHtml2MdMetadataExtraction:
    fp = pathlib.Path("tests") / "_fixtures" / "metadata_extraction.docx"

    @classmethod
    def setup_class(cls):
        with open(cls.fp, "rb") as f:
            result = mammoth.convert_to_html(f)
        cls.html_soup = bs4.BeautifulSoup(result.value, "html.parser")
        cls.metadata = DocumentMetadata()
        tables = cls.html_soup.find_all("table")
        cls.html_soup = prepare_metadata_tables(cls.html_soup, cls.metadata, tables)
        cls.md = convert_to_md(cls.html_soup, cls.metadata)
        cls.assets_meta = cls.metadata.to_dict()
        assets_ids = [dp.pk for dp in cls.metadata.assets]
        cls.asset_0 = cls.metadata.get_asset(assets_ids[0])
        cls.asset_1 = cls.metadata.get_asset(assets_ids[1])
        cls.asset_2 = cls.metadata.get_asset(assets_ids[2])
        cls.expected_kwargs = [
            {
                FIELD_PAPER_SOURCE: pathlib.Path("./images/tiny-picture.png"),
                FIELD_LICENSE_NAME: "Unsplash License",
                "licenseurl": "https://unsplash.com/license",
                "author": "Jean Carlo Emer",
                "takenfrom": "https://unsplash.com/photos/beige-concrete-house-2d-RL-xa4mk",
                FIELD_DELETE_PREVIOUS: True,
            },
            {
                FIELD_PAPER_SOURCE: pathlib.Path("./images/10x10px-img.png"),
                FIELD_DIGITAL_SOURCE: pathlib.Path("./images/10x10px-img.png"),
                FIELD_DELETE_PREVIOUS: False,
                "author": "Koziołek Matołek",
            },
            {
                FIELD_PAPER_SOURCE: pathlib.Path("./images/10x10px-img.png"),
                FIELD_DELETE_PREVIOUS: True,
            },
        ]

    def test_all_metadata_tables_were_extracted(self):
        assert len(self.metadata.assets) == 3

    def test_all_metadata_rows_were_extracted(self):
        assert len(self.asset_0.kwargs) == 7
        assert len(self.asset_1.kwargs) == 5
        assert len(self.asset_2.kwargs) == 4

    def test_string_values(self):
        print("self.asset_0.kwargs", self.asset_0.kwargs)
        print("self.asset_1.kwargs", self.asset_1.kwargs)
        assert (
            self.asset_0.kwargs[FIELD_PAPER_SOURCE]
            == self.expected_kwargs[0][FIELD_PAPER_SOURCE]
        )
        assert (
            self.asset_0.kwargs[FIELD_LICENSE_NAME]
            == self.expected_kwargs[0][FIELD_LICENSE_NAME]
        )
        assert (
            self.asset_0.kwargs["licenseurl"] == self.expected_kwargs[0]["licenseurl"]
        )
        assert self.asset_0.kwargs["author"] == self.expected_kwargs[0]["author"]
        assert self.asset_1.kwargs["author"] == self.expected_kwargs[1]["author"]

    def test_filepath_values(self):
        assert (
            self.asset_0.kwargs[FIELD_PAPER_SOURCE]
            == self.expected_kwargs[0][FIELD_PAPER_SOURCE]
        )
        assert (
            self.asset_1.kwargs[FIELD_PAPER_SOURCE]
            == self.expected_kwargs[1][FIELD_PAPER_SOURCE]
        )
        assert (
            self.asset_1.kwargs[FIELD_DIGITAL_SOURCE]
            == self.expected_kwargs[1][FIELD_DIGITAL_SOURCE]
        )

    def test_filepath_attribs(self):
        tiny_pic = pathlib.Path("./images/tiny-picture.png")
        img10x10 = pathlib.Path("./images/10x10px-img.png")
        assert self.asset_0.kwargs[FIELD_PAPER_SOURCE] == tiny_pic
        assert self.asset_0.kwargs.get(FIELD_DIGITAL_SOURCE) == None
        assert self.asset_1.kwargs[FIELD_PAPER_SOURCE] == img10x10
        assert self.asset_1.kwargs[FIELD_DIGITAL_SOURCE] == img10x10
        assert self.asset_2.kwargs[FIELD_PAPER_SOURCE] == tiny_pic
        assert self.asset_2.kwargs[FIELD_DIGITAL_SOURCE] == img10x10

    def test_delete_prev_values(self):
        assert (
            self.asset_0.kwargs[FIELD_DELETE_PREVIOUS]
            == self.expected_kwargs[0][FIELD_DELETE_PREVIOUS]
        )
        assert (
            self.asset_1.kwargs[FIELD_DELETE_PREVIOUS]
            == self.expected_kwargs[1][FIELD_DELETE_PREVIOUS]
        )
        assert (
            self.asset_2.kwargs[FIELD_DELETE_PREVIOUS]
            == self.expected_kwargs[2][FIELD_DELETE_PREVIOUS]
        )

    def test_delete_prev_attrib(self):
        assert self.asset_0.kwargs[FIELD_DELETE_PREVIOUS]
        assert self.asset_1.kwargs[FIELD_DELETE_PREVIOUS] == False
        assert self.asset_2.kwargs[FIELD_DELETE_PREVIOUS]

    def test_metadata_tables_removed_from_markdown(self):
        # TODO: think a smarter test
        assert self.asset_0.kwargs[FIELD_LICENSE_NAME] not in self.md
        assert self.asset_0.kwargs["author"] not in self.md
        assert self.asset_1.kwargs["author"] not in self.md

    def test_standard_tables_included_in_markdown(self):
        assert (
            "\n\n| Just a table | Just a table |\n| --- | --- |\n| Don’t extract | Don’t extract |\n\nJust a sentence to make sure that it won’t be removed.\n\n"
            in self.md
        )

    # def test_deleteprev_True_deleted_previous_block(self):
    #     # TODO: This doesn't work properly. Return to this.
    #     print("\n\n\n\n")
    #     print([(k, v.delete_prev) for k, v in self.metadata._metadata.items()])
    #     print("\n\n\n\n")
    #     print(repr(self.md))
    #     pprint(self.md)
    #     assert (
    #         "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAIAAAACUFjqAAAAAXNSR0IArs4c6QAAAAlwSFlzAAAOvgAADr4B6kKxwAAAABNJREFUKFNj/M+ADzDhlWUYqdIAQSwBE8U+X40AAAAASUVORK5CYII="
    #         not in self.md
    #     )

    def test_deleteprev_False_not_deleted_previous_block(self):
        assert (
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAhSURBVChTY/z/ieE/A0HAwcAEZREAP4hVyDCqEB9gYAAACsEEBH5uYgcAAAAASUVORK5CYII="
            in self.md
        )

    def test_oneliners_were_not_removed(self):
        assert "Just a sentence to make sure that it won’t be removed." in self.md
        assert "Another sentence." in self.md
