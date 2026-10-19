"""
CLI Frontend for Retail Inventory Management System.

Provides an interactive console interface allowing administrators to:
1. View all inventory items
2. View detailed product specifications
3. Add new inventory items manually
4. Search OpenFoodFacts API and import items directly into inventory
5. Update item prices and stock levels
6. Delete items from inventory
7. Search local inventory by keyword

Communicates with the REST API via HTTP requests (with automated fallback
to Flask internal client if the local server is not running).
"""

import sys
import json
import requests
from typing import Optional, Dict, Any, List

API_BASE_URL = "http://127.0.0.1:5000"


class InventoryApiClient:
    """Client wrapper for communicating with the Flask REST API."""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self._use_in_process = False
        self._test_client = None

        # Check if HTTP server is running; if not, use Flask test client
        try:
            r = requests.get(f"{self.base_url}/", timeout=0.8)
            if r.status_code == 200:
                self._use_in_process = False
            else:
                self._init_in_process()
        except Exception:
            self._init_in_process()

    def _init_in_process(self):
        """Fallback to in-process Flask test client for seamless standalone execution."""
        from app import app
        self._use_in_process = True
        self._test_client = app.test_client()

    def get_all(self, query: Optional[str] = None) -> Dict[str, Any]:
        """Fetch all inventory items."""
        endpoint = f"/inventory?q={query}" if query else "/inventory"
        if self._use_in_process:
            res = self._test_client.get(endpoint)
            return res.get_json()
        r = requests.get(f"{self.base_url}{endpoint}")
        return r.json()

    def get_one(self, item_id: int) -> Tuple_Response:
        """Fetch single item by ID."""
        endpoint = f"/inventory/{item_id}"
        if self._use_in_process:
            res = self._test_client.get(endpoint)
            return res.status_code, res.get_json()
        r = requests.get(f"{self.base_url}{endpoint}")
        return r.status_code, r.json()

    def create(self, payload: Dict[str, Any]) -> Tuple_Response:
        """Create new inventory item."""
        endpoint = "/inventory"
        if self._use_in_process:
            res = self._test_client.post(endpoint, json=payload)
            return res.status_code, res.get_json()
        r = requests.post(f"{self.base_url}{endpoint}", json=payload)
        return r.status_code, r.json()

    def patch(self, item_id: int, payload: Dict[str, Any]) -> Tuple_Response:
        """Update inventory item."""
        endpoint = f"/inventory/{item_id}"
        if self._use_in_process:
            res = self._test_client.patch(endpoint, json=payload)
            return res.status_code, res.get_json()
        r = requests.patch(f"{self.base_url}{endpoint}", json=payload)
        return r.status_code, r.json()

    def delete(self, item_id: int) -> Tuple_Response:
        """Delete inventory item."""
        endpoint = f"/inventory/{item_id}"
        if self._use_in_process:
            res = self._test_client.delete(endpoint)
            return res.status_code, res.get_json()
        r = requests.delete(f"{self.base_url}{endpoint}")
        return r.status_code, r.json()

    def search_external(self, query: str) -> Tuple_Response:
        """Search products on OpenFoodFacts."""
        endpoint = f"/external/search?q={query}"
        if self._use_in_process:
            res = self._test_client.get(endpoint)
            return res.status_code, res.get_json()
        r = requests.get(f"{self.base_url}{endpoint}")
        return r.status_code, r.json()

    def get_external_product(self, barcode: str) -> Tuple_Response:
        """Fetch product from OpenFoodFacts by barcode."""
        endpoint = f"/external/product/{barcode}"
        if self._use_in_process:
            res = self._test_client.get(endpoint)
            return res.status_code, res.get_json()
        r = requests.get(f"{self.base_url}{endpoint}")
        return r.status_code, r.json()

    def import_external(self, payload: Dict[str, Any]) -> Tuple_Response:
        """Import product from OpenFoodFacts into inventory."""
        endpoint = "/inventory/import-external"
        if self._use_in_process:
            res = self._test_client.post(endpoint, json=payload)
            return res.status_code, res.get_json()
        r = requests.post(f"{self.base_url}{endpoint}", json=payload)
        return r.status_code, r.json()


