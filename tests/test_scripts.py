import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "pantry-meal-planner" / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


normalize = load("normalize_inventory")
score = load("score_recipes")
nutrition = load("calculate_nutrition")


class InventoryTests(unittest.TestCase):
    def test_converts_kg_to_grams(self):
        result = normalize.normalize_item({"name": "rice", "quantity": 1.2, "unit": "kg"})
        self.assertEqual((result["quantity"], result["unit"]), (1200.0, "g"))

    def test_unknown_quantity_is_not_invented(self):
        result = normalize.normalize_item({"name": "spinach", "quantity": None, "unit": "g"})
        self.assertIsNone(result["quantity"])
        self.assertEqual(result["quantity_confidence"], "unknown")


class ScoringTests(unittest.TestCase):
    def test_allergy_and_missing_items_are_hard_filters(self):
        payload = {
            "mode": "strict_zero_shopping",
            "profile": {"allergies": ["peanut"], "equipment": ["stove"], "time_minutes": 20},
            "pantry": [{"name": "egg", "quantity": 2, "unit": "count"}],
            "recipes": [
                {"id": "eggs", "title": "Eggs", "required": [{"name": "egg", "quantity": 2, "unit": "count"}], "equipment": ["stove"], "time_minutes": 10},
                {"id": "peanut", "title": "Peanut eggs", "required": [{"name": "egg", "quantity": 2, "unit": "count"}], "allergens": ["peanut"], "equipment": ["stove"], "time_minutes": 10},
                {"id": "rice", "title": "Egg rice", "required": [{"name": "rice", "quantity": 100, "unit": "g"}], "equipment": ["stove"], "time_minutes": 10}
            ]
        }
        ranked = score.score_recipes(payload, date(2026, 9, 17))
        by_id = {x["id"]: x for x in ranked}
        self.assertTrue(by_id["eggs"]["feasible"])
        self.assertFalse(by_id["peanut"]["feasible"])
        self.assertFalse(by_id["rice"]["feasible"])


class NutritionTests(unittest.TestCase):
    def test_calculates_per_serving_and_reports_missing(self):
        result = nutrition.calculate({
            "servings": 2,
            "ingredients": [{"name": "a", "grams": 200}, {"name": "b", "grams": 10}],
            "nutrient_table": {"a": {"energy_kcal": 100, "protein_g": 10}}
        })
        self.assertEqual(result["per_serving"]["energy_kcal"], 100.0)
        self.assertEqual(result["per_serving"]["protein_g"], 10.0)
        self.assertIn("b: missing nutrient-table entry", result["missing"])


if __name__ == "__main__":
    unittest.main()
