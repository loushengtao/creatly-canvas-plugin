# Creatly Canvas Plugin Marketplace

通过本地 MCP 桥接复用画布 JSON 与 /api/agent/mcp/tools、/api/agent/mcp/call。

## GitHub 安装

Codex：

```bash
codex plugin marketplace add https://github.com/loushengtao/creatly-canvas-plugin.git
codex plugin add creatly-video-director@creatly
```

Claude Code：

```text
/plugin marketplace add loushengtao/creatly-canvas-plugin
/plugin install creatly-video-director@creatly
```

安装后重新加载插件或开启新任务。

## 本地安装

解压发行包后：

```bash
codex plugin marketplace add /absolute/path/to/creatly-video-director-local
codex plugin add creatly-video-director@creatly
```

托管到 GitHub 后，把上述 marketplace add 的本地路径替换为本仓库的 HTTPS Git URL。私有仓库需要本机已配置 GitHub 访问权限。

Claude Code：

```text
/plugin marketplace add /absolute/path/to/creatly-video-director-local
/plugin install creatly-video-director@creatly
```

也可用 claude --plugin-dir /absolute/path/to/creatly-video-director-local/plugins/creatly-video-director 加载。
WorkBuddy 支持把 creatly-video-director-local.zip 添加为本地 marketplace，再安装相同插件 ID。

## 使用前

安装 Node.js >=22，启动 creatly-fe 的 pnpm dev:canvas 并保持画布页面登录。默认端口 3000；其他本地端口可设置 YUANJI_CANVAS_URL。仅打开线上网站不能代替本地桥接。

先 canvas_status 核对后端环境，再 canvas_describe_tools 获取工具。插件包含自带依赖的 stdio 适配器，不需要安装 npm 包。认证复用当前浏览器；不需要 v2 OAuth 或 Film DSL 编译流程。

三个技能使用同一个连接：film-narrative（叙事短片）、film-cinematic-realism（写实电影）、film-creation（已有任务）。

[完整插件说明](plugins/creatly-video-director/README.md)

## 更新

适配器源码与独立构建脚本位于 plugins/creatly-video-director/mcp；修改后在该目录执行 `npm ci` 和 `npm test`（包含构建与模拟桥接测试）。发布前执行 `npm run smoke` 做只读连接检查。脚本调用使用插件自带的 `mcp/canvas-call.cjs`，无需依赖前端源码；具体参数见完整插件说明。

从同一个 marketplace 更新插件后重新加载或开启新任务。源码中的工具由后端实时发现；getCanvasContext 返回后端实际 JSON，尚未部署的详细画布接口不由插件伪造。