Tuple_Response = tuple[int, Dict[str, Any]]


def print_banner():
    print("\n" + "=" * 65)
    print("      RETAIL INVENTORY MANAGEMENT - ADMINISTRATOR PORTAL")
    print("=" * 65)


def format_item_table(items: List[Dict[str, Any]]) -> str:
    """Format a list of inventory items into a readable tabular text output."""
    if not items:
        return "No inventory items found."

    header = f"{'ID':<4} | {'Product Name':<30} | {'Brand':<15} | {'Price':<7} | {'Stock':<6} | {'Barcode'}"
    divider = "-" * len(header)
    lines = [header, divider]

    for it in items:
        p_name = (it.get("product_name") or "")[:28]
        brand = (it.get("brands") or "")[:13]
        price = f"${it.get('price', 0.0):.2f}"
        qty = str(it.get("quantity", 0))
        code = it.get("barcode", "") or "N/A"
        lines.append(f"{it.get('id', 0):<4} | {p_name:<30} | {brand:<15} | {price:<7} | {qty:<6} | {code}")

    return "\n".join(lines)


def view_all_items(client: InventoryApiClient):
    """CLI action: list all inventory items."""
    print("\n--- Current Inventory Items ---")
    data = client.get_all()
    items = data.get("inventory", [])
    print(format_item_table(items))
    print(f"Total Items: {len(items)}\n")


def view_item_details(client: InventoryApiClient):
    """CLI action: view complete details for a single item."""
    try:
        raw_id = input("Enter Item ID to view: ").strip()
        item_id = int(raw_id)
    except ValueError:
        print("[!] Error: ID must be a valid integer.")
        return

    status, res = client.get_one(item_id)
    if status == 200:
        print("\n--- Product Details ---")
        print(f"ID:               {res.get('id')}")
        print(f"Product Name:     {res.get('product_name')}")
        print(f"Brand:            {res.get('brands')}")
        print(f"Category:         {res.get('category')}")
        print(f"Barcode:          {res.get('barcode')}")
        print(f"Price:            ${res.get('price', 0.0):.2f}")
        print(f"Stock Quantity:   {res.get('quantity')}")
        print(f"Nutri-Score:      {res.get('nutrition_grade', 'N/A').upper()}")
        print(f"Ingredients:      {res.get('ingredients_text', 'N/A')}\n")
    else:
        print(f"[!] {res.get('message', 'Item not found.')}")


def add_item_manual(client: InventoryApiClient):
    """CLI action: manually add a new inventory item."""
    print("\n--- Add New Inventory Item ---")
    name = input("Product Name (required): ").strip()
    if not name:
        print("[!] Error: Product name is required.")
        return

    price_input = input("Retail Price (e.g. 4.99): ").strip()
    try:
        price = float(price_input)
        if price < 0:
            raise ValueError()
    except ValueError:
        print("[!] Error: Price must be a non-negative number.")
        return

    qty_input = input("Stock Quantity [default 0]: ").strip() or "0"
    try:
        qty = int(qty_input)
        if qty < 0:
            raise ValueError()
    except ValueError:
        print("[!] Error: Quantity must be a non-negative integer.")
        return

    brands = input("Brand [optional]: ").strip()
    category = input("Category [default 'General']: ").strip() or "General"
    barcode = input("Barcode / UPC [optional]: ").strip()
    ingredients = input("Ingredients text [optional]: ").strip()

    payload = {
        "product_name": name,
        "price": price,
        "quantity": qty,
        "brands": brands,
        "category": category,
        "barcode": barcode,
        "ingredients_text": ingredients
    }

    status, res = client.create(payload)
    if status == 201:
        print(f"[+] Success: Added '{name}' with ID {res['item']['id']}!")
    else:
        print(f"[!] Error: {res.get('message', 'Failed to create item.')}")


