# Recommendation workflow

## Candidate recipe schema

Each candidate should specify `required`, `optional`, `equipment`, `time_minutes`, `servings`, `tags`, and a stable `id`. Ingredient entries contain `name`, `quantity`, and `unit`. A substitution is not available merely because it is imaginable; it must be present in the pantry and compatible with hard constraints.

## Filter before ranking

Reject a candidate when:

- it contains an allergy, explicit avoidance, or clinician-provided exclusion;
- a required ingredient is missing in strict zero-shopping mode;
- a known required quantity exceeds inventory;
- required equipment is unavailable;
- food freshness or storage information indicates it should not be used.

If quantity is unknown, label sufficiency as uncertain instead of claiming the recipe fits.

## Ranking priorities

Use these priorities as a starting point rather than a medical formula:

1. Inventory coverage and zero-shopping feasibility.
2. Foods that should be used soon, provided they remain safe.
3. User taste and cuisine preferences.
4. Time, skill, and equipment fit.
5. Stated nutrition preference and meal balance.
6. Variety relative to recent meals.

`scripts/score_recipes.py` implements a transparent default score for structured candidates. Explain the major reason behind the ordering instead of exposing meaningless decimal precision.

## Recipe instructions

For the selected dish, include servings and ingredient quantities, preparation order, heat setting and time, observable doneness cues, safe handling cues where relevant, substitutions actually in the pantry, and consumed and remaining inventory.

Prefer three meaningfully different options. Do not generate superficial variants that differ only by garnish.
