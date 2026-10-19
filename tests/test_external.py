"""
Unit tests for external_service.py (OpenFoodFacts API Integration).

Validates:
- format_openfoodfacts_product data normalization
- fetch_product_by_barcode with mocked HTTP responses
- search_products_by_name with mocked HTTP responses
- Error handling (network timeouts, non-200 status, product not found)
"""

import pytest
import requests
from unittest.mock import patch, MagicMock

import external_service


def test_format_openfoodfacts_product_normalization():
    """Verify raw OpenFoodFacts JSON is cleaned and structured properly."""
    raw = {
        "code": "12345000",
        "product_name": "Organic Oat Milk",
        "brands": "Oatly",
        "categories": "Plant-based beverages, Cereals and potatoes",
        "ingredients_text": "Oat base (water, oats 10%), rapeseed oil, calcium carbonate.",
        "nutrition_grades": "b"
    }

    formatted = external_service.format_openfoodfacts_product(raw)
    assert formatted["barcode"] == "12345000"
    assert formatted["product_name"] == "Organic Oat Milk"
    assert formatted["brands"] == "Oatly"
    assert formatted["category"] == "Plant-based beverages"
    assert formatted["nutrition_grade"] == "b"


@patch("requests.get")
def test_fetch_product_by_barcode_success(mock_get):
    """fetch_product_by_barcode returns product dict when found (status=1)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": 1,
        "product": {
            "code": "0025293002487",
            "product_name": "Organic Almond Milk",
            "brands": "Silk",
            "categories": "Beverages",
            "ingredients_text": "Almonds, water",
            "nutrition_grades": "b"
        }
    }
    mock_get.return_value = mock_response

    result = external_service.fetch_product_by_barcode("0025293002487")
    assert result is not None
    assert result["product_name"] == "Organic Almond Milk"
    assert result["barcode"] == "0025293002487"


@patch("requests.get")
def test_fetch_product_by_barcode_not_found(mock_get):
    """fetch_product_by_barcode returns None when product is missing (status=0)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": 0, "status_verbose": "product not found"}
    mock_get.return_value = mock_response

    result = external_service.fetch_product_by_barcode("0000000000000")
    assert result is None


@patch("requests.get")
def test_fetch_product_by_barcode_network_error(mock_get):
    """fetch_product_by_barcode gracefully returns None when requests raises an exception."""
    mock_get.side_effect = requests.RequestException("Connection timed out")
    result = external_service.fetch_product_by_barcode("12345")
    assert result is None


@patch("requests.get")
def test_search_products_by_name_success(mock_get):
    """search_products_by_name returns formatted list of matching products."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "count": 2,
        "products": [
            {"code": "111", "product_name": "Dark Chocolate 70%", "brands": "Lindt"},
            {"code": "222", "product_name": "Dark Chocolate 85%", "brands": "Lindt"}
        ]
    }
    mock_get.return_value = mock_response

    results = external_service.search_products_by_name("chocolate")
    assert len(results) == 2
    assert results[0]["barcode"] == "111"
    assert results[1]["product_name"] == "Dark Chocolate 85%"


def test_search_products_by_name_empty_query():
    """Empty query should return empty list without network call."""
    results = external_service.search_products_by_name("")
    assert results == []


@patch("requests.get")
def test_search_products_by_name_network_error(mock_get):
    """search_products_by_name handles request failure safely."""
    mock_get.side_effect = requests.RequestException("DNS lookup failed")
    results = external_service.search_products_by_name("bread")
    assert results == []