def search_and_import_openfoodfacts(client: InventoryApiClient):
    """CLI action: search OpenFoodFacts and import into inventory."""
    print("\n--- Search & Import from OpenFoodFacts API ---")
    print("1. Search by Barcode")
    print("2. Search by Product Keyword")
    choice = input("Select search mode (1 or 2): ").strip()

    if choice == "1":
        barcode = input("Enter Barcode (e.g. 0025293002487): ").strip()
        if not barcode:
            print("[!] Barcode cannot be empty.")
            return

        status, res = client.get_external_product(barcode)
        if status != 200:
            print(f"[!] {res.get('message', 'Product not found on OpenFoodFacts.')}")
            return

        prod = res.get("product", {})
        print("\nProduct Found on OpenFoodFacts:")
        print(f"  Name:        {prod.get('product_name')}")
        print(f"  Brand:       {prod.get('brands')}")
        print(f"  Category:    {prod.get('category')}")
        print(f"  Barcode:     {prod.get('barcode')}")
        print(f"  Nutri-Score: {prod.get('nutrition_grade', 'N/A').upper()}")
        print(f"  Ingredients: {prod.get('ingredients_text', 'N/A')[:90]}...")

        confirm = input("\nImport this product into your inventory? (y/n): ").strip().lower()
        if confirm != "y":
            print("Import cancelled.")
            return

        price_in = input("Enter retail price [default 3.99]: ").strip() or "3.99"
        qty_in = input("Enter initial stock quantity [default 15]: ").strip() or "15"

        try:
            price = float(price_in)
            qty = int(qty_in)
        except ValueError:
            print("[!] Invalid price or quantity.")
            return

        import_payload = {
            "barcode": barcode,
            "price": price,
            "quantity": qty
        }
        st, imp_res = client.import_external(import_payload)
        if st == 201:
            print(f"[+] Successfully imported product with ID {imp_res['item']['id']} into inventory!")
        else:
            print(f"[!] {imp_res.get('message', 'Import failed.')}")

    elif choice == "2":
        keyword = input("Enter product keyword (e.g. 'almond milk', 'pasta'): ").strip()
        if not keyword:
            print("[!] Keyword cannot be empty.")
            return

        print("Searching OpenFoodFacts database...")
        status, res = client.search_external(keyword)
        if status != 200 or not res.get("results"):
            print("[!] No matching products found on OpenFoodFacts.")
            return

        results = res.get("results", [])
        print(f"\nFound {len(results)} matches:")
        for idx, p in enumerate(results, start=1):
            print(f" [{idx}] {p.get('product_name')} | Brand: {p.get('brands')} | Barcode: {p.get('barcode')}")

        select_idx = input("\nEnter number to import (or press Enter to cancel): ").strip()
        if not select_idx or not select_idx.isdigit():
            print("Import cancelled.")
            return

        sel = int(select_idx)
        if sel < 1 or sel > len(results):
            print("[!] Invalid selection.")
            return

        chosen = results[sel - 1]
        barcode = chosen.get("barcode")
        if not barcode:
            print("[!] Selected product does not have a valid barcode for import.")
            return

        price_in = input("Enter retail price [default 4.49]: ").strip() or "4.49"
        qty_in = input("Enter initial stock quantity [default 20]: ").strip() or "20"
        try:
            price = float(price_in)
            qty = int(qty_in)
        except ValueError:
            print("[!] Invalid price or quantity.")
            return

        import_payload = {
            "barcode": barcode,
            "price": price,
            "quantity": qty
        }
        st, imp_res = client.import_external(import_payload)
        if st == 201:
            print(f"[+] Successfully imported '{chosen.get('product_name')}' into inventory (ID: {imp_res['item']['id']})!")
        else:
            print(f"[!] {imp_res.get('message', 'Import failed.')}")
    else:
        print("[!] Invalid option.")


