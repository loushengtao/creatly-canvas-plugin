---
name: film-creation
description: 继续已有的画布电影创作任务，通过当前画布 JSON 和实时 MCP 工具修改剧本、主体、分镜、媒体及成片。新作可选择 film-narrative 或 film-cinematic-realism。
---

# Film Creation

创作质量参考 [Film 质量基线](references/film-quality-baseline.md)、[工作计划方法](references/film-work-plan-method.md)、[工作计划建议](references/film-work-plan-propose.md) 与[连续性审查](references/film-continuity-review.md)。

所有执行先阅读 [MCP 执行协议](references/mcp-execution.md)。使用 `canvas_status` 和 `canvas_describe_tools` 发现实际能力，读取当前画布 JSON 后按明确范围更新节点。业务工具接收外层项目上下文与内层 payload，不使用旧文档中的 v2 参数。

沿用用户已有创作决定与执行授权；不重复要求已确认阶段。生成前检查真实节点、输入关系、媒体依赖与当前费用确认要求。受理不等于生成成功，完成状态不等于文件已挂载。超时先读原状态，不重复付费提交。
