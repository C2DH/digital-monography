import bs4
import mammoth
import pathlib

from src.preparer.constants import MediumEnum, MAMMOTH_STYLE_MAP
from src.preparer.digital_prep import remove_metadata_tables
from src.preparer.html2md import convert_to_md
from src.preparer.metadata import DocumentMetadata, AssetDatapoint
from src.preparer.metadata_extraction import prepare_metadata_tables
from src.preparer.keys import KeyPath


SLUG = "book-content-examples"

# TODO: add metadata table tests


class TestMetadataTablesExtraction:
    fp = KeyPath(
        pathlib.Path("tests") / "_fixtures" / SLUG / "metadata_extraction.docx"
    )

    @classmethod
    def setup_class(cls):
        with open(cls.fp, "rb") as f:
            result = mammoth.convert_to_html(f, style_map=MAMMOTH_STYLE_MAP)
        cls.html_soup = bs4.BeautifulSoup(result.value, "html.parser")
        cls.metadata = DocumentMetadata(cls.fp.relative_to(cls.fp.parent.parent))
        tables = cls.html_soup.find_all("table")
        cls.html_soup = prepare_metadata_tables(cls.html_soup, cls.metadata, tables)
        cls.html_soup = remove_metadata_tables(cls.html_soup, cls.metadata, tables)
        cls.md = convert_to_md(cls.html_soup, cls.metadata)
        cls.asset_0 = cls.metadata.assets[0]
        cls.asset_1 = cls.metadata.assets[1]
        cls.asset_2 = cls.metadata.assets[2]
        cls.asset_3 = cls.metadata.assets[3]

    def test_all_metadata_tables_were_extracted(self):
        assert len(self.metadata.metadata_tables) == 3

    def test_all_assets_were_extracted(self):
        assert len(self.metadata.assets) == 4

    def test_all_metadata_rows_were_extracted(self):
        assert len(self.metadata.metadata_tables[0].kwargs) == 7
        assert len(self.metadata.metadata_tables[1].kwargs) == 5
        assert len(self.metadata.metadata_tables[2].kwargs) == 6

    def test_asset_0__1_asset_from_1_metadata_table(self):
        assert self.asset_0.fp == pathlib.Path("assets/tiny-picture.png")
        assert self.asset_0.metadata_table == self.metadata.metadata_tables[0].pk
        assert self.asset_0.medium == MediumEnum.PAPER
        assert self.asset_0.slug == SLUG
        assert self.asset_0.author == "Jean Carlo Emer"
        assert (
            self.asset_0.source
            == "https://unsplash.com/photos/beige-concrete-house-2d-RL-xa4mk"
        )
        assert self.asset_0.location == KeyPath(f"{SLUG}/metadata_extraction.docx")
        assert self.asset_0.alttext == "Red square"
        assert self.asset_0.caption == ""
        assert self.asset_0.comments == ""
        assert self.asset_0.is_color == False
        assert self.asset_0.is_ready == False
        assert self.asset_0.is_on_paper == True

    def test_asset_1__digital_and_paper_asset(self):
        assert self.asset_1.fp == pathlib.Path("assets/10x10px-img.png")
        assert self.asset_1.metadata_table == self.metadata.metadata_tables[1].pk
        assert self.asset_1.medium == MediumEnum.PAPER_AND_DIGITAL
        assert self.asset_1.slug == SLUG
        assert self.asset_1.author == "Jan Sobiepan"
        assert self.asset_1.source == ""
        assert self.asset_1.location == KeyPath(f"{SLUG}/metadata_extraction.docx")
        assert self.asset_1.alttext == "Yellow square - alt text written in MS Word"
        assert self.asset_1.caption == "Figure 1: Yellow square."
        assert self.asset_1.comments == ""
        assert self.asset_1.is_color == True
        assert self.asset_1.is_ready == False
        assert self.asset_1.is_on_paper == True

    def test_asset_2__2_assets_from_1_metadata_table__paper_one(self):
        assert self.asset_2.fp == pathlib.Path("assets/tiny-picture.png")
        assert self.asset_2.metadata_table == self.metadata.metadata_tables[2].pk
        assert self.asset_2.medium == MediumEnum.PAPER
        assert self.asset_2.slug == SLUG
        assert self.asset_2.author == ""
        assert self.asset_2.source == ""
        assert self.asset_2.location == KeyPath(f"{SLUG}/metadata_extraction.docx")
        assert self.asset_2.alttext == ""
        assert self.asset_2.caption == ""
        assert self.asset_2.comments == "Looks good"
        assert self.asset_2.is_color == None
        assert self.asset_2.is_ready == True
        assert self.asset_2.is_on_paper == True

    def test_asset_3__2_assets_from_1_metadata_table__digital_one(self):
        assert self.asset_3.fp == pathlib.Path("assets/10x10px-img.png")
        assert self.asset_3.metadata_table == self.metadata.metadata_tables[2].pk
        assert self.asset_3.medium == MediumEnum.DIGITAL
        assert self.asset_3.slug == SLUG
        assert self.asset_3.author == ""
        assert self.asset_3.source == ""
        assert self.asset_3.location == KeyPath(f"{SLUG}/metadata_extraction.docx")
        assert self.asset_3.alttext == ""
        assert self.asset_3.caption == ""
        assert self.asset_3.comments == "Looks good"
        assert self.asset_3.is_color == None
        assert self.asset_3.is_ready == True
        assert self.asset_3.is_on_paper == False

    def test_asset_json_handling(self):
        jsonified = self.asset_3.to_json()
        assert jsonified["is_color"] == None
        asset = AssetDatapoint.from_json(jsonified)
        assert asset.fp == pathlib.Path("assets/10x10px-img.png")
        assert asset.metadata_table == self.metadata.metadata_tables[2].pk
        assert asset.medium == MediumEnum.DIGITAL
        assert asset.slug == SLUG
        assert asset.author == ""
        assert asset.source == ""
        # assert asset.location == KeyPath(f"{SLUG}/metadata_extraction.docx")
        assert asset.alttext == ""
        assert asset.caption == ""
        assert asset.comments == "Looks good"
        assert asset.is_color == None
        assert asset.is_ready == True
        assert asset.is_on_paper == False
