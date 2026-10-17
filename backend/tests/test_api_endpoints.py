"""
Integration tests for FastAPI endpoints and static file delivery.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_public_html_pages(client):
    routes = [
        "/",
        "/about",
        "/timings",
        "/contact",
        "/donate",
        "/gallery",
        "/festivals",
        "/login",
        "/register",
        "/dashboard",
        "/temple-info",
        "/admin",
        "/admin/temple",
        "/admin/temple-info",
        "/admin/donations",
        "/admin/users",
        "/admin/festivals",
    ]
    for route in routes:
        response = client.get(route)
        assert response.status_code == 200, f"Page route {route} failed with {response.status_code}"
        assert "text/html" in response.headers.get("content-type", "")


def test_static_assets(client):
    assets = [
        "/static/css/style.css",
        "/static/css/components.css",
        "/static/css/admin.css",
        "/static/js/app.js",
        "/static/js/i18n.js",
        "/static/js/auth.js",
        "/static/js/admin.js",
        "/static/favicon.svg",
        "/static/assets/gallery/temple-view.png",
        "/static/assets/documents/official_document_p1.jpg",
    ]
    for asset in assets:
        response = client.get(asset)
        assert response.status_code == 200, f"Static asset {asset} failed with {response.status_code}"


def test_api_temple_info(client):
    response = client.get("/api/temple")
    assert response.status_code == 200
    data = response.json()
    assert "name_en" in data
    assert "Shree Shanishwara" in data["name_en"]


def test_api_festivals(client):
    response = client.get("/api/festivals")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_api_gallery(client):
    response = client.get("/api/gallery")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
