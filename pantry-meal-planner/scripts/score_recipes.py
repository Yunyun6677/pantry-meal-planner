#!/usr/bin/env python3
"""Filter and rank structured recipes against a pantry and user profile."""
from __future__ import annotations
import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any


def _key(value: str) -> str:
    return value.strip().casefold().replace(" ", "_")


def _blocked(recipe: dict[str, Any], exclusions: set[str]) -> list[str]:
    present = {_key(i["name"]) for i in recipe.get("required", []) + recipe.get("optional", [])}
    present.update(_key(a) for a in recipe.get("allergens", []))
    return sorted(present & exclusions)


def score_recipes(payload: dict[str, Any], today: date | None = None) -> list[dict[str, Any]]:
    today = today or date.today()
    profile = payload.get("profile", {})
    pantry = {_key(i.get("canonical_name") or i["name"]): i for i in payload.get("pantry", [])}
    exclusions = {_key(x) for x in profile.get("allergies", []) + profile.get("avoid", []) + profile.get("clinician_restrictions", [])}
    equipment = {_key(x) for x in profile.get("equipment", [])}
    preferred_tags = {_key(x) for x in profile.get("goals", []) + profile.get("preferred_tags", [])}
    time_limit = profile.get("time_minutes")
    strict = payload.get("mode", "strict_zero_shopping") == "strict_zero_shopping"
    ranked: list[dict[str, Any]] = []

    for recipe in payload.get("recipes", []):
        reasons, missing, uncertain = [], [], []
        blocked = _blocked(recipe, exclusions)
        required_equipment = {_key(x) for x in recipe.get("equipment", [])}
        unavailable_equipment = sorted(required_equipment - equipment)
        coverage_count, expiring_bonus = 0, 0.0
        for need in recipe.get("required", []):
            name = _key(need["name"])
            have = pantry.get(name)
            if not have:
                missing.append(need["name"])
                continue
            coverage_count += 1
            have_qty, need_qty = have.get("quantity"), need.get("quantity")
            same_unit = have.get("unit") == need.get("unit")
            if have_qty is None or need_qty is None or not same_unit:
                uncertain.append(need["name"])
            elif float(have_qty) < float(need_qty):
                missing.append(need["name"])
            use_by = have.get("use_by")
            if use_by:
                try:
                    days = (date.fromisoformat(use_by) - today).days
                    if 0 <= days <= 3:
                        expiring_bonus += 8.0 - (2.0 * days)
                except ValueError:
                    uncertain.append(f"{need['name']}:use_by")
        feasible = not blocked and not unavailable_equipment and (not strict or not missing)
        if not feasible:
            ranked.append({"id": recipe.get("id"), "title": recipe.get("title"), "feasible": False,
                           "score": None, "blocked": blocked, "missing": missing,
                           "unavailable_equipment": unavailable_equipment, "uncertain": sorted(set(uncertain))})
            continue
        total_required = max(1, len(recipe.get("required", [])))
        recipe_score = 50.0 * coverage_count / total_required + expiring_bonus
        tags = {_key(x) for x in recipe.get("tags", [])}
        matched_tags = sorted(tags & preferred_tags)
        recipe_score += 6.0 * len(matched_tags)
        if time_limit is not None:
            if recipe.get("time_minutes", 10**9) <= time_limit:
                recipe_score += 10.0
                reasons.append("within_time_limit")
            else:
                recipe_score -= min(20.0, float(recipe["time_minutes"] - time_limit))
        if not missing:
            reasons.append("all_required_ingredients_available")
        if expiring_bonus:
            reasons.append("uses_food_due_soon")
        ranked.append({"id": recipe.get("id"), "title": recipe.get("title"), "feasible": True,
                       "score": round(recipe_score, 2), "reasons": reasons, "matched_tags": matched_tags,
                       "missing": missing, "uncertain": sorted(set(uncertain))})
    return sorted(ranked, key=lambda x: (x["feasible"], x["score"] if x["score"] is not None else -1), reverse=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--today", type=date.fromisoformat, help="ISO date for reproducible tests")
    args = parser.parse_args()
    result = score_recipes(json.loads(args.input.read_text(encoding="utf-8")), args.today)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
