"""
Unit tests for Flask REST API Endpoints.

Tests full CRUD operations:
- GET /inventory (all items, filtered)
- GET /inventory/<id> (single item, 404 handling)
- POST /inventory (creation, validation)
- PATCH /inventory/<id> (partial update, validation, 404 handling)
- DELETE /inventory/<id> (deletion, 404 handling)
- Helper and external search routes
"""

import pytest
from unittest.mock import patch

from app import create_app
import models


@pytest.fixture
def client():
    """Create a Flask test client with reset database state for each test."""
    models.reset_db()
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
    models.reset_db()


def test_index_route(client):
    """GET / should return welcome message and endpoint index."""
    res = client.get("/")
    assert res.status_code == 200
    data = res.get_json()
    assert "endpoints" in data
    assert "GET /inventory" in data["endpoints"]


def test_get_all_inventory(client):
    """GET /inventory returns all items with count."""
    res = client.get("/inventory")
    assert res.status_code == 200
    data = res.get_json()
    assert data["count"] == 5
    assert len(data["inventory"]) == 5
    assert data["inventory"][0]["product_name"] == "Organic Almond Milk"


def test_get_inventory_with_query_filter(client):
    """GET /inventory?q=almond filters items by search keyword."""
    res = client.get("/inventory?q=almond")
    assert res.status_code == 200
    data = res.get_json()
    assert data["count"] == 1
    assert data["inventory"][0]["brands"] == "Silk"


def test_get_inventory_with_category_filter(client):
    """GET /inventory?category=Spreads filters items by category."""
    res = client.get("/inventory?category=Spreads")
    assert res.status_code == 200
    data = res.get_json()
    assert data["count"] == 1
    assert data["inventory"][0]["product_name"] == "Nutella Hazelnut Spread"


def test_get_single_item_success(client):
    """GET /inventory/<id> returns item data when ID exists."""
    res = client.get("/inventory/1")
    assert res.status_code == 200
    item = res.get_json()
    assert item["id"] == 1
    assert item["product_name"] == "Organic Almond Milk"
    assert item["price"] == 3.99


def test_get_single_item_not_found(client):
    """GET /inventory/<id> returns 404 when ID does not exist."""
    res = client.get("/inventory/9999")
    assert res.status_code == 404
    data = res.get_json()
    assert data["error"] == "Not Found"


def test_create_item_success(client):
    """POST /inventory creates new item and returns 201 with auto-assigned ID."""
    payload = {
        "product_name": "Greek Yogurt Vanilla",
        "brands": "Chobani",
        "category": "Dairy",
        "price": 1.49,
        "quantity": 35,
        "barcode": "070847811169",
        "ingredients_text": "Cultured pasteurized nonfat milk, live and active cultures."
    }
    res = client.post("/inventory", json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert "item" in data
    assert data["item"]["id"] == 6
    assert data["item"]["product_name"] == "Greek Yogurt Vanilla"
    assert data["item"]["price"] == 1.49

    # Verify item is now retrievable
    get_res = client.get("/inventory/6")
    assert get_res.status_code == 200


def test_create_item_missing_product_name(client):
    """POST /inventory returns 400 when product_name is missing."""
    payload = {"price": 2.99, "quantity": 10}
    res = client.post("/inventory", json=payload)
    assert res.status_code == 400
    data = res.get_json()
    assert "product_name" in data["message"]


def test_create_item_invalid_price(client):
    """POST /inventory returns 400 when price is negative or non-numeric."""
    payload = {"product_name": "Invalid Item", "price": -5.00}
    res = client.post("/inventory", json=payload)
    assert res.status_code == 400
    data = res.get_json()
    assert "price" in data["message"]


def test_patch_item_success(client):
    """PATCH /inventory/<id> partially updates price and quantity."""
    payload = {"price": 4.29, "quantity": 18}
    res = client.patch("/inventory/1", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["item"]["price"] == 4.29
    assert data["item"]["quantity"] == 18
    # Unchanged fields remain intact
    assert data["item"]["product_name"] == "Organic Almond Milk"


def test_patch_item_not_found(client):
    """PATCH /inventory/<id> returns 404 for nonexistent item ID."""
    res = client.patch("/inventory/9999", json={"price": 5.99})
    assert res.status_code == 404


def test_patch_item_invalid_data(client):
    """PATCH /inventory/<id> returns 400 when given invalid values."""
    res = client.patch("/inventory/1", json={"quantity": -10})
    assert res.status_code == 400


def test_delete_item_success(client):
    """DELETE /inventory/<id> deletes item from array and returns 200."""
    res = client.delete("/inventory/1")
    assert res.status_code == 200

    # Ensure item no longer exists
    check_res = client.get("/inventory/1")
    assert check_res.status_code == 404

    # Ensure total count decreased
    all_res = client.get("/inventory")
    assert all_res.get_json()["count"] == 4


def test_delete_item_not_found(client):
    """DELETE /inventory/<id> returns 404 when item does not exist."""
    res = client.delete("/inventory/9999")
    assert res.status_code == 404


def test_search_local_route(client):
    """GET /inventory/search?q=barilla returns matched item."""
    res = client.get("/inventory/search?q=barilla")
    assert res.status_code == 200
    data = res.get_json()
    assert data["count"] == 1
    assert data["results"][0]["brands"] == "Barilla"


@patch("external_service.fetch_product_by_barcode")
def test_external_product_lookup_route(mock_fetch, client):
    """GET /external/product/<barcode> fetches product from OpenFoodFacts service."""
    mock_fetch.return_value = {
        "barcode": "123456789",
        "product_name": "Mocked Coconut Water",
        "brands": "Vita Coco",
        "category": "Beverages",
        "ingredients_text": "Coconut water",
        "nutrition_grade": "b"
    }

    res = client.get("/external/product/123456789")
    assert res.status_code == 200
    data = res.get_json()
    assert data["product"]["product_name"] == "Mocked Coconut Water"


@patch("external_service.fetch_product_by_barcode")
def test_import_external_route_success(mock_fetch, client):
    """POST /inventory/import-external adds external product into inventory."""
    mock_fetch.return_value = {
        "barcode": "999888777",
        "product_name": "Organic Honey",
        "brands": "Nature Nate's",
        "category": "Sweeteners",
        "ingredients_text": "100% Pure Raw Honey",
        "nutrition_grade": "d"
    }

    payload = {"barcode": "999888777", "price": 8.99, "quantity": 12}
    res = client.post("/inventory/import-external", json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert data["item"]["barcode"] == "999888777"
    assert data["item"]["price"] == 8.99
    assert data["item"]["quantity"] == 12


def test_import_external_route_conflict(client):
    """POST /inventory/import-external returns 409 if barcode already exists."""
    payload = {"barcode": "0025293002487", "price": 3.99}  # Silk almond milk already in initial db
    res = client.post("/inventory/import-external", json=payload)
    assert res.status_code == 409
    assert "already exists" in res.get_json()["message"]
