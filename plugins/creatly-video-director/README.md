# Creatly Canvas Plugin · 生产环境

本分支 `main` 通过远程 MCP 连接 [yuanji.studio](https://yuanji.studio/)，无需启动本地画布服务。

## 环境对应

| 环境 | 网站 | GitHub 分支 |
| --- | --- | --- |
| 开发 | https://dev.yuanji.studio | dev |
| 测试 | https://test.yuanji.studio | test |
| 生产 | https://yuanji.studio | main |

安装的分支决定连接的环境，打开另一个网站不会自动切换插件。切换环境前，在宿主中移除旧的 `creatly` marketplace 来源，再添加目标分支并重新加载插件；在目标环境完成授权，确认账号与空间。三个环境不共用授权和画布数据。

## Codex 安装

```bash
codex plugin marketplace add https://github.com/loushengtao/creatly-canvas-plugin.git --ref main
codex plugin add creatly-video-director@creatly
```

## Claude Code 安装

```text
/plugin marketplace add https://github.com/loushengtao/creatly-canvas-plugin.git#main
/plugin install creatly-video-director@creatly
```

安装后开启新任务，使用 `/mcp` 或宿主提示完成 yuanji 的 OAuth 授权，在 **yuanji.studio** 登录。单纯打开网站不等于完成插件授权。

## WorkBuddy

下载 [main 分支 ZIP](https://github.com/loushengtao/creatly-canvas-plugin/archive/refs/heads/main.zip)，按宿主的本地 marketplace 安装流程导入。需要支持 HTTP MCP 与 OAuth；完整安装与授权流程尚未端到端验证。

## CLI / 手动 MCP 配置

Codex：

```bash
codex mcp add creatly --url https://yuanji.studio/api/agent/mcp/v2
codex mcp login creatly
```

Claude Code：

```text
claude mcp add --transport http creatly https://yuanji.studio/api/agent/mcp/v2
/mcp
```

手动 HTTP MCP 配置：

```json
{"mcpServers": {"creatly": {"type": "http", "url": "https://yuanji.studio/api/agent/mcp/v2"}}}
```

手动 MCP 配置不包含插件创作技能；已通过插件连接时无需重复添加。

## 创作与协议

三个技能共用远程连接：`film-narrative`（叙事短片）、`film-cinematic-realism`（写实电影）、`film-creation`（已有任务）。用户明确指定的模型与画质参数优先。

配置使用标准 HTTP MCP，由宿主管理 OAuth 授权与令牌刷新，不打包凭据。通过实时 `tools/list` 获取工具及 Schema，具体见 [执行协议](skills/film-creation/references/mcp-execution.md)。工具能力取决于对应环境的后端部署；插件升级不等于后端已发布，也不代表已完成付费生成验收。

仓库中的旧 stdio 适配器仅为历史开发工具，本版本插件不加载它。

## 维护环境版本

在仓库根目录执行 `python3 scripts/configure-environment.py production`，同步三个宿主的配置、版本、技能连接说明和安装文档；开发、测试、生产必须分别发布到 `dev`、`test`、`main`。

## 图片、视频、音频上传

配套后端部署后，使用统一的 `upload(action="prepare"|"complete")` 上传本地参考素材，不依赖浏览器交接。操作和限制见 [媒体上传说明](scripts/README.md)。

## 0.2.0 精简工具目录

新版后端默认提供 13 个工具（生成关闭时 12 个）：`listProjects`、`projectCreate`、`getCanvasContext`、`createNode`、`updateNode`、`deleteNodes`、`createSubject`、`upload`、`listGenerationModels`、`listSystemVoices`、`calculateCredits`、`generateNodes`、`getGenerationStatus`。

`getCanvasContext` 默认 compact，需要生成配置等详细信息时传 `detail="full"`；主体列表合入 `subjects`。`createSubject` 用 `kind="character"|"scene"|"prop"|"custom"` 选择主体类型，custom 使用实际分类 ID。

上传统一走 `upload`：`action="prepare"` 申请直传 → 本机上传原始字节 → `action="complete"` 登记。支持图片、视频、音频、文本（txt/md）；文本返回文件引用，需要在画布展示时再创建直接输入的文本节点。上传不自动发起生成。

先部署对应后端，再升级插件并重新连接 MCP。旧后端不会因为安装插件自动获得新工具；实时 `tools/list` 才是能力依据。默认目录不再提供 Film DSL、浏览器交接、独立确认或 previewAssemble。

### 0.2.1：已上传配音挂载

后端支持节点级 fileRef 后，可通过 createNode/updateNode 将已上传音频直接挂成节点的可播放文件，无需 TTS 或重复上传。已有音频可批量更新；挂载后读回 audioFiles。先部署配套后端，再更新插件并刷新 MCP 工具目录。

### 0.2.2：视频素材列表

配套后端支持多图片、多音频输入连线，人物正视图和跨镜头补拍图可作为视频参考。跨镜头引用时用显式 Shot 确定归属，多图采用 referenceImg，按素材顺序编写提示词编号。

### 0.2.3：正式主体库

`createSubject` 写入正式主体资产并应用到画布，支持人物、场景、道具及已有自定义分类。图片生成完成后自动归档主体素材。

`getCanvasContext` 同时返回主体分类、资产列表和画布主体；full 模式包含参考项和文件，subjectId/subjectQuery 可精读或检索。`updateNode` 支持 generationParams.elementBindings；使用返回的 mentionToken 在图片或视频提示词中 @ 主体，无需连线，也可指定主体素材子集。

需要部署配套主体库后端；插件刷新工具目录即可发现服务端参数，更新插件到 0.2.3 可获得新版调用说明。旧 triView 三视图参数仍兼容；新调用优先使用 threeView，造型使用 look。
