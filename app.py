"""
Flask-based RESTful API for Inventory Management System.

Exposes endpoints for full CRUD operations on inventory resources,
as well as helper routes for searching and integrating with the
external OpenFoodFacts database.
"""

from flask import Flask, request, jsonify, make_response
from typing import Tuple, Any

import models
import external_service


def create_app() -> Flask:
    """Application factory for Flask inventory API."""
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    # -------------------------------------------------------------
    # Root / Info Endpoint
    # -------------------------------------------------------------
    @app.route("/", methods=["GET"])
    def index():
        """Welcome route and endpoint documentation."""
        return jsonify({
            "message": "Welcome to the Retail Inventory Management REST API",
            "version": "1.0.0",
            "endpoints": {
                "GET /inventory": "Retrieve all inventory items (supports ?q= and ?category=)",
                "GET /inventory/<id>": "Retrieve a single inventory item by ID",
                "POST /inventory": "Add a new inventory item",
                "PATCH /inventory/<id>": "Update details/price/stock of an item",
                "DELETE /inventory/<id>": "Remove an item from inventory",
                "GET /inventory/search": "Search local inventory by keyword (?q=)",
                "GET /external/product/<barcode>": "Fetch product directly from OpenFoodFacts",
                "GET /external/search": "Search OpenFoodFacts by keyword (?q=)",
                "POST /inventory/import-external": "Import product directly from OpenFoodFacts by barcode"
            }
        }), 200

    # -------------------------------------------------------------
    # CRUD: GET /inventory (Read All)
    # -------------------------------------------------------------
    @app.route("/inventory", methods=["GET"])
    def get_inventory():
        """
        Fetch all inventory items.
        Supports optional query filters:
          ?q=<keyword>
          ?category=<category>
        """
        query = request.args.get("q")
        category = request.args.get("category")

        items = models.get_all_items()

        if query:
            items = models.search_items(query)

        if category:
            cat_clean = category.strip().lower()
            items = [item for item in items if cat_clean in str(item.get("category", "")).lower()]

        return jsonify({
            "count": len(items),
            "inventory": items
        }), 200

    # -------------------------------------------------------------
    # CRUD: GET /inventory/<int:item_id> (Read Single)
    # -------------------------------------------------------------
    @app.route("/inventory/<int:item_id>", methods=["GET"])
    def get_inventory_item(item_id: int):
        """Fetch a single inventory item by ID."""
        item = models.get_item_by_id(item_id)
        if not item:
            return jsonify({
                "error": "Not Found",
                "message": f"Inventory item with ID {item_id} does not exist."
            }), 404

        return jsonify(item), 200

    # -------------------------------------------------------------
    # CRUD: POST /inventory (Create)
    # -------------------------------------------------------------
    @app.route("/inventory", methods=["POST"])
    def create_inventory_item():
        """
        Add a new inventory item.
        Expects JSON body with at minimum: product_name, price.
        Optional fields: barcode, brands, category, quantity, ingredients_text, nutrition_grade.
        """
        data = request.get_json()
        if not data or not isinstance(data, dict):
            return jsonify({
                "error": "Bad Request",
                "message": "Request body must be valid JSON object."
            }), 400

        try:
            new_item = models.add_item(data)
            return jsonify({
                "message": "Inventory item created successfully.",
                "item": new_item
            }), 201
        except ValueError as err:
            return jsonify({
                "error": "Bad Request",
                "message": str(err)
            }), 400

    # -------------------------------------------------------------
    # CRUD: PATCH /inventory/<int:item_id> (Update)
    # -------------------------------------------------------------
    @app.route("/inventory/<int:item_id>", methods=["PATCH"])
    def update_inventory_item(item_id: int):
        """
        Partially update an inventory item by ID.
        Commonly updates price, quantity/stock, or metadata.
        """
        data = request.get_json()
        if not data or not isinstance(data, dict):
            return jsonify({
                "error": "Bad Request",
                "message": "Request body must be valid JSON object."
            }), 400

        if models.get_item_by_id(item_id) is None:
            return jsonify({
                "error": "Not Found",
                "message": f"Inventory item with ID {item_id} does not exist."
            }), 404

        try:
            updated_item = models.update_item(item_id, data)
            return jsonify({
                "message": f"Inventory item {item_id} updated successfully.",
                "item": updated_item
            }), 200
        except ValueError as err:
            return jsonify({
                "error": "Bad Request",
                "message": str(err)
            }), 400

    # -------------------------------------------------------------
    # CRUD: DELETE /inventory/<int:item_id> (Delete)
    # -------------------------------------------------------------
    @app.route("/inventory/<int:item_id>", methods=["DELETE"])
    def delete_inventory_item(item_id: int):
        """Delete an inventory item by ID."""
        success = models.delete_item(item_id)
        if not success:
            return jsonify({
                "error": "Not Found",
                "message": f"Inventory item with ID {item_id} does not exist."
            }), 404

        return jsonify({
            "message": f"Inventory item with ID {item_id} has been successfully deleted."
        }), 200

    # -------------------------------------------------------------
    # Helper Route: Search Local Inventory
    # -------------------------------------------------------------
    @app.route("/inventory/search", methods=["GET"])
    def search_local():
        """Search local inventory by query parameter ?q=."""
        query = request.args.get("q", "")
        results = models.search_items(query)
        return jsonify({
            "query": query,
            "count": len(results),
            "results": results
        }), 200

    # -------------------------------------------------------------
    # Helper Route: External OpenFoodFacts Lookup by Barcode
    # -------------------------------------------------------------
    @app.route("/external/product/<barcode>", methods=["GET"])
    def get_external_product(barcode: str):
        """Fetch live product details from OpenFoodFacts by barcode."""
        product = external_service.fetch_product_by_barcode(barcode)
        if not product:
            return jsonify({
                "error": "Not Found",
                "message": f"Product with barcode '{barcode}' was not found on OpenFoodFacts."
            }), 404

        return jsonify({
            "source": "OpenFoodFacts API",
            "product": product
        }), 200

    # -------------------------------------------------------------
    # Helper Route: External OpenFoodFacts Search by Name
    # -------------------------------------------------------------
    @app.route("/external/search", methods=["GET"])
    def search_external():
        """Search OpenFoodFacts API for products matching ?q=."""
        query = request.args.get("q", "")
        if not query:
            return jsonify({
                "error": "Bad Request",
                "message": "Query parameter 'q' is required."
            }), 400

        results = external_service.search_products_by_name(query)
        return jsonify({
            "source": "OpenFoodFacts API",
            "query": query,
            "count": len(results),
            "results": results
        }), 200

    # -------------------------------------------------------------
    # Helper Route: Import External Product into Inventory
    # -------------------------------------------------------------
    @app.route("/inventory/import-external", methods=["POST"])
    def import_external_product():
        """
        Fetch product details from OpenFoodFacts by barcode, apply default
        price/quantity, and insert into the local inventory array.
        """
        data = request.get_json() or {}
        barcode = data.get("barcode")
        if not barcode:
            return jsonify({
                "error": "Bad Request",
                "message": "Field 'barcode' is required in request body."
            }), 400

        # Check if already in inventory
        existing = models.get_item_by_barcode(barcode)
        if existing:
            return jsonify({
                "error": "Conflict",
                "message": f"Product with barcode '{barcode}' already exists in inventory with ID {existing['id']}."
            }), 409

        external_data = external_service.fetch_product_by_barcode(barcode)
        if not external_data:
            return jsonify({
                "error": "Not Found",
                "message": f"Could not find product with barcode '{barcode}' on OpenFoodFacts."
            }), 404

        # Supplement with provided price / quantity or defaults
        item_payload = {
            **external_data,
            "price": data.get("price", 4.99),
            "quantity": data.get("quantity", 10)
        }

        new_item = models.add_item(item_payload)
        return jsonify({
            "message": "Product successfully imported from OpenFoodFacts into inventory.",
            "item": new_item
        }), 201

    # -------------------------------------------------------------
    # Global Error Handlers
    # -------------------------------------------------------------
    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({
            "error": "Not Found",
            "message": "The requested endpoint does not exist."
        }), 404

    @app.errorhandler(405)
    def handle_405(e):
        return jsonify({
            "error": "Method Not Allowed",
            "message": "The HTTP method is not allowed for this route."
        }), 405

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
