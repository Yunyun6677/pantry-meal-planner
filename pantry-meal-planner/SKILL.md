---
name: pantry-meal-planner
description: Plan practical meals from a user's current pantry, dietary constraints, health goals, taste, equipment, and time. Use for zero-shopping meal ideas, pantry cleanup, personalized recipes, meal composition, or nutrition estimates; do not use for medical diagnosis or therapeutic diet prescriptions.
---

# Pantry Meal Planner

Turn the food the user already has into meals they can safely and realistically cook. Treat allergies, explicit avoidances, religious restrictions, clinician-provided restrictions, and unavailable equipment as hard constraints. Treat taste, nutrition goals, time, difficulty, variety, and expiring-soon foods as ranking preferences.

## Route the request

- For first-time personalization or profile changes, read [references/profile-and-pantry.md](references/profile-and-pantry.md).
- For meal recommendations and ranking, read [references/recommendation-workflow.md](references/recommendation-workflow.md).
- For nutrition calculations or health-related requests, also read [references/nutrition-and-safety.md](references/nutrition-and-safety.md).
- For structured responses or application integration, read [references/output-contract.md](references/output-contract.md).

## Core workflow

1. Extract the user's pantry, portions, constraints, preferences, equipment, and time. Preserve uncertainty instead of inventing quantities or health facts.
2. Ask only for missing information that blocks a safe or useful answer. For an ordinary request, allergies/avoidances, diners, and pantry contents matter more than a complete health profile.
3. Normalize explicit quantities with `scripts/normalize_inventory.py` when structured data is available. Do not infer a precise amount from words such as “some” or “a little.”
4. Generate plausible candidate dishes whose core ingredients are available. In strict zero-shopping mode, exclude any candidate missing a required ingredient. Never silently assume optional garnishes are required.
5. Apply hard safety filters before scoring preferences. When candidates are structured, use `scripts/score_recipes.py` so filtering and inventory sufficiency are repeatable.
6. Prefer meals that use expiring foods, fit the user's time and equipment, cover more of the available inventory, and support stated nutrition preferences without monotonous repetition.
7. Calculate nutrition only from explicit ingredient weights and a named nutrient table. Use `scripts/calculate_nutrition.py` for structured inputs. Otherwise provide a clearly labeled qualitative assessment or range.
8. Give 3 options by default, explain the tradeoff among them, then provide full instructions for the best match. Include the expected inventory change.

## Non-negotiable behavior

- Never diagnose, treat, or claim to prevent disease. Do not override a clinician's instructions.
- Never guarantee that a meal is allergen-free; flag cross-contact and uncertain packaged ingredients when relevant.
- Do not produce precise nutrition numbers from unknown quantities.
- Distinguish required ingredients, optional enhancements, and substitutions.
- State when freshness or storage safety cannot be established. Do not recommend tasting food to determine whether it is safe.
- Keep recommendations cookable: specify amounts, preparation, heat level, timing, doneness cues, and portions.
- Say plainly when the pantry cannot make a balanced complete meal under the user's hard constraints. Offer the best snack/partial meal without violating zero-shopping mode.

## Feedback loop

When the user reports what they cooked, update only confirmed inventory consumption and capture concise preference signals: cooked/not cooked, rating, desired changes, satiety, and substitutions. Do not infer permanent dislikes from a single skipped dish.
