# GitHub 调研与框架决策

调研日期：2026-09-18。基于官方项目文档，未进行这些产品的完整安装评测。

|项目|公开能力|借鉴与取舍|
|---|---|---|
|[Mealie](https://github.com/mealie-recipes/mealie)|菜谱、餐食计划、购物清单、API|菜谱与交互分层，未来可增加导入适配器|
|[Tandoor](https://github.com/TandoorRecipes/recipes)|菜谱管理、餐食计划、购物清单|明确食材用量和基准人数，支持按人数缩放|
|[Grocy](https://github.com/grocy/grocy)|家庭食品与库存管理|补货、消耗分离，库存配合事务流水|
|[LangGraph](https://docs.langchain.com/oss/python/langgraph/persistence)|工作流状态持久化与恢复|未来复杂模型工作流可用；首版SQLite足够|

以上为设计参考，没有复制第三方源码或集成服务。原Skill只有规则和独立脚本，没有真正跨会话记忆。新增工作流：中文解析→草稿确认→持久化→人数缩放与匹配→营养→确认做完→事务扣减。

## 已搭建的库

- foods：别名、计数估重、营养；recipes：基准份量、克重、步骤。
- pantry：可用库存；profile：默认人数。
- messages：输入历史，供回看，不用于推算库存。
- drafts：待确认入库草稿；plans：推荐快照和消费状态。
- events：盘点、补货、做饭流水，与库存原子提交。

PantryAgent是规则式工作流编排器，不是多个LLM专家。后续模型替换chat解析层；数据库写入继续走preview/apply/consume。精确库存无需向量检索。

## API及边界

GET /api/state；POST /api/chat (text)；/api/preview (text,mode=set/add)；/api/apply (id)；/api/recommend (people可选)；/api/cook (id)。

默认 data/pantry.sqlite3，Git忽略。仅127.0.0.1，单家庭无公网鉴权。推荐不预扣；各菜独立核算，不保证所有候选能同时做。做完确认时重查库存，不足整笔回滚，重复点击不会重复扣减。

10种食材、8道原创演示菜谱。营养是未逐条核验的近似值，个/根转克为估重。首版未接入原Skill的健康/过敏/保质期约束。后续营养数据需来源URL、food_id、版本、生熟状态及每100克值。后续可增批次、保质期、设备、口味、多人整餐优化、模型解析和小程序。

catalog.json首次启动插入种子，已有记录不覆盖；开发时用 --db 指向新库预览新种子，后续再加版本化迁移。
