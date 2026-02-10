import bs4
import json
import mammoth
import pathlib
import pytest
import typing as t

from src._common.constants import MediumEnum, MAMMOTH_STYLE_MAP
from src._common.keys import KeyPath
from src._common.state import DocumentState
from src._common.models import Asset, ChapterService
from src.preparer.main import prepare_docx

SLUG = "book-content-examples"


class TestMetadataTablesExtraction:
    fp = KeyPath(
        pathlib.Path("tests") / "_fixtures" / SLUG / "metadata_extraction.docx"
    )

    @classmethod
    def setup_class(cls):
        with open(cls.fp, "rb") as f:
            result = mammoth.convert_to_html(f, style_map=MAMMOTH_STYLE_MAP)
        cls.html_soup = bs4.BeautifulSoup(result.value, "html.parser")
        key = cls.fp.relative_to(cls.fp.parent.parent)
        cls.docstate = DocumentState(key)
        cls.docstate.add(ChapterService.generate_chapter_from_key(key))
        cls.html_soup, cls.docstate, _ = prepare_docx(cls.html_soup, cls.docstate)

    def test_all_assets_were_extracted(self):
        assert self.docstate.len("assets") == 4

    @pytest.mark.parametrize(
        "asset_data",
        [
            {
                "i": 0,
                "fp": KeyPath(f"assets/tiny-picture.png"),
                "location": KeyPath(f"{SLUG}/metadata_extraction.docx"),
                "medium": MediumEnum.PAPER,  # TODO: this might be wrong
                "alttext": "Red square",
                "caption": r"Figure {{ cd437c444ce8fc0d }}: Red square.",
                "comments": "",
                "target": "cd437c444ce8fc0d",
                "source": "https://unsplash.com/photos/beige-concrete-house-2d-RL-xa4mk",
                "author": "Unknown",
                "is_color": False,
                "is_ready": False,
                "is_on_paper": True,
                "rest": {"license": "copyleft", "deleteprevious": True},
                "height": None,
            },
            {
                "i": 1,
                "fp": KeyPath(f"assets/10x10px-img.png"),
                "location": KeyPath(f"{SLUG}/metadata_extraction.docx"),
                "medium": MediumEnum.PAPER_AND_DIGITAL,
                "alttext": "Yellow square - alt text written in MS Word",
                "caption": r"Figure {{ 6de3fd2e3ea2ee2f }}: Yellow square.",
                "comments": "",
                "target": "6de3fd2e3ea2ee2f",
                "source": "",
                "author": "Jan Sobiepan",
                "is_color": True,
                "is_ready": False,
                "is_on_paper": True,
                "rest": {"deleteprevious": False},
                "height": None,
            },
            {
                "i": 2,
                "fp": KeyPath(f"assets/tiny-picture.png"),
                "location": KeyPath(f"{SLUG}/metadata_extraction.docx"),
                "medium": MediumEnum.PAPER,
                "alttext": "",
                "caption": r"",
                "comments": "Looks good",
                "target": "",
                "source": "",
                "author": "",
                "is_color": None,
                "is_ready": True,
                "is_on_paper": True,
                "rest": {"deleteprevious": True},
                "height": None,
            },
            {
                "i": 3,
                "fp": KeyPath(f"assets/10x10px-img.png"),
                "location": KeyPath(f"{SLUG}/metadata_extraction.docx"),
                "medium": MediumEnum.DIGITAL,
                "alttext": "",
                "caption": r"",
                "comments": "Looks good",
                "target": "",
                "source": "",
                "author": "",
                "is_color": None,
                "is_ready": True,
                "is_on_paper": False,
                "rest": {"deleteprevious": True},
                "height": None,
            },
        ],
    )
    def test_assets_were_extracted_from_metadata_tables(
        self, asset_data: dict[str, int | str | KeyPath | bool]
    ):
        asset = self.docstate.all("assets")[asset_data["i"]]
        print("asset", asset)
        assert isinstance(asset, Asset), "Expected asset to be an instance of Asset"
        assert asset.fp == asset_data["fp"], "Asset.fp does not match"
        assert asset.location == asset_data["location"], "Asset.location does not match"
        assert asset.medium == asset_data["medium"], "Asset.medium does not match"
        assert asset.alttext == asset_data["alttext"], "Asset.alttext does not match"
        assert asset.caption == asset_data["caption"], "Asset.caption does not match"
        assert asset.comments == asset_data["comments"], "Asset.comments does not match"
        assert asset.target == asset_data["target"], "Asset.target does not match"
        assert asset.source == asset_data["source"], "Asset.source does not match"
        assert asset.author == asset_data["author"], "Asset.author does not match"
        assert asset.height == asset_data["height"], "Asset.height does not match"
        assert asset.is_color == asset_data["is_color"], "Asset.is_color does not match"
        assert asset.is_ready == asset_data["is_ready"], "Asset.is_ready does not match"
        assert (
            asset.is_on_paper == asset_data["is_on_paper"]
        ), "Asset.is_on_paper does not match"
        asset_rest: dict[str, t.Any] = json.loads(asset.rest)
        assert len(asset_rest) == len(
            asset_data["rest"]
        ), "Asset.rest length does not match"
        for k in asset_rest.keys():
            assert (
                asset_rest[k] == asset_data["rest"][k]
            ), f"Asset.rest[{k}] does not match"

    def test_asset_to_json_handling(self):
        asset = self.docstate.all("assets")[3]
        assert isinstance(asset, Asset)
        jsonified = asset.model_dump(mode="json")
        assert jsonified["fp"] == "assets/10x10px-img.png"
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
        asset = self.docstate.all("assets")[3]
        assert isinstance(asset, Asset)
        jsonified = asset.model_dump(mode="json")
        asset: Asset = Asset(**jsonified)
        assert asset.fp == pathlib.Path("assets/10x10px-img.png")
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
