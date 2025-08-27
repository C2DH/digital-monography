import os
import flask
import flask.testing
import pytest
from sqlmodel import Session

from src.entrypoint.app import create_app


@pytest.fixture
def client():
    os.environ["FLASK_SECRET_KEY"] = "123"
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.mark.parametrize(
    "url,expected_length",
    [
        ("/assets/list?slug=a_book", 0),
        ("/citations/groups/list?slug=a_book", 0),
        ("/citations/items/list?slug=a_book", 0),
        ("/headings/list?slug=a_book", 0),
        ("/", 0),
    ],
)
def test_endpoint_accessible(
    url: str, expected_length: int, client: flask.testing.FlaskClient
):
    response = client.get(url)
    assert response.status_code == 200, url
    # assert len(response.json) == length
    # assert 1 == 666
    # DGTMON_DEBUG=1 FLASK_SECRET_KEY=123 python3.12 -m pytest tests/entrypoint
