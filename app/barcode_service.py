"""Barcode enrichment via free public catalogs.

- Food: OpenFoodFacts world API — no key required.
- Medicine: OpenFDA NDC directory — no key required.

Returns a normalised dict the scan pipeline can feed straight to Claude.
"""
from __future__ import annotations

import re
from typing import Any

import httpx

FOOD_URL = "https://world.openfoodfacts.org/api/v2/product/{code}.json"
FDA_URL = "https://api.fda.gov/drug/ndc.json"


async def _get_json(client: httpx.AsyncClient, url: str, params: dict | None = None) -> dict | None:
    try:
        response = await client.get(url, params=params, timeout=8.0)
        if response.status_code != 200:
            return None
        return response.json()
    except (httpx.HTTPError, ValueError):
        return None


def _pack(*items: str | list[str] | None) -> str:
    lines: list[str] = []
    for value in items:
        if not value:
            continue
        if isinstance(value, list):
            joined = ", ".join(str(v).strip() for v in value if v)
            if joined:
                lines.append(joined)
        else:
            text = str(value).strip()
            if text:
                lines.append(text)
    return "\n".join(lines)


async def _lookup_food(client: httpx.AsyncClient, code: str) -> dict[str, Any] | None:
    data = await _get_json(client, FOOD_URL.format(code=code))
    if not data or data.get("status") != 1:
        return None
    product = data.get("product") or {}
    name = product.get("product_name") or product.get("generic_name") or "Scanned product"
    brand = product.get("brands", "")
    ingredients = product.get("ingredients_text_en") or product.get("ingredients_text") or ""
    allergens = product.get("allergens_from_ingredients") or product.get("allergens", "")
    nutrition = product.get("nutriments") or {}
    nutrition_summary_parts = []
    for key, label in [
        ("energy-kcal_100g", "kcal/100g"),
        ("sugars_100g", "sugars g/100g"),
        ("salt_100g", "salt g/100g"),
        ("saturated-fat_100g", "sat fat g/100g"),
        ("proteins_100g", "protein g/100g"),
    ]:
        if key in nutrition and nutrition[key] is not None:
            nutrition_summary_parts.append(f"{label}: {nutrition[key]}")
    packed_text = _pack(
        f"Product: {name}" if name else None,
        f"Brand: {brand}" if brand else None,
        f"Ingredients: {ingredients}" if ingredients else None,
        f"Allergens: {allergens}" if allergens else None,
        "Nutrition — " + ", ".join(nutrition_summary_parts) if nutrition_summary_parts else None,
    )
    return {
        "source": "openfoodfacts",
        "kind": "FOOD",
        "product_name": name,
        "brand": brand,
        "ingredients_text": ingredients,
        "packed_text": packed_text,
        "image_url": product.get("image_front_small_url") or product.get("image_url"),
    }


def _ndc_candidates(code: str) -> list[str]:
    """Return every plausible hyphenated NDC layout for a raw scanned code."""
    digits = re.sub(r"\D", "", code)
    if not digits:
        return []
    # GTIN-13 drug barcodes prefix a leading "3" to a 10-digit NDC (and a check digit).
    stripped = set()
    if len(digits) == 13 and digits[0] == "3":
        stripped.add(digits[1:11])  # drop leading 3 and trailing check digit
    if len(digits) == 12:
        stripped.add(digits[:11])
        stripped.add(digits[1:])
    stripped.add(digits)

    candidates: list[str] = []
    for d in stripped:
        if len(d) == 11:
            # NDC-11 can be 5-4-2, 5-3-2 (with rescue insertion) — cover the common splits
            for a, b in [(5, 4), (4, 5), (5, 3)]:
                if a + b + 2 == 11:
                    candidates.append(f"{d[:a]}-{d[a:a + b]}-{d[a + b:]}")
        elif len(d) == 10:
            for a, b in [(4, 4), (5, 3), (5, 4)]:
                if a + b + 2 <= 10:
                    candidates.append(f"{d[:a]}-{d[a:a + b]}-{d[a + b:a + b + 2]}")
        elif len(d) == 9:
            candidates.append(f"{d[:4]}-{d[4:8]}-{d[8:]}")
    # De-duplicate while preserving order; also allow already-hyphenated input
    if "-" in code:
        candidates.insert(0, code)
    seen = set()
    unique = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return unique


async def _lookup_medicine(client: httpx.AsyncClient, code: str) -> dict[str, Any] | None:
    for ndc in _ndc_candidates(code):
        for field in ("product_ndc", "package_ndc"):
            data = await _get_json(client, FDA_URL, params={"search": f"{field}:{ndc}", "limit": 1})
            if data and data.get("results"):
                entry = data["results"][0]
                name = entry.get("brand_name") or entry.get("generic_name") or "Scanned medicine"
                generic = entry.get("generic_name", "")
                active_ingredients = [
                    f"{ing.get('name', '')} {ing.get('strength', '')}".strip()
                    for ing in (entry.get("active_ingredients") or [])
                    if ing.get("name")
                ]
                dosage_form = entry.get("dosage_form", "")
                route = ", ".join(entry.get("route") or [])
                labeler = entry.get("labeler_name", "")
                packed_text = _pack(
                    f"Medicine: {name}" if name else None,
                    f"Generic: {generic}" if generic else None,
                    f"Active ingredients: {'; '.join(active_ingredients)}" if active_ingredients else None,
                    f"Dosage form: {dosage_form}" if dosage_form else None,
                    f"Route: {route}" if route else None,
                    f"Labeler: {labeler}" if labeler else None,
                )
                return {
                    "source": "openfda",
                    "kind": "MEDICINE",
                    "product_name": name,
                    "brand": labeler,
                    "ingredients_text": "; ".join(active_ingredients),
                    "packed_text": packed_text,
                    "image_url": None,
                }
    return None


async def lookup_barcode(code: str, mode: str = "AUTO") -> dict[str, Any] | None:
    """Try the most relevant catalog first based on `mode`, fall back to the other."""
    code = re.sub(r"\s+", "", code or "")
    if not code:
        return None
    async with httpx.AsyncClient() as client:
        order = ["MEDICINE", "FOOD"] if mode.upper() == "MEDICINE" else ["FOOD", "MEDICINE"]
        for kind in order:
            if kind == "FOOD":
                result = await _lookup_food(client, code)
            else:
                result = await _lookup_medicine(client, code)
            if result:
                return result
    return None
