# Creatly Canvas Plugin

通过另一套已经跑通的本地画布桥接调用 `/api/agent/mcp/tools` 与 `/api/agent/mcp/call`，直接使用当前画布 JSON。包含 film-narrative、film-cinematic-realism、film-creation 三个创作技能。

## 运行条件

- Node.js 22 或更新版本，安装宿主能从 PATH 找到 `node`。
- 本机运行支持 canvas bridge 的 creatly-fe（`pnpm dev:canvas`），并保持一个已登录画布页面打开。
- 默认连接 `http://127.0.0.1:3000`；自定义本地端口通过启动宿主时的 `YUANJI_CANVAS_URL` 环境变量设置。
- 这是本地桥接插件；仅登录线上网站不够。后端环境由前端配置决定，安装插件不会切换测试或生产环境。

插件带有自包含的 `mcp/canvas-mcp.cjs`，安装后不需要 npm install，也不需要 creatly-agent 服务。首次使用先 `canvas_status`，再 `canvas_describe_tools`。多页面时指定 clientId，工具定义从所选页面的实际后端发现。

## JSON 与工具

业务调用使用外层 projectId/baseVersion 等上下文与内层 payload。getCanvasContext 原样返回后端业务 JSON，大整数转成字符串；不会生成另一份可写 Film DSL。简单摘要可从结果整理，详细读取仅在后端实际提供时调用。本次没有新增后端 getCanvasDetail 接口。

工具数量由实时 `/tools` 决定，插件另提供三个连接/发现辅助工具。当前后端缺少的工具不会以静态目录冒充可用能力。模型不强制固定，遵循用户选择和实际 Schema。

## 安装

发布目录的根 README 提供 GitHub marketplace 安装命令。维护者可进入 `mcp/` 目录，执行 `npm ci`、`npm run build` 重建适配器，再执行 `npm run smoke` 做只读连接检查。

Codex 使用 `.mcp.json` 的 `${PLUGIN_ROOT}`；Claude Code 使用 `.mcp.claude.json`，WorkBuddy 使用内联配置 的 `${CLAUDE_PLUGIN_ROOT}`。需要支持插件路径变量的宿主版本。

## 验证与安全边界

`npm run plugin:check:mcp` 仅做初始化、连接状态和工具发现，不创建节点、不触发生成。前端未连接时会失败并给出诊断。

复用本机 bridge.token 和浏览器登录态；不打包凭据、不发送 token 到远程地址。适配器没有自动写入重试，超时须先读取原任务状态。长时间媒体任务用后端任务 ID 查询，MCP 工具超时不等于任务失败。

## 构建来源

MCP 适配器移植自 creatly-fe/scripts/canvas-mcp 的已验证流程。插件维护自己的可分发版本；不修改另一个任务运行中的 FE 或 Sky 服务。创作方法来自本仓库 Film Product，执行说明由 host/ 管理，skills/ 由投影脚本生成。
