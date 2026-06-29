"""
Real-time product lookup using public barcode APIs.

Sources tried:
1. Open Food Facts      - food/grocery
2. Open Beauty Facts    - cosmetics/personal care
3. Open Library         - books / ISBN
4. Google Books         - books / ISBN
5. UPCitemdb            - general retail
6. Demo fallback        - when no API finds product
"""

import requests

HEADERS = {"User-Agent": "BarcodeScannerApp/1.0"}
TIMEOUT = 1.5


def lookup(barcode: str) -> dict:
    barcode = str(barcode).strip()

    result = (
        _open_food_facts(barcode)
        or _open_beauty_facts(barcode)
        or _open_library(barcode)
        or _google_books(barcode)
        or _upcitemdb(barcode)
    )

    if result:
        result.setdefault("brand", "N/A")
        result.setdefault("category", "N/A")
        result.setdefault("price", "N/A")
        result.setdefault("mfg_date", "N/A")
        result.setdefault("exp_date", "N/A")
        result.setdefault("hsn_code", "N/A")
        result["found"] = True
        result["barcode"] = barcode
        return result

    return _demo_fallback(barcode)


def _open_food_facts(barcode: str) -> dict | None:
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        data = resp.json()

        if data.get("status") != 1:
            return None

        p = data.get("product", {})
        name = (
            p.get("product_name_en")
            or p.get("product_name")
            or p.get("abbreviated_product_name")
            or ""
        ).strip()

        if not name:
            return None

        return {
            "name": name,
            "brand": p.get("brands", "N/A").split(",")[0].strip(),
            "category": _first(p.get("categories_tags", [])) or "Food / Grocery",
            "source": "Open Food Facts",
        }

    except Exception:
        return None


def _open_beauty_facts(barcode: str) -> dict | None:
    url = f"https://world.openbeautyfacts.org/api/v0/product/{barcode}.json"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        data = resp.json()

        if data.get("status") != 1:
            return None

        p = data.get("product", {})
        name = (p.get("product_name") or "").strip()

        if not name:
            return None

        return {
            "name": name,
            "brand": p.get("brands", "N/A").split(",")[0].strip(),
            "category": _first(p.get("categories_tags", [])) or "Beauty / Personal Care",
            "source": "Open Beauty Facts",
        }

    except Exception:
        return None


def _open_library(barcode: str) -> dict | None:
    url = f"https://openlibrary.org/isbn/{barcode}.json"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)

        if resp.status_code != 200:
            return None

        data = resp.json()
        title = (data.get("title") or "").strip()

        if not title:
            return None

        authors = "N/A"
        if data.get("authors"):
            authors = "Author Available"

        return {
            "name": title,
            "brand": authors,
            "category": "Book / ISBN",
            "source": "Open Library",
        }

    except Exception:
        return None


def _google_books(barcode: str) -> dict | None:
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{barcode}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        data = resp.json()

        items = data.get("items", [])
        if not items:
            return None

        info = items[0].get("volumeInfo", {})
        title = (info.get("title") or "").strip()

        if not title:
            return None

        authors = ", ".join(info.get("authors", [])) if info.get("authors") else "N/A"
        categories = ", ".join(info.get("categories", [])) if info.get("categories") else "Book / ISBN"

        return {
            "name": title,
            "brand": authors,
            "category": categories,
            "source": "Google Books",
        }

    except Exception:
        return None


def _upcitemdb(barcode: str) -> dict | None:
    url = f"https://api.upcitemdb.com/prod/trial/lookup?upc={barcode}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        data = resp.json()

        items = data.get("items", [])
        if not items:
            return None

        item = items[0]
        name = (item.get("title") or "").strip()

        if not name:
            return None

        price_str = "N/A"
        offers = item.get("offers", [])
        if offers:
            price = offers[0].get("price")
            if price:
                price_str = f"₹{price}"

        return {
            "name": name,
            "brand": (item.get("brand") or "N/A").strip(),
            "category": (item.get("category") or "General Retail").strip(),
            "price": price_str,
            "source": "UPCitemdb",
        }

    except Exception:
        return None


def _demo_fallback(barcode: str) -> dict:
    return {
        "found": False,
        "barcode": barcode,
        "name": f"Demo Product {barcode[-4:]}",
        "brand": "Demo Brand",
        "category": _guess_category(barcode),
        "price": "₹99",
        "mfg_date": "2026-01-01",
        "exp_date": "2026-12-31",
        "hsn_code": "2106",
        "source": "Demo Fallback",
    }


def _guess_category(barcode: str) -> str:
    if barcode.startswith(("978", "979")):
        return "Book / ISBN"
    if barcode.startswith("890"):
        return "Indian Product / Grocery"
    return "General Product"


def _first(tags: list) -> str:
    for t in tags:
        val = str(t).split(":")[-1].replace("-", " ").title()
        if val:
            return val
    return "N/A"