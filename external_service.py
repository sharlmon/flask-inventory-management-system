"""
OpenFoodFacts External API Integration Service.

Connects to the OpenFoodFacts public REST API to query real-time product information
by either barcode or keyword search, extracting relevant nutritional and ingredient
metadata to supplement inventory records.
"""

import requests
from typing import Optional, Dict, Any, List

OPENFOODFACTS_BARCODE_URL = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
OPENFOODFACTS_SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"

DEFAULT_HEADERS = {
    "User-Agent": "RetailInventoryManagementApp/1.0 (inventory-admin@retailstore.com)"
}


def format_openfoodfacts_product(raw_product: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and normalize relevant inventory fields from raw OpenFoodFacts JSON.
    """
    barcode = raw_product.get("code") or raw_product.get("_id") or ""
    product_name = (
        raw_product.get("product_name")
        or raw_product.get("product_name_en")
        or raw_product.get("generic_name")
        or "Unknown Product"
    )
    brands = raw_product.get("brands") or raw_product.get("brand") or "Generic"
    
    # Categories may be comma-separated or list
    categories = raw_product.get("categories") or raw_product.get("category") or "Groceries"
    if isinstance(categories, str) and "," in categories:
        primary_category = categories.split(",")[0].strip()
    elif isinstance(categories, list) and categories:
        primary_category = str(categories[0]).strip()
    else:
        primary_category = str(categories).strip()

    ingredients = (
        raw_product.get("ingredients_text")
        or raw_product.get("ingredients_text_en")
        or "N/A"
    )

    nutrition_grade = (
        raw_product.get("nutrition_grades")
        or raw_product.get("nutrition_grade_fr")
        or raw_product.get("nutriscore_grade")
        or "N/A"
    )

    return {
        "barcode": str(barcode).strip(),
        "product_name": str(product_name).strip(),
        "brands": str(brands).strip(),
        "category": primary_category,
        "ingredients_text": str(ingredients).strip(),
        "nutrition_grade": str(nutrition_grade).strip().lower()
    }


def fetch_product_by_barcode(barcode: str, timeout: int = 5) -> Optional[Dict[str, Any]]:
    """
    Query OpenFoodFacts API for a single product by barcode.
    Returns standardized product dict if found, None otherwise.
    """
    clean_barcode = str(barcode).strip()
    if not clean_barcode:
        return None

    url = OPENFOODFACTS_BARCODE_URL.format(barcode=clean_barcode)
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            # OpenFoodFacts returns status == 1 when product is found
            if data.get("status") == 1 and "product" in data:
                return format_openfoodfacts_product(data["product"])
        return None
    except requests.RequestException:
        # Handles connection errors, timeouts, etc.
        return None


def search_products_by_name(query: str, page_size: int = 5, timeout: int = 5) -> List[Dict[str, Any]]:
    """
    Search OpenFoodFacts database by keyword/product name.
    Returns a list of standardized product dicts up to page_size.
    """
    clean_query = str(query).strip()
    if not clean_query:
        return []

    params = {
        "search_terms": clean_query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": page_size
    }

    try:
        response = requests.get(OPENFOODFACTS_SEARCH_URL, params=params, headers=DEFAULT_HEADERS, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            products = data.get("products", [])
            formatted = []
            for p in products:
                # Include only products with a valid name
                if p.get("product_name") or p.get("product_name_en"):
                    formatted.append(format_openfoodfacts_product(p))
            return formatted
        return []
    except requests.RequestException:
        return []
