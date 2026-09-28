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

## 图片、视频、音频上传

配套后端部署后，使用统一的 `upload(action="prepare"|"complete")` 上传本地参考素材，不依赖浏览器交接。操作和限制见 [媒体上传说明](scripts/README.md)。

## 0.2.0 精简工具目录

新版后端默认提供 13 个工具（生成关闭时 12 个）：`listProjects`、`projectCreate`、`getCanvasContext`、`createNode`、`updateNode`、`deleteNodes`、`createSubject`、`upload`、`listGenerationModels`、`listSystemVoices`、`calculateCredits`、`generateNodes`、`getGenerationStatus`。

`getCanvasContext` 默认 compact，需要生成配置等详细信息时传 `detail="full"`；主体列表合入 `subjects`。`createSubject` 用 `kind="character"|"scene"` 选择主体类型。

上传统一走 `upload`：`action="prepare"` 申请直传 → 本机上传原始字节 → `action="complete"` 登记。支持图片、视频、音频、文本（txt/md）；文本返回文件引用，需要在画布展示时再创建直接输入的文本节点。上传不自动发起生成。

先部署对应后端，再升级插件并重新连接 MCP。旧后端不会因为安装插件自动获得新工具；实时 `tools/list` 才是能力依据。默认目录不再提供 Film DSL、浏览器交接、独立确认或 previewAssemble。

### 0.2.1：已上传配音挂载

后端支持节点级 fileRef 后，可通过 createNode/updateNode 将已上传音频直接挂成节点的可播放文件，无需 TTS 或重复上传。已有音频可批量更新；挂载后读回 audioFiles。先部署配套后端，再更新插件并刷新 MCP 工具目录。

### 0.2.2：视频素材列表

配套后端支持多图片、多音频输入连线，人物正视图和跨镜头补拍图可作为视频参考。跨镜头引用时用显式 Shot 确定归属，多图采用 referenceImg，按素材顺序编写提示词编号。
