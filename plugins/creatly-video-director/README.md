# Creatly Canvas Plugin · Dev

本分支通过远程 MCP 直接连接 [元极开发站点](https://dev.yuanji.studio/)，无需启动本地画布服务。

## Codex 安装

```bash
codex plugin marketplace add https://github.com/loushengtao/creatly-canvas-plugin.git --ref dev
codex plugin add creatly-video-director@creatly
```

安装后开启新任务，在宿主提示的 dev 网站授权页面登录并确认账号与空间。单纯打开网站不等于完成插件授权。已安装其他分支时先在宿主中移除旧的 creatly marketplace 来源，再添加 dev，避免同名来源仍指向旧分支。

## Claude Code 安装

```text
/plugin marketplace add https://github.com/loushengtao/creatly-canvas-plugin.git#dev
/plugin install creatly-video-director@creatly
```

使用 `/mcp` 完成 yuanji 的 OAuth 授权。WorkBuddy 用户可下载本仓库 dev 分支源码 ZIP，按宿主的本地 marketplace 安装流程导入；宿主需支持 HTTP MCP 与 OAuth，未完成端到端兼容验证。

## CLI / 手动 MCP 配置

```bash
codex mcp add creatly-dev --url https://dev.yuanji.studio/api/agent/mcp/v2
codex mcp login creatly-dev
```

手动 MCP 配置可独立测试连接，不包含插件创作技能。已通过插件连接时无需重复添加。

## 创作

三个技能共用远程连接：`film-narrative`（叙事短片）、`film-cinematic-realism`（写实电影）、`film-creation`（已有任务）。默认生图模型为 **Creatly Sigma 2.5 Sunburst、2K**，用户明确指定的参数优先。

安装后可说：“使用 film-narrative，在 dev 站点创建一个短片项目，先完善剧本与人物设定；生成前告诉我预计费用。”

## 环境与协议

- 本分支 `dev` 固定连接 `https://dev.yuanji.studio/api/agent/mcp/v2`。
- Codex、Claude Code 和 WorkBuddy 配置统一使用 HTTP MCP；认证令牌由宿主管理，不打包凭据。
- 通过 `tools/list` 获取当前工具和 Schema，参数平铺，不使用旧本地 clientId/payload 包装。具体见 [执行协议](skills/film-creation/references/mcp-execution.md)。
- 仓库 `mcp/` 中原有本地 stdio 适配器作为旧开发工具保留，但本分支插件不加载它；它不能当作远程 CLI 使用。
- main 仍保留此前发布的版本。未来生产发布必须显式配置并验证生产站点，不把 dev 地址当作生产地址。

## 验证

开发站点的 OAuth 元数据返回 200，未授权 MCP 请求返回 401 并提供正确的授权发现地址。已通过 Codex 完成 OAuth 登录并发现 19 个远程工具，包括项目、画布、模型查询和生成工具。尚未执行付费生成，工具发现不等于生图验收。
