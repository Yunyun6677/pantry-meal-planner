# Profile and pantry model

Collect only what is relevant to the current request. Health data is sensitive: do not require it merely to suggest an ordinary meal.

## User profile

```json
{
  "people": 1,
  "age_group": "adult",
  "body": {"height_cm": null, "weight_kg": null},
  "activity_level": "moderate",
  "goals": ["higher_protein"],
  "allergies": ["peanut"],
  "avoid": ["cilantro"],
  "clinician_restrictions": [],
  "preferences": {"cuisines": ["Chinese home cooking"], "spice": 2, "oil": "light"},
  "skill_level": "beginner",
  "equipment": ["stove", "wok", "rice_cooker"],
  "time_minutes": 30
}
```

Height and weight are optional unless the user specifically requests energy or macronutrient targets. Do not calculate targets for children, pregnancy, eating disorders, or disease treatment without an appropriate professional plan supplied by the user.

## Pantry item

```json
{
  "name": "鸡胸肉",
  "canonical_name": "chicken_breast",
  "quantity": 350,
  "unit": "g",
  "state": "raw",
  "storage": "refrigerated",
  "opened": true,
  "use_by": "2026-09-18",
  "quantity_confidence": "exact"
}
```

Preserve the user's original name. Canonical names are for matching, not for overwriting their language. Use `quantity: null` and `quantity_confidence: "unknown"` when no defensible amount is available.

## Pantry assumptions

- Maintain a user-configurable list of staple condiments. Do not assume oil, salt, aromatics, or sauces are present unless the user has opted into that assumption.
- Leftovers need preparation date, storage method, and reheating context when safety depends on them.
- “Best before” and “use by” are not interchangeable. If labeling or storage is unclear, communicate the uncertainty.
- When a package contains mixed or processed food, retain its label and allergen information rather than reducing it to a generic ingredient.
