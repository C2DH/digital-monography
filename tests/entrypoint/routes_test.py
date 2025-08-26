import os
import flask
import pytest
from sqlmodel import Session
from src.entrypoint.main import app  # , Item, engine


# os.environ["FLASK_SECRET_KEY"] = "123"


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client


def test_endpoint_accessible(client):
    params = [
        ("/assets/list?slug=a_book", 0),
        ("/citations/groups/list?slug=a_book", 0),
        ("/citations/items/list?slug=a_book", 0),
        ("/headings/list?slug=a_book", 0),
        ("/", 0),
    ]
    for url, length in params:
        response = client.get(url)
        assert response.status_code == 200, url
        # assert len(response.json) == length
    # assert 1 == 666
    # DGTMON_DEBUG=1 FLASK_SECRET_KEY=123 python3.12 -m pytest tests/entrypoint
