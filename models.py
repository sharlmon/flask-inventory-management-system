"""
Inventory Data Models and Simulated Storage.

Provides an in-memory database stored as an array of product dictionaries,
mirroring data attributes from the OpenFoodFacts API, along with helper
methods to perform complete CRUD operations.
"""

from typing import List, Dict, Any, Optional

# Initial mock database seed array resembling OpenFoodFacts API structure
INITIAL_INVENTORY: List[Dict[str, Any]] = [
    {
        "id": 1,
        "barcode": "0025293002487",
        "product_name": "Organic Almond Milk",
        "brands": "Silk",
        "category": "Plant-based beverages",
        "price": 3.99,
        "quantity": 25,
        "ingredients_text": "Almondmilk (filtered water, almonds), cane sugar, vitamin and mineral blend, sea salt.",
        "nutrition_grade": "b"
    },
    {
        "id": 2,
        "barcode": "3017620422003",
        "product_name": "Nutella Hazelnut Spread",
        "brands": "Ferrero",
        "category": "Spreads",
        "price": 4.49,
        "quantity": 40,
        "ingredients_text": "Sugar, palm oil, hazelnuts, skimmed milk powder, fat-reduced cocoa, emulsifier, vanillin.",
        "nutrition_grade": "e"
    },
    {
        "id": 3,
        "barcode": "5449000000996",
        "product_name": "Coca-Cola Original Taste",
        "brands": "Coca-Cola",
        "category": "Carbonated drinks",
        "price": 1.79,
        "quantity": 60,
        "ingredients_text": "Carbonated water, sugar, caramel color, phosphoric acid, natural flavors, caffeine.",
        "nutrition_grade": "e"
    },
    {
        "id": 4,
        "barcode": "7622210449283",
        "product_name": "Oreo Original Sandwich Cookies",
        "brands": "Oreo / Mondelez",
        "category": "Biscuits and cakes",
        "price": 2.99,
        "quantity": 30,
        "ingredients_text": "Wheat flour, sugar, palm oil, fat reduced cocoa powder, wheat starch, glucose-fructose syrup.",
        "nutrition_grade": "e"
    },
    {
        "id": 5,
        "barcode": "8076809513753",
        "product_name": "Barilla Spaghetti No. 5",
        "brands": "Barilla",
        "category": "Pastas",
        "price": 2.19,
        "quantity": 50,
        "ingredients_text": "Durum wheat semolina, water.",
        "nutrition_grade": "a"
    }
]

# Simulated in-memory database storage array
inventory_db: List[Dict[str, Any]] = [dict(item) for item in INITIAL_INVENTORY]


def reset_db() -> None:
    """Reset the in-memory inventory array back to initial state (for testing)."""
    global inventory_db
    inventory_db = [dict(item) for item in INITIAL_INVENTORY]


def get_all_items() -> List[Dict[str, Any]]:
    """Return all inventory items."""
    return inventory_db


def get_item_by_id(item_id: int) -> Optional[Dict[str, Any]]:
    """Find and return an inventory item by its numeric ID."""
    for item in inventory_db:
        if item.get("id") == item_id:
            return item
    return None


def get_item_by_barcode(barcode: str) -> Optional[Dict[str, Any]]:
    """Find and return an inventory item by its barcode."""
    clean_code = str(barcode).strip()
    for item in inventory_db:
        if str(item.get("barcode", "")).strip() == clean_code:
            return item
    return None


def add_item(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add a new inventory item with auto-assigned unique ID.
    Validates required fields and assigns sensible defaults.
    """
    product_name = data.get("product_name")
    if not product_name or not str(product_name).strip():
        raise ValueError("Field 'product_name' is required.")

    price = data.get("price")
    if price is None:
        raise ValueError("Field 'price' is required.")
    try:
        price_val = round(float(price), 2)
        if price_val < 0:
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError("Field 'price' must be a non-negative number.")

    quantity = data.get("quantity", 0)
    try:
        quantity_val = int(quantity)
        if quantity_val < 0:
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError("Field 'quantity' must be a non-negative integer.")

    # Determine next available ID
    existing_ids = [item["id"] for item in inventory_db if "id" in item]
    next_id = max(existing_ids, default=0) + 1

    new_item: Dict[str, Any] = {
        "id": next_id,
        "barcode": str(data.get("barcode", "")).strip(),
        "product_name": str(product_name).strip(),
        "brands": str(data.get("brands", "")).strip(),
        "category": str(data.get("category", "General")).strip(),
        "price": price_val,
        "quantity": quantity_val,
        "ingredients_text": str(data.get("ingredients_text", "")).strip(),
        "nutrition_grade": str(data.get("nutrition_grade", "")).strip().lower()
    }

    inventory_db.append(new_item)
    return new_item


def update_item(item_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Update selected fields of an existing inventory item.
    Supports partial updates (PATCH).
    """
    item = get_item_by_id(item_id)
    if not item:
        return None

    if "product_name" in updates:
        val = str(updates["product_name"]).strip()
        if not val:
            raise ValueError("Field 'product_name' cannot be empty.")
        item["product_name"] = val

    if "price" in updates:
        try:
            price_val = round(float(updates["price"]), 2)
            if price_val < 0:
                raise ValueError()
            item["price"] = price_val
        except (ValueError, TypeError):
            raise ValueError("Field 'price' must be a non-negative number.")

    if "quantity" in updates:
        try:
            quantity_val = int(updates["quantity"])
            if quantity_val < 0:
                raise ValueError()
            item["quantity"] = quantity_val
        except (ValueError, TypeError):
            raise ValueError("Field 'quantity' must be a non-negative integer.")

    if "brands" in updates:
        item["brands"] = str(updates["brands"]).strip()

    if "category" in updates:
        item["category"] = str(updates["category"]).strip()

    if "barcode" in updates:
        item["barcode"] = str(updates["barcode"]).strip()

    if "ingredients_text" in updates:
        item["ingredients_text"] = str(updates["ingredients_text"]).strip()

    if "nutrition_grade" in updates:
        item["nutrition_grade"] = str(updates["nutrition_grade"]).strip().lower()

    return item


def delete_item(item_id: int) -> bool:
    """Remove an item by ID from the inventory array. Returns True if removed, False if not found."""
    for idx, item in enumerate(inventory_db):
        if item.get("id") == item_id:
            del inventory_db[idx]
            return True
    return False


def search_items(query: str) -> List[Dict[str, Any]]:
    """Search inventory items matching query across product_name, brands, category, or barcode."""
    q = query.strip().lower()
    if not q:
        return inventory_db

    results = []
    for item in inventory_db:
        if (
            q in str(item.get("product_name", "")).lower()
            or q in str(item.get("brands", "")).lower()
            or q in str(item.get("category", "")).lower()
            or q in str(item.get("barcode", "")).lower()
        ):
            results.append(item)
    return results
