# Creatly Canvas Plugin · 测试环境

本分支 `test` 通过远程 MCP 连接 [test.yuanji.studio](https://test.yuanji.studio/)，无需启动本地画布服务。

## 环境对应

| 环境 | 网站 | GitHub 分支 |
| --- | --- | --- |
| 开发 | https://dev.yuanji.studio | dev |
| 测试 | https://test.yuanji.studio | test |
| 生产 | https://yuanji.studio | main |

安装的分支决定连接的环境，打开另一个网站不会自动切换插件。切换环境前，在宿主中移除旧的 `creatly` marketplace 来源，再添加目标分支并重新加载插件；在目标环境完成授权，确认账号与空间。三个环境不共用授权和画布数据。

## Codex 安装

```bash
codex plugin marketplace add https://github.com/loushengtao/creatly-canvas-plugin.git --ref test
codex plugin add creatly-video-director@creatly
```

## Claude Code 安装

```text
/plugin marketplace add https://github.com/loushengtao/creatly-canvas-plugin.git#test
/plugin install creatly-video-director@creatly
```

安装后开启新任务，使用 `/mcp` 或宿主提示完成 yuanji 的 OAuth 授权，在 **test.yuanji.studio** 登录。单纯打开网站不等于完成插件授权。

## WorkBuddy

下载 [test 分支 ZIP](https://github.com/loushengtao/creatly-canvas-plugin/archive/refs/heads/test.zip)，按宿主的本地 marketplace 安装流程导入。需要支持 HTTP MCP 与 OAuth；完整安装与授权流程尚未端到端验证。

## CLI / 手动 MCP 配置

Codex：

```bash
codex mcp add creatly-test --url https://test.yuanji.studio/api/agent/mcp/v2
codex mcp login creatly-test
```

Claude Code：

```text
claude mcp add --transport http creatly-test https://test.yuanji.studio/api/agent/mcp/v2
/mcp
```

手动 HTTP MCP 配置：

```json
{"mcpServers": {"creatly-test": {"type": "http", "url": "https://test.yuanji.studio/api/agent/mcp/v2"}}}
```

手动 MCP 配置不包含插件创作技能；已通过插件连接时无需重复添加。

## 创作与协议

技能统一为 `film-skill`：一个入口覆盖剧本、选角、分镜、运镜、视频提示词、画布执行和剪辑，按叙事短片或写实电影路线推进，细节按需读取 `references/`。视频默认 Seedance 2.5、480p、开启音频；用户明确指定的模型、画质和音频参数优先。

配置使用标准 HTTP MCP，由宿主管理 OAuth 授权与令牌刷新，不打包凭据。通过实时 `tools/list` 获取工具及 Schema，具体见 [执行协议](plugins/creatly-video-director/skills/film-skill/references/mcp-execution.md)。工具能力取决于对应环境的后端部署；插件升级不等于后端已发布，也不代表已完成付费生成验收。

仓库中的旧 stdio 适配器仅为历史开发工具，本版本插件不加载它。

## 维护环境版本

在仓库根目录执行 `python3 scripts/configure-environment.py test`，同步三个宿主的配置、版本、技能连接说明和安装文档；开发、测试、生产必须分别发布到 `dev`、`test`、`main`。

## 生成确认

每批图片或视频生成前，在对话中确认节点、模型、数量和预计积分；确认后直接提交，无需再到画布或网页确认费用。插件将确认金额作为 `generateNodes.maxCredits`，超出金额或需要失败重试时重新在对话中确认。需要部署支持该流程的后端；更新插件后开启新任务以刷新工具定义。OAuth 登录授权仍由宿主完成。

## 0.2.0 精简工具目录

新版后端默认提供 13 个工具（生成关闭时 12 个）：`listProjects`、`projectCreate`、`getCanvasContext`、`createNode`、`updateNode`、`deleteNodes`、`createSubject`、`upload`、`listGenerationModels`、`listSystemVoices`、`calculateCredits`、`generateNodes`、`getGenerationStatus`。

`getCanvasContext` 默认 compact，需要生成配置等详细信息时传 `detail="full"`；主体列表合入 `subjects`。`createSubject` 用 `kind="character"|"scene"|"prop"|"custom"` 选择主体类型。

上传统一走 `upload`：`action="prepare"` 申请直传 → 本机上传原始字节 → `action="complete"` 登记。支持图片、视频、音频、文本（txt/md）；文本返回文件引用，需要在画布展示时再创建直接输入的文本节点。上传不自动发起生成。

先部署对应后端，再升级插件并重新连接 MCP。旧后端不会因为安装插件自动获得新工具；实时 `tools/list` 才是能力依据。默认目录不再提供 Film DSL、浏览器交接、独立确认或 previewAssemble。
