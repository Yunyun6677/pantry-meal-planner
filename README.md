# Pantry Meal Planner / 冰箱私厨

一个面向 Codex 的私人膳食规划 Skill：根据用户现有库存、口味、过敏与忌口、厨具、时间和营养偏好，推荐真正能做出来的家常餐，并解释制作方法、营养估算和库存变化。

> 本项目提供一般性的膳食规划与营养信息，不用于疾病诊断、治疗或替代医生/注册营养师的个体化建议。

## 它解决什么问题

- 严格零采购：缺少核心食材的菜不会混入推荐。
- 个性化约束：过敏、忌口和医生已明确的限制优先于口味偏好。
- 可执行菜谱：提供用量、火候、时间、熟度判断与实际可用替代。
- 可解释排序：兼顾库存覆盖、临期食材、时间、设备、口味与营养目标。
- 营养可追溯：由显式克重和外部营养表计算，不凭空给出精确数字。
- 连续库存：可输出本餐消耗量和预计余量，为下一餐继续规划。

## 项目结构

```text
pantry-meal-planner/
├── SKILL.md
├── agents/openai.yaml
├── references/
└── scripts/
examples/
tests/
```

Skill 使用渐进式披露：`SKILL.md` 保存核心决策流程，用户档案、推荐规则、营养安全和输出协议按实际任务加载。Python 脚本承担可重复的单位归一、筛选评分和营养计算。

## 安装

将 `pantry-meal-planner` 文件夹复制或克隆到 Codex 的 skills 目录：

```powershell
Copy-Item -Recurse .\pantry-meal-planner "$env:USERPROFILE\.codex\skills\pantry-meal-planner"
```

重新启动或刷新 Codex 后，可以直接描述做饭需求，或显式调用：

```text
Use $pantry-meal-planner. 我有4个鸡蛋、两个番茄和300克剩米饭，
不吃花生，只有炒锅，想在25分钟内做一人餐，不要让我购买新食材。
```

## 运行确定性工具

```powershell
python pantry-meal-planner/scripts/score_recipes.py examples/demo-request.json --today 2026-09-17
python pantry-meal-planner/scripts/calculate_nutrition.py examples/demo-nutrition.json
python -m unittest discover -s tests -v
```

`demo-nutrition.json` 中的数据只用于演示计算流程。生产应用应接入适用地区的权威食物成分数据库，保留数据来源和版本，并将结果标为估算值。

## 推荐的产品化架构

小程序或 Web 前端保存用户授权后的档案与库存；后端维护食材同义词、菜谱候选和营养数据；本 Skill 负责约束解析、候选生成、取舍解释和可执行菜谱。过敏过滤、库存扣减和营养计算应继续由确定性代码复核。

## 隐私和安全

- 只收集完成当前功能所需的健康信息，并允许用户查看、修改和删除。
- 健康数据、过敏信息和饮食记录不应进入公开日志或示例。
- 对严重过敏、儿童、孕期、进食障碍和治疗性饮食保持保守边界。
- 不保证“无过敏原”；包装标签、加工环境和交叉接触仍需用户核对。

## License

MIT
