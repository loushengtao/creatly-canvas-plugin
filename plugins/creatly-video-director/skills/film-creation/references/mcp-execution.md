# 远程 MCP 执行协议（dev）

## 连接与授权

本分支直接连接 `https://dev.yuanji.studio/api/agent/mcp/v2`，使用标准 Streamable HTTP MCP 与 OAuth。无需本地画布服务、bridge.token 或保持浏览器画布打开。由宿主完成授权发现、浏览器登录、PKCE 和令牌刷新；不索取或复制用户密码、Cookie、Access Token，不使用本地桥接替代授权。

首次使用按宿主提示打开 dev 网站完成授权，确认账号和空间。通过标准 MCP `tools/list` 获取当前部署的工具及完整 inputSchema；不要调用旧本地适配器独有的 `canvas_status`、`canvas_describe_tools` 或 `canvas_list_projects`。若宿主已发现工具，直接读取其最新定义。若提供 `getAuthorizationContext`，用它核对授权上下文。

工具不可用、未授权或权限不足时给出实际错误，不能使用过期工具目录冒充连接成功。项目与模型目录通过当前实际工具查询。

## 参数与画布状态

标准 v2 工具参数按实时 inputSchema **平铺**传递，不包裹旧版 `payload`，不传本地 `clientId`。projectId/nodeId 等使用服务端返回的原始不透明字符串，不解密、不转换成数据库数字，也不直接传整个 workbench URL。版本号和其他字段遵循实际 Schema 的类型。

先读取 `getCanvasContext`，保留节点、关系、位置、媒体、版本及状态摘要。读取返回的 scope 必须覆盖修改范围；过滤快照不能当作完整画布。缺少字段不等于空值，不建立另一个可写 Film DSL 副本。

写入按实时定义提供 `idempotencyKey`、`expectedNodeStates`、`expectedDeletion`、`expectedSourceFiles` 等所需字段。摘要来自当前快照，不能凭空补造；冲突后先重新读取并检查用户改动。相同操作使用稳定幂等键，参数改变视为新操作。工具失败或超时先查原状态，不自动重复写入或付费生成。

## 生成与交付

1. 用户明确要求生成后，读取节点、参考文件及实时模型配置，准备实际生成参数。
2. 未指定时默认 **Creatly Sigma 2.5 Sunburst、2K**。当前模型标识为 `gpt-image-2.5-sunburst`、function 为 `gpt25_sunburst`、modelConfigId 为 `image_gpt25_sunburst`、resolution 为 `2k`；以当前模型目录验证可用性。用户明确指定的模型、分辨率、质量和数量优先。默认模型不可用时说明缺口，不擅自换模型。
3. 节点配置、费用估算和生成请求参数保持一致。按实际后端流程估算并取得必要确认；需要浏览器确认时使用服务端返回的确认链接，不伪造 confirmationTaskId 或绕过授权。
4. 提交后查询原任务，回读非空 frameFiles/videoFiles/audioFiles 等实际媒体；受理、生成终态、挂载和视觉验收分别判断。
5. 保留成功结果。用户指定的待处理节点保持原状，不因默认参数改变而重生成。没有像素或音频证据时，不宣称质量验收通过。
6. 按实际工具提供的预览与项目链接交付；浏览器交接仅使用服务端生成的链接，不复制凭据到网址或文件。