def update_item_price_or_stock(client: InventoryApiClient):
    """CLI action: update price or stock of an item."""
    print("\n--- Update Inventory Item ---")
    raw_id = input("Enter Item ID to update: ").strip()
    try:
        item_id = int(raw_id)
    except ValueError:
        print("[!] ID must be a valid integer.")
        return

    status, cur = client.get_one(item_id)
    if status != 200:
        print(f"[!] {cur.get('message', 'Item not found.')}")
        return

    print(f"Current Item: {cur.get('product_name')}")
    print(f"Current Price: ${cur.get('price'):.2f} | Current Stock: {cur.get('quantity')}")

    new_price = input("New Price (press Enter to leave unchanged): ").strip()
    new_stock = input("New Stock Quantity (press Enter to leave unchanged): ").strip()

    updates = {}
    if new_price:
        try:
            updates["price"] = float(new_price)
        except ValueError:
            print("[!] Error: Invalid price.")
            return
    if new_stock:
        try:
            updates["quantity"] = int(new_stock)
        except ValueError:
            print("[!] Error: Invalid quantity.")
            return

    if not updates:
        print("No changes specified.")
        return

    st, res = client.patch(item_id, updates)
    if st == 200:
        print(f"[+] Success: Updated item {item_id}!")
    else:
        print(f"[!] Error: {res.get('message', 'Update failed.')}")


def delete_item_action(client: InventoryApiClient):
    """CLI action: delete an item from inventory."""
    print("\n--- Delete Inventory Item ---")
    raw_id = input("Enter Item ID to delete: ").strip()
    try:
        item_id = int(raw_id)
    except ValueError:
        print("[!] ID must be an integer.")
        return

    status, cur = client.get_one(item_id)
    if status != 200:
        print(f"[!] {cur.get('message', 'Item not found.')}")
        return

    confirm = input(f"Are you sure you want to delete '{cur.get('product_name')}'? (y/n): ").strip().lower()
    if confirm != "y":
        print("Deletion cancelled.")
        return

    st, res = client.delete(item_id)
    if st == 200:
        print(f"[+] {res.get('message', 'Deleted successfully.')}")
    else:
        print(f"[!] Error: {res.get('message', 'Failed to delete.')}")


def search_local_action(client: InventoryApiClient):
    """CLI action: search local inventory items by keyword."""
    query = input("\nEnter search keyword (product name, brand, category): ").strip()
    data = client.get_all(query=query)
    items = data.get("inventory", [])
    print(f"\n--- Search Results for '{query}' ---")
    print(format_item_table(items))
    print(f"Matches found: {len(items)}\n")


def main_interactive_menu():
    """Main CLI event loop."""
    client = InventoryApiClient()
    mode = "In-Process Flask API" if client._use_in_process else f"HTTP Server ({client.base_url})"

    while True:
        print_banner()
        print(f" [Connected via: {mode}]")
        print(" [1] View All Inventory Items")
        print(" [2] View Item Details by ID")
        print(" [3] Add New Inventory Item (Manual)")
        print(" [4] Search & Import from OpenFoodFacts API")
        print(" [5] Update Item (Price or Stock Level)")
        print(" [6] Delete an Item from Inventory")
        print(" [7] Search Local Inventory by Keyword")
        print(" [0] Exit Administrator Portal")
        print("-" * 65)

        choice = input("Enter your choice (0-7): ").strip()

        if choice == "1":
            view_all_items(client)
        elif choice == "2":
            view_item_details(client)
        elif choice == "3":
            add_item_manual(client)
        elif choice == "4":
            search_and_import_openfoodfacts(client)
        elif choice == "5":
            update_item_price_or_stock(client)
        elif choice == "6":
            delete_item_action(client)
        elif choice == "7":
            search_local_action(client)
        elif choice == "0":
            print("\nExiting Administrator Portal. Goodbye!")
            sys.exit(0)
        else:
            print("[!] Invalid selection. Please enter a number between 0 and 7.")

        input("\nPress Enter to return to main menu...")


if __name__ == "__main__":
    main_interactive_menu()
