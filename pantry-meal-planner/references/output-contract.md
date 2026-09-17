# Output contract

## Human-readable response

Default structure:

1. `最推荐` — dish, why it fits, cook time, inventory match, and material uncertainty.
2. `另外两个选择` — concise alternatives with their tradeoffs.
3. `怎么做` — quantities, preparation, ordered steps, heat, timing, and doneness.
4. `营养概览` — per serving, source-backed estimate or qualitative description.
5. `库存变化` — consumed and expected remainder.
6. `安全提醒` — include only relevant warnings.

Avoid forcing this structure when the user asks only for inventory normalization or one recipe.

## Machine-readable recommendation

```json
{
  "mode": "strict_zero_shopping",
  "servings": 1,
  "recommendations": [
    {
      "recipe_id": "tomato_egg_rice",
      "title": "番茄鸡蛋盖饭",
      "feasible": true,
      "uncertainties": [],
      "why": ["所有必需食材已有", "25分钟内完成"],
      "ingredients": [],
      "steps": [],
      "nutrition_per_serving": {},
      "inventory_delta": []
    }
  ],
  "safety_notes": [],
  "assumptions": []
}
```

Do not mix an unavailable ingredient into `ingredients` in strict mode. Put optional, unavailable enhancements in a separate field if the application needs to display them.
