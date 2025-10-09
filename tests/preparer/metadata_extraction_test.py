import bs4
import mammoth
import pathlib

from src._common.constants import MediumEnum, MAMMOTH_STYLE_MAP
from src._common.html2md import convert_to_md
from src._common.metadata import DocumentMetadata
from src._common.models import Asset
from src._common.keys import KeyPath
from src._common.state import DocumentState
from src.preparer.digital_prep import remove_metadata_tables
from src.preparer.metadata_extraction import prepare_metadata_tables
from src.preparer.refs import (
    # prepare_ref_targets_in_captions,
    prepare_references,
    # is_caption,
    is_reference,
)
from src.preparer.targets import is_caption, prepare_ref_targets_in_captions

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
        cls.soup = bs4.BeautifulSoup(result.value, "html.parser")
        key = cls.fp.relative_to(cls.fp.parent.parent)
        cls.dstate = DocumentState(key)
        cls.metadata = DocumentMetadata(key)
        tables = cls.soup.find_all("table")
        captions = []
        references = []
        classifiers = [
            (is_caption, captions),
            (is_reference, references),
        ]
        for node in cls.soup.descendants:
            for check_if_meets_criteria, container in classifiers:
                if isinstance(node, bs4.element.Tag) and check_if_meets_criteria(node):
                    container.append(node)
        cls.soup = prepare_ref_targets_in_captions(
            cls.soup, cls.metadata, cls.dstate, captions
        )
        cls.soup = prepare_references(cls.soup, cls.metadata, cls.dstate, references)
        cls.soup = prepare_metadata_tables(cls.soup, cls.metadata, cls.dstate, tables)
        cls.soup = remove_metadata_tables(cls.soup, cls.dstate, tables)
        cls.md = convert_to_md(cls.soup, cls.dstate)
        cls.asset_0: Asset = cls.dstate["assets"][0]
        cls.asset_1: Asset = cls.dstate["assets"][1]
        cls.asset_2: Asset = cls.dstate["assets"][2]
        cls.asset_3: Asset = cls.dstate["assets"][3]
        # cls.asset_0 = cls.metadata.assets[0]
        # cls.asset_1 = cls.metadata.assets[1]
        # cls.asset_2 = cls.metadata.assets[2]
        # cls.asset_3 = cls.metadata.assets[3]

    def test_all_metadata_tables_were_extracted(self):
        assert len(self.metadata.metadata_tables) == 3

    def test_all_assets_were_extracted(self):
        assert len(self.dstate["assets"]) == 4

    def test_all_metadata_rows_were_extracted(self):
        assert len(self.metadata.metadata_tables[0].kwargs) == 7
        assert len(self.metadata.metadata_tables[1].kwargs) == 5
        assert len(self.metadata.metadata_tables[2].kwargs) == 6

    def test_asset_0__1_asset_from_1_metadata_table(self):
        assert self.asset_0.fp == pathlib.Path("assets/tiny-picture.png")
        assert self.asset_0.metadata_table == self.metadata.metadata_tables[0].pk
        assert self.asset_0.medium == MediumEnum.PAPER
        assert self.asset_0.slug == SLUG
        assert self.asset_0.author == "Unknown"
        assert (
            self.asset_0.source
            == "https://unsplash.com/photos/beige-concrete-house-2d-RL-xa4mk"
        )
        assert self.asset_0.location == KeyPath(f"{SLUG}/metadata_extraction.docx")
        assert self.asset_0.alttext == "Red square"
        assert self.asset_0.caption.startswith("Figure ")
        assert self.asset_0.caption.endswith(": Red square.")
        assert self.asset_0.comments == ""
        assert self.asset_0.target == "f-metadata-extraction-fig1redsquare"  # bookmark
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
        assert self.asset_1.caption.startswith("Figure ")
        assert self.asset_1.caption.endswith(": Yellow square.")
        assert self.asset_1.comments == ""
        assert self.asset_1.target == "f-metadata-extraction-ref191564298"  # auto ref
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
        assert self.asset_2.target == ""  # no caption, no target
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
        assert self.asset_3.target == ""  # no caption, no target
        assert self.asset_3.is_color == None
        assert self.asset_3.is_ready == True
        assert self.asset_3.is_on_paper == False

    def test_asset_to_json_handling(self):
        jsonified = self.asset_3.model_dump(mode="json")
        assert jsonified["fp"] == "assets/10x10px-img.png"
        assert jsonified["metadata_table"] == self.metadata.metadata_tables[2].pk
        assert type(jsonified["metadata_table"]) == str
        assert jsonified["medium"] == MediumEnum.DIGITAL.value
        assert jsonified["medium"] == "D"
        assert type(jsonified["medium"]) == str
        assert jsonified["slug"] == SLUG
        assert jsonified["author"] == ""
        assert jsonified["source"] == ""
        assert jsonified["location"] == f"{SLUG}/metadata_extraction.docx"
        assert jsonified["alttext"] == ""
        assert jsonified["caption"] == ""
        assert jsonified["comments"] == "Looks good"
        assert jsonified["target"] == ""  # no caption, no target
        assert jsonified["is_color"] == None
        assert jsonified["is_ready"] == True
        assert jsonified["is_on_paper"] == False

    def test_asset_from_json_handling(self):
        jsonified = self.asset_3.model_dump(mode="json")
        asset: Asset = Asset(**jsonified)
        assert asset.fp == pathlib.Path("assets/10x10px-img.png")
        assert asset.metadata_table == self.metadata.metadata_tables[2].pk
        assert type(asset.metadata_table) == str
        assert asset.medium == MediumEnum.DIGITAL
        assert asset.slug == SLUG
        assert asset.author == ""
        assert asset.source == ""
        assert asset.location == KeyPath(f"{SLUG}/metadata_extraction.docx")
        assert asset.alttext == ""
        assert asset.caption == ""
        assert asset.comments == "Looks good"
        assert asset.target == ""  # no caption, no target
        assert asset.is_color == None
        assert asset.is_ready == True
        assert asset.is_on_paper == False

    # TODO: missing test case where target points to unref
    # (there is a caption, but no reference)
