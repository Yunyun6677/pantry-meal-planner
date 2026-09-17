#!/usr/bin/env python3
"""Normalize structured pantry quantities without guessing missing amounts."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any

MASS_TO_G = {"g": 1.0, "kg": 1000.0, "克": 1.0, "千克": 1000.0, "公斤": 1000.0}
VOLUME_TO_ML = {"ml": 1.0, "l": 1000.0, "毫升": 1.0, "升": 1000.0}
COUNT_UNITS = {"count", "piece", "pieces", "个", "只", "枚"}


def normalize_item(item: dict[str, Any]) -> dict[str, Any]:
    result = dict(item)
    quantity = result.get("quantity")
    unit = str(result.get("unit", "")).strip().lower()
    if quantity is None:
        result["quantity_confidence"] = result.get("quantity_confidence", "unknown")
        return result
    try:
        value = float(quantity)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid quantity for {result.get('name', '<unnamed>')}: {quantity}") from exc
    if value < 0:
        raise ValueError(f"Quantity cannot be negative for {result.get('name', '<unnamed>')}")
    if unit in MASS_TO_G:
        result.update(quantity=value * MASS_TO_G[unit], unit="g")
    elif unit in VOLUME_TO_ML:
        result.update(quantity=value * VOLUME_TO_ML[unit], unit="ml")
    elif unit in COUNT_UNITS:
        result.update(quantity=value, unit="count")
    else:
        result.update(quantity=value, unit=unit)
        result.setdefault("normalization_warning", "unrecognized unit; quantity preserved")
    result["quantity_confidence"] = result.get("quantity_confidence", "exact")
    return result


def normalize_inventory(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [normalize_item(item) for item in items]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="JSON array or object containing a pantry array")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    wrapped = isinstance(payload, dict)
    items = payload["pantry"] if wrapped else payload
    normalized = normalize_inventory(items)
    output = {**payload, "pantry": normalized} if wrapped else normalized
    rendered = json.dumps(output, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
