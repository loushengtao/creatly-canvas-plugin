---
name: film-creation
description: 继续已有的画布电影创作任务，通过当前画布 JSON 和实时 MCP 工具修改剧本、主体、分镜、媒体及成片。新作可选择 film-narrative 或 film-cinematic-realism。
---

# Film Creation

创作质量参考 [Film 质量基线](references/film-quality-baseline.md)、[工作计划方法](references/film-work-plan-method.md)、[工作计划建议](references/film-work-plan-propose.md) 与[连续性审查](references/film-continuity-review.md)。

所有执行先阅读 [MCP 执行协议](references/mcp-execution.md)。使用标准 MCP `tools/list` 发现实际能力，读取当前画布 JSON 后按明确范围更新节点。通过远程 v2 接口按实时 Schema 平铺传参，不使用本地桥接的 clientId 和 payload 包装。

沿用用户已有创作决定与执行授权；不重复要求已确认阶段。生成前检查真实节点、输入关系与媒体依赖；每批生成的范围及预计费用在对话中确认一次，确认后直接生成并传入 `maxCredits`，不再要求画布费用确认。受理不等于生成成功，完成状态不等于文件已挂载。超时先读原状态，不重复付费提交。

涉及已建角色的分镜和视频，生成前必须用 `[@角色名]` 提及该角色锁定身份（所有主体都只 @、不连线、不重复写 referenceResources），角色图未生成时先生成角色图；详见 MCP 执行协议「角色参考图（强制）」。

分镜 Frame 生成前必须先出本幕色卡图并做成色卡主体，每个分镜和视频都在提示词里 `[@色卡]` 控制色调；生成分镜和视频时，每个镜头建一个组，把该镜的分镜图、补拍图、音频和视频框在组内。详见 MCP 执行协议「色卡（强制，分镜前完成）」与「画布分组与排版（强制）」。
