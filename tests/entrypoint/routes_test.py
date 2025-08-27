import os
import flask
import flask.testing
import pathlib
import pytest
import sqlmodel

from src._common.constants import MediumEnum
from src._common.models import Asset, Heading
from src._common.keys import KeyPath
from src.entrypoint.app import create_app
from src.entrypoint.db import db_engine


@pytest.fixture
def client():
    os.environ["FLASK_SECRET_KEY"] = "123"
    os.environ["DASHBOARD_DOMAIN"] = "localhost:8001"
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def asset_slugs():
    # include
    SLUG_INCLUDE = "a_slug"
    SLUG_OMIT = "different-slug"
    ass_in_1 = Asset(
        fp=pathlib.PosixPath("foo/bar/1.txt"),
        metadata_table="0a7bf8c-0a7b-4b8c-0a7b-f8c0a7bf8c0a",
        medium=MediumEnum.PAPER,
        slug=SLUG_INCLUDE,
        author="TEST_TEST_TEST",
        source="source",
        location=KeyPath("foo/bar/1.docx"),
        loc=KeyPath("foo/bar/1.docx"),
        alttext="alttext",
        caption="caption",
        orig_caption="caption",
        comments="comments",
        target="target",
        is_color=True,
        is_ready=False,
    )
    # include
    ass_in_2 = Asset(
        fp=pathlib.PosixPath("foo/bar/2.txt"),
        metadata_table="ab7bf8c-0a7b-4b8c-0a7b-f8c0a7bf8c0a",
        medium=MediumEnum.DIGITAL,
        slug=SLUG_INCLUDE,
        author="TEST_TEST_TEST",
        source="source",
        location=KeyPath("foo/bar/2.docx"),
        loc=KeyPath("foo/bar/2.docx"),
        alttext="alttext",
        caption="caption",
        orig_caption="caption",
        comments="comments",
        target="target",
        is_color=True,
        is_ready=False,
    )
    # omit
    ass_out = Asset(
        fp=pathlib.PosixPath("zig/zag/index.txt"),
        metadata_table="",
        medium=MediumEnum.DIGITAL,
        slug=SLUG_OMIT,
        author="TEST_TEST_TEST",
        source="source",
        location=KeyPath("zig/zag/index.docx"),
        loc=KeyPath("zig/zag/index.docx"),
        alttext="alttext",
        caption="caption",
        orig_caption="caption",
        comments="comments",
        target="target",
        is_color=False,
        is_ready=False,
    )
    with sqlmodel.Session(db_engine) as session:
        session.add(ass_in_1)
        session.add(ass_in_2)
        session.add(ass_out)
        session.commit()
    yield SLUG_INCLUDE, SLUG_OMIT
    with sqlmodel.Session(db_engine) as session:
        stmt = sqlmodel.delete(Asset).where(Asset.author == "TEST_TEST_TEST")
        session.exec(stmt)
        session.commit()


@pytest.fixture
def heading_slugs():
    SLUG_INCLUDE = "a_slug"
    SLUG_OMIT = "different-slug"
    pk1 = "e1ae8368-9127-40a4-93a7-48e110520e67"
    pk2 = "cbdedcb1-f3f9-40b6-b987-8c9596d50aa7"
    h_in = Heading(
        **{
            "char_count": 434,
            "elem": "<h4>Important section</h4>",
            "file_name": "00_index.docx",
            "file_num": 0,
            "h_num": 4,
            "level": "4",
            "pk": pk1,
            "slug": SLUG_INCLUDE,
            "target": "",
            "text": "Important section",
            "word_count": 95,
            "x_loc": f"{SLUG_INCLUDE}/00_index.docx",
        }
    )
    h_out = Heading(
        **{
            "char_count": 434,
            "elem": "<h4>Heading</h4>",
            "file_name": "00_index.docx",
            "file_num": 0,
            "h_num": 4,
            "level": "4",
            "pk": pk2,
            "slug": SLUG_OMIT,
            "target": "",
            "text": "Heading",
            "word_count": 95,
            "x_loc": f"{SLUG_OMIT}/00_index.docx",
        }
    )
    with sqlmodel.Session(db_engine) as session:
        session.add(h_in)
        session.add(h_out)
        session.commit()
    yield SLUG_INCLUDE, SLUG_OMIT
    with sqlmodel.Session(db_engine) as session:
        stmt = sqlmodel.delete(Heading).where(sqlmodel.col(Heading.pk).in_([pk1, pk2]))
        session.exec(stmt)
        session.commit()


@pytest.mark.parametrize(
    "url,expected_length",
    [
        ("/assets/list?slug=a_slug", 0),
        ("/citations/groups/list?slug=a_slug", 0),
        ("/citations/items/list?slug=a_slug", 0),
        ("/headings/list?slug=a_slug", 0),
        ("/webhook", 0),
        ("/", 0),
    ],
)
def test_endpoint_accessible(
    url: str, expected_length: int, client: flask.testing.FlaskClient
):
    response = client.get(url)
    assert response.status_code == 200, f"{url} is unaccesible"


def test_assets_list(client: flask.testing.FlaskClient, asset_slugs: tuple[str, str]):
    slug_in, slug_out = asset_slugs
    url = f"/assets/list?slug={slug_in}"
    response = client.get(url)
    assert response.status_code == 200, f"{url} is unaccesible"
    assert (
        len(response.json) == 2
    ), f"{url} filtering is incorrect. Returned {len(response.json)} items"
    # filter out
    url = f"/assets/list?slug={slug_out}"
    response = client.get(url)
    assert response.status_code == 200, f"{url} is unaccesible"
    assert (
        len(response.json) == 1
    ), f"{url} filtering is incorrect. Returned {len(response.json)} items"


def test_headings_list(
    client: flask.testing.FlaskClient, heading_slugs: tuple[str, str]
):
    slug_in, slug_out = heading_slugs
    url = f"/headings/list?slug={slug_in}"
    response = client.get(url)
    assert response.status_code == 200, f"{url} is unaccesible"
    assert (
        len(response.json) == 1
    ), f"{url} filtering is incorrect. Returned {len(response.json)} items"
    h = Heading(**response.json[0])
    assert h.text == "Important section"
    # filter out
    slug_in, slug_out = heading_slugs
    url = f"/headings/list?slug={slug_out}"
    response = client.get(url)
    assert response.status_code == 200, f"{url} is unaccesible"
    assert (
        len(response.json) == 1
    ), f"{url} filtering is incorrect. Returned {len(response.json)} items"
    h = Heading(**response.json[0])
    assert h.text == "Heading"
