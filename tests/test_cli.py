"""
Unit tests for cli.py (Command Line Interface).

Tests:
- format_item_table formatting logic
- InventoryApiClient in-process API communication
- CLI interactive actions with mocked input and stdout
"""

import pytest
from unittest.mock import patch

from cli import format_item_table, InventoryApiClient
import models


@pytest.fixture(autouse=True)
def reset_db_state():
    """Ensure clean inventory database for each CLI test."""
    models.reset_db()
    yield
    models.reset_db()


def test_format_item_table_empty():
    """format_item_table handles empty list gracefully."""
    output = format_item_table([])
    assert "No inventory items found" in output


def test_format_item_table_with_items():
    """format_item_table creates headers and formatted columns."""
    sample = [
        {"id": 1, "product_name": "Test Milk", "brands": "BrandX", "price": 2.50, "quantity": 10, "barcode": "123"}
    ]
    output = format_item_table(sample)
    assert "ID" in output
    assert "Test Milk" in output
    assert "$2.50" in output


def test_api_client_in_process_crud():
    """Verify InventoryApiClient performs CRUD against in-process Flask app."""
    client = InventoryApiClient(base_url="http://non-existent-test-domain:9999")
    assert client._use_in_process is True

    # 1. Get all
    data = client.get_all()
    assert data["count"] == 5

    # 2. Get one
    status, item = client.get_one(1)
    assert status == 200
    assert item["id"] == 1

    # 3. Create
    status, created = client.create({
        "product_name": "CLI Created Item",
        "price": 5.49,
        "quantity": 20
    })
    assert status == 201
    assert created["item"]["product_name"] == "CLI Created Item"

    # 4. Patch
    status, patched = client.patch(created["item"]["id"], {"price": 6.00})
    assert status == 200
    assert patched["item"]["price"] == 6.00

    # 5. Delete
    status, deleted = client.delete(created["item"]["id"])
    assert status == 200
    assert "deleted" in deleted["message"]


@patch("builtins.input", side_effect=["Test Product", "9.99", "5", "TestBrand", "Snacks", "111222", "Sugar"])
def test_cli_add_item_manual(mock_input, capsys):
    """Test manual add item flow."""
    from cli import add_item_manual
    client = InventoryApiClient(base_url="http://non-existent-test-domain:9999")

    add_item_manual(client)
    captured = capsys.readouterr()
    assert "[+] Success: Added 'Test Product'" in captured.out


@patch("builtins.input", side_effect=["1", "y"])
def test_cli_delete_item_action(mock_input, capsys):
    """Test delete item flow."""
    from cli import delete_item_action
    client = InventoryApiClient(base_url="http://non-existent-test-domain:9999")

    delete_item_action(client)
    captured = capsys.readouterr()
    assert "has been successfully deleted" in captured.out
