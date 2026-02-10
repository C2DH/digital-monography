import os
import flask
import flask.testing
import pytest

from src.entrypoint.app import create_app


@pytest.fixture
def client():
    os.environ["FLASK_SECRET_KEY"] = "123"
    os.environ["DASHBOARD_DOMAIN"] = "localhost:8001"
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.mark.parametrize(
    "url,expected_length",
    [
        ("/dbx/webhook/", 0),
        ("/dbx/webhook", 0),
        ("/dbx/", 0),
    ],
)
def test_api_endpoint_accessible(
    url: str, expected_length: int, client: flask.testing.FlaskClient
):
    response = client.get(url)
    assert response.status_code == 200, f"{url} is unaccesible"
