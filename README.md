# Retail Inventory Management System (Flask REST API & CLI)

A robust, enterprise-grade inventory management backend and administrator portal built with **Python 3**, **Flask**, and **OpenFoodFacts External API integration**.

This project provides a complete CRUD RESTful web service to manage retail product stock, pricing, and nutritional details, paired with an interactive Command-Line Interface (CLI) and automated test suite.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture & Design](#architecture--design)
3. [Features](#features)
4. [Project Structure](#project-structure)
5. [Installation & Setup](#installation--setup)
6. [Running the Application](#running-the-application)
7. [API Endpoint Documentation](#api-endpoint-documentation)
8. [CLI Administrator Portal Guide](#cli-administrator-portal-guide)
9. [Running Unit Tests](#running-unit-tests)
10. [Git Workflow & Branching Strategy](#git-workflow--branching-strategy)

---

## Project Overview

Modern e-commerce and retail operations require inventory systems that are both easily manageable by operations staff and capable of augmenting local product records with rich, real-world data.

This application fulfills this requirement by:
- Offering standard **RESTful endpoints** for CRUD operations (`GET`, `POST`, `PATCH`, `DELETE`).
- Integrating with the public **OpenFoodFacts API** to pull real-time product metadata (ingredients, Nutri-Score, category, and brand) by barcode or keyword search.
- Providing an **interactive CLI tool** with graceful fallbacks for store managers.
- Providing 100% test coverage using `pytest` and `unittest.mock`.

---

## Architecture & Design

### Data Model & OpenFoodFacts Schema

Inventory data is maintained in an in-memory array (`inventory_db`) where each product contains:

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `Integer` | Unique primary key (auto-incremented) |
| `barcode` | `String` | Global Trade Item Number / EAN / UPC barcode |
| `product_name` | `String` | Commercial product title (Required) |
| `brands` | `String` | Manufacturer or brand name |
| `category` | `String` | Primary product category |
| `price` | `Float` | Unit retail price in USD (Required, non-negative) |
| `quantity` | `Integer` | In-stock inventory count (Default: 0) |
| `ingredients_text` | `String` | Full ingredients listing fetched or entered |
| `nutrition_grade` | `String` | Nutri-Score grade (`a`, `b`, `c`, `d`, `e`) |

### Mock Data Seed Structure

The initial simulated storage resembles the OpenFoodFacts data structure:
```json
{
  "id": 1,
  "barcode": "0025293002487",
  "product_name": "Organic Almond Milk",
  "brands": "Silk",
  "category": "Plant-based beverages",
  "price": 3.99,
  "quantity": 25,
  "ingredients_text": "Almondmilk (filtered water, almonds), cane sugar, sea salt.",
  "nutrition_grade": "b"
}
```

---

## Features

- **Full RESTful CRUD Support**: Standard HTTP methods and response status codes (`200 OK`, `201 Created`, `400 Bad Request`, `404 Not Found`, `409 Conflict`).
- **OpenFoodFacts Integration**: Query live food product databases by EAN/UPC barcode or product name.
- **One-Click Product Import**: Import external products directly into store inventory with custom price and stock quantities.
- **Interactive CLI Admin Portal**: Clean tabular displays, guided prompts, input sanitization, and error handling.
- **Comprehensive Unit Testing**: End-to-end tests for all API endpoints, CLI menus, and external API mocking.

---

## Project Structure

```
flask-inventory-management-system/
├── app.py                  # Flask application factory, routes, and error handlers
├── models.py               # In-memory inventory array & CRUD business logic
├── external_service.py     # OpenFoodFacts API integration (barcode & search)
├── cli.py                  # Interactive CLI Administrator Portal
├── requirements.txt        # Production & testing dependencies
├── .gitignore              # Ignored files (virtual environment, cache)
├── README.md               # Comprehensive documentation and API specification
└── tests/
    ├── __init__.py
    ├── test_api.py         # Unit tests for Flask REST endpoints (CRUD & search)
    ├── test_external.py    # Unit tests for OpenFoodFacts integration with mocks
    └── test_cli.py         # Unit tests for CLI functions and client logic
```

---

## Installation & Setup

### Prerequisites

- **Python 3.9+** (tested on Python 3.12 / 3.14)
- **pip** and **git**

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd flask-inventory-management-system
```

### 2. Create and Activate Virtual Environment

```bash
# On macOS / Linux:
python3 -m venv .venv
source .venv/bin/activate

# On Windows:
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Running the Application

### 1. Start the Flask REST API

```bash
python app.py
```
The server will start at: `http://127.0.0.1:5000/` with debug mode enabled.

### 2. Launch the CLI Administrator Portal

In a separate terminal (with the virtual environment activated):

```bash
python cli.py
```

> **Note**: `cli.py` includes automatic fallback detection. If the HTTP server is running, it makes live HTTP calls to `http://127.0.0.1:5000`. If the server is not yet running, it seamlessly communicates directly through Flask's in-process test client.

---

## API Endpoint Documentation

### Base URL: `http://127.0.0.1:5000`

### 1. Get All Inventory Items
- **Method**: `GET`
- **URL**: `/inventory`
- **Query Parameters**:
  - `q` *(optional)*: Search keyword across name, brand, barcode, category.
  - `category` *(optional)*: Filter by category.
- **Response**: `200 OK`
```json
{
  "count": 5,
  "inventory": [
    {
      "id": 1,
      "barcode": "0025293002487",
      "product_name": "Organic Almond Milk",
      "brands": "Silk",
      "category": "Plant-based beverages",
      "price": 3.99,
      "quantity": 25,
      "ingredients_text": "Almondmilk...",
      "nutrition_grade": "b"
    }
  ]
}
```

### 2. Get Single Item by ID
- **Method**: `GET`
- **URL**: `/inventory/<int:item_id>`
- **Response**: `200 OK` or `404 Not Found`
```json
{
  "id": 1,
  "barcode": "0025293002487",
  "product_name": "Organic Almond Milk",
  "brands": "Silk",
  "category": "Plant-based beverages",
  "price": 3.99,
  "quantity": 25,
  "ingredients_text": "Almondmilk...",
  "nutrition_grade": "b"
}
```

### 3. Create New Item (Manual)
- **Method**: `POST`
- **URL**: `/inventory`
- **Headers**: `Content-Type: application/json`
- **Request Body**:
```json
{
  "product_name": "Greek Yogurt Vanilla",
  "brands": "Chobani",
  "category": "Dairy",
  "price": 1.49,
  "quantity": 30,
  "barcode": "070847811169"
}
```
- **Response**: `201 Created`

### 4. Update Existing Item (Partial)
- **Method**: `PATCH`
- **URL**: `/inventory/<int:item_id>`
- **Headers**: `Content-Type: application/json`
- **Request Body**:
```json
{
  "price": 4.19,
  "quantity": 45
}
```
- **Response**: `200 OK` or `404 Not Found`

### 5. Delete Item
- **Method**: `DELETE`
- **URL**: `/inventory/<int:item_id>`
- **Response**: `200 OK` or `404 Not Found`
```json
{
  "message": "Inventory item with ID 1 has been successfully deleted."
}
```

### 6. Lookup Live Product from OpenFoodFacts
- **Method**: `GET`
- **URL**: `/external/product/<barcode>`
- **Response**: `200 OK` or `404 Not Found`

### 7. Search OpenFoodFacts Database
- **Method**: `GET`
- **URL**: `/external/search?q=<keyword>`
- **Response**: `200 OK`

### 8. Import Product from OpenFoodFacts
- **Method**: `POST`
- **URL**: `/inventory/import-external`
- **Headers**: `Content-Type: application/json`
- **Request Body**:
```json
{
  "barcode": "3017620422003",
  "price": 4.99,
  "quantity": 20
}
```
- **Response**: `201 Created` (or `409 Conflict` if product barcode is already in inventory).

---

## CLI Administrator Portal Guide

Run `python cli.py` to enter the interactive console:

```
=================================================================
      RETAIL INVENTORY MANAGEMENT - ADMINISTRATOR PORTAL
=================================================================
 [Connected via: HTTP Server (http://127.0.0.1:5000)]
 [1] View All Inventory Items
 [2] View Item Details by ID
 [3] Add New Inventory Item (Manual)
 [4] Search & Import from OpenFoodFacts API
 [5] Update Item (Price or Stock Level)
 [6] Delete an Item from Inventory
 [7] Search Local Inventory by Keyword
 [0] Exit Administrator Portal
-----------------------------------------------------------------
Enter your choice (0-7):
```

### Typical Workflows

1. **View Catalog**: Option `[1]` prints a clean ASCII table of all stock items.
2. **OpenFoodFacts Import**: Option `[4]` lets you enter any real-world barcode (e.g. `5449000000996` for Coca-Cola) or search by name (e.g. `Nutella`), preview product data, and immediately add it to your inventory.
3. **Restocking / Price Adjustments**: Option `[5]` updates stock levels and retail pricing.
4. **Product Retirement**: Option `[6]` prompts for confirmation before removing an item.

---

## Running Unit Tests

The test suite covers:
- REST API endpoint behavior (positive & negative cases).
- Validation error handling (`400 Bad Request` on invalid inputs).
- HTTP status code adherence (`200`, `201`, `404`, `409`).
- Mocked external OpenFoodFacts network requests using `unittest.mock`.
- CLI helper and table formatting functions.

Run the test suite with:

```bash
pytest -v
```

Expected output:
```
============================= test session starts ==============================
collected 30 items

tests/test_api.py::test_index_route PASSED                               [  3%]
tests/test_api.py::test_get_all_inventory PASSED                         [  6%]
...
tests/test_external.py::test_fetch_product_by_barcode_success PASSED     [ 83%]
...
tests/test_cli.py::test_api_client_in_process_crud PASSED                [ 70%]
============================== 30 passed in 0.27s ==============================
```

---

## Git Workflow & Branching Strategy

This repository was constructed strictly adhering to professional Git branching practices:

1. `main`: Production-ready stable branch.
2. `feature/models-and-data`: Implemented simulated storage array and CRUD business logic.
3. `feature/external-api`: Integrated OpenFoodFacts API service with error handling.
4. `feature/flask-routes`: Implemented Flask routing, request handling, and REST endpoints.
5. `feature/cli-frontend`: Created interactive CLI tool with table formatting and input validation.
6. `feature/unit-tests`: Implemented 30 unit tests using `pytest` and `unittest.mock`.
7. `feature/documentation`: Authored complete project documentation and user guide.

All feature branches were merged into `main` using `--no-ff` merge commits and cleaned up.
