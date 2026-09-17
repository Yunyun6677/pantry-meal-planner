#!/usr/bin/env python3
"""Calculate recipe nutrients from explicit gram weights and a per-100g table."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any

DEFAULT_FIELDS = ("energy_kcal", "protein_g", "fat_g", "carbohydrate_g", "fiber_g", "sodium_mg")


def calculate(payload: dict[str, Any]) -> dict[str, Any]:
    table = payload["nutrient_table"]
    servings = float(payload.get("servings", 1))
    if servings <= 0:
        raise ValueError("servings must be greater than zero")
    totals = {field: 0.0 for field in DEFAULT_FIELDS}
    missing, details = [], []
    for ingredient in payload.get("ingredients", []):
        name, grams = ingredient["name"], ingredient.get("grams")
        if grams is None:
            missing.append(f"{name}: missing gram weight")
            continue
        if float(grams) < 0:
            raise ValueError(f"grams cannot be negative for {name}")
        nutrients = table.get(name)
        if not nutrients:
            missing.append(f"{name}: missing nutrient-table entry")
            continue
        contribution = {}
        for field in DEFAULT_FIELDS:
            if field in nutrients:
                value = float(nutrients[field]) * float(grams) / 100.0
                totals[field] += value
                contribution[field] = round(value, 2)
        details.append({"name": name, "grams": float(grams), "contribution": contribution})
    return {"servings": servings, "recipe_total": {k: round(v, 2) for k, v in totals.items()},
            "per_serving": {k: round(v / servings, 2) for k, v in totals.items()},
            "missing": missing, "details": details, "source": payload.get("source"),
            "notice": "Estimate based on supplied edible weights and per-100g values."}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = calculate(json.loads(args.input.read_text(encoding="utf-8")))
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
