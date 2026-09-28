# 远程 MCP 执行协议（dev）

## 连接与授权

本分支直接连接 `https://dev.yuanji.studio/api/agent/mcp/v2`，使用标准 Streamable HTTP MCP 与 OAuth。无需本地画布服务、bridge.token 或保持浏览器画布打开。由宿主完成授权发现、浏览器登录、PKCE 和令牌刷新；不索取或复制用户密码、Cookie、Access Token，不使用本地桥接替代授权。

首次使用按宿主提示打开 dev 网站完成授权，确认账号和空间。通过标准 MCP `tools/list` 获取当前部署的工具及完整 inputSchema；不要调用旧本地适配器独有的 `canvas_status`、`canvas_describe_tools` 或 `canvas_list_projects`。若宿主已发现工具，直接读取其最新定义。使用 `listProjects` 返回的 `authorizationContext` 核对账号和空间；创建项目的回执也包含该字段。

工具不可用、未授权或权限不足时给出实际错误，不能使用过期工具目录冒充连接成功。项目与模型目录通过当前实际工具查询。

## 参数与画布状态

标准 v2 工具参数按实时 inputSchema **平铺**传递，不包裹旧版 `payload`，不传本地 `clientId`。projectId/nodeId 等使用服务端返回的原始不透明字符串，不解密、不转换成数据库数字，也不直接传整个 workbench URL。版本号和其他字段遵循实际 Schema 的类型。

先读取 `getCanvasContext(detail="compact")`，需要模型配置和资源详情时使用 `detail="full"`。主体分组在 `subjects` 中，保留节点、关系、位置、媒体、版本及状态摘要。读取返回的 scope 必须覆盖修改范围；过滤快照不能当作完整画布。缺少字段不等于空值，不建立另一个可写 Film DSL 副本。

写入按实时定义提供 `idempotencyKey`、`expectedNodeStates`、`expectedDeletion`、`expectedSourceFiles` 等所需字段。摘要来自当前快照，不能凭空补造；冲突后先重新读取并检查用户改动。相同操作使用稳定幂等键，参数改变视为新操作。工具失败或超时先查原状态，不自动重复写入或付费生成。

## 生成与交付

1. 用户明确要求生成后，读取节点、参考文件及实时模型配置，准备实际生成参数。
2. 未指定时默认 **Creatly Sigma 2.5 Sunburst、2K**。当前模型标识为 `gpt-image-2.5-sunburst`、function 为 `gpt25_sunburst`、modelConfigId 为 `image_gpt25_sunburst`、resolution 为 `2k`；以当前模型目录验证可用性。用户明确指定的模型、分辨率、质量和数量优先。默认模型不可用时说明缺口，不擅自换模型。
3. 节点配置、费用估算和生成请求参数保持一致。每批图片或视频生成前，在当前对话中说明目标节点、模型、数量与预计积分，取得用户明确同意；同一批已确认内容不重复询问。确认后直接调用 `generateNodes`，将用户同意的本批总积分作为 `maxCredits`，无需再打开画布或网页确认费用。报价超过上限、生成范围改变或失败重试时，回到对话重新确认，不擅自增加额度或重复提交。仅提高同一批的费用上限时沿用原幂等键；生成参数或节点范围改变时使用新键。若旧部署仍返回网页费用确认，说明需要更新后端，停止提交，不伪造确认凭据。
4. 提交后查询原任务，回读非空 frameFiles/videoFiles/audioFiles 等实际媒体；受理、生成终态、挂载和视觉验收分别判断。
5. 保留成功结果。用户指定的待处理节点保持原状，不因默认参数改变而重生成。没有像素或音频证据时，不宣称质量验收通过。
6. 使用返回的 `projectUrl` 交付画布链接。精简目录不包含 previewAssemble、浏览器交接或 Film DSL 工具。


## 本地参考素材上传

先通过实时工具目录确认 `upload` 已部署。使用插件 [本地上传脚本](../../../scripts/README.md)：本机计算文件元信息 → `upload(action="prepare")` → 本机按返回 URL/headers 直传原文件 → `upload(action="complete")` → 用返回的真实 `fileRef` 绑定节点并读回。支持图片、视频、音频和文本（txt/md）。媒体作为生成输入时用 referenceResource 绑定；文本只返回 fileRef，读取正文后用 createNode(type="text", content=正文) 直接展示，不把文本文件当图片参考。不通过浏览器交接完成上传，不把本地路径冒充远程资源 ID，不把 Base64 放入工具参数。签名 URL 只存私有临时文件，上传或登记超时先核对原 uploadId，不能自动重投或付费生成。宿主没有本地文件传输能力时明确说明缺口。

## 精简工具目录

默认最多 13 个工具：listProjects、projectCreate、getCanvasContext、createNode、updateNode、deleteNodes、createSubject、upload、listGenerationModels、listSystemVoices、calculateCredits、generateNodes、getGenerationStatus。以实时 tools/list 为准，生成能力可能关闭。createSubject(kind="character"|"scene") 建立人物/场景主体结构，不自动生成。删除一个或多个节点都使用 deleteNodes，在用户指定的删除范围内直接执行，无需网页确认或 confirmOperation。先读取目标 deletion 观察并传入 expectedDeletions，重试沿用原参数及幂等键。

节点连线使用 createNode/updateNode 的 parentIds：给 B 设置 parentIds=[A的ID] 建立 A → B。该字段替换完整输入列表，追加时保留已有 ID，[] 清空；parentNode 仅表示嵌套归属。需要指定参考图、首尾帧或音视频用途时同步设置 generationParams.referenceResources。

已上传配音需要作为节点自身播放文件时，使用 updateNode(nodes=[{nodeId, fileRef:{id:上传回执.fileRef.id}}])；20 条可一次批量挂载，按最新画布提供 expectedNodeStates 和幂等键。也可 createNode(nodes=[{clientRef,type:"audio",label,fileRef:{id}}]) 直接建可播放音频节点，此时 content 可省略。fileRef 仅传 id，目前只支持 audio，会替换当前播放文件。不重传已有文件，不调用 generateNodes 或 TTS；挂载后用 getCanvasContext 检查 audioFiles。仅用 SOURCE_AUDIO 参考或连线不会将文件挂成节点自身音频。以实时 Schema 含 fileRef 为前提，旧后端需要先部署更新。

视频可以连接多张分镜、人物正视图、补拍图以及多条音频，统一传入有序 parentIds 列表。跨镜头参考时显式加入本镜 Shot 并传 nodeIndex，人物图本身无需 Shot。多图模式使用 generationParams.videoType="referenceImg"；需要精确编号时按提示词顺序写 referenceResources，图片用 IMAGE/REFERENCE，配音用 AUDIO/SOURCE_AUDIO，分别对应图1…和音频1…。不要再将“一张图/一条音频”或“人物/补拍图不能连视频”当成通用限制。生成仍需核对具体模型的素材数量、格式与时长要求。首尾帧 keyframe 模式与多图 referenceImg 模式区分使用。
