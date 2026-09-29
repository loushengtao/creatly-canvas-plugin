# 远程 MCP 执行协议（dev）

## 连接与授权

本分支直接连接 `https://dev.yuanji.studio/api/agent/mcp/v2`，使用标准 Streamable HTTP MCP 与 OAuth。无需本地画布服务、bridge.token 或保持浏览器画布打开。由宿主完成授权发现、浏览器登录、PKCE 和令牌刷新；不索取或复制用户密码、Cookie、Access Token，不使用本地桥接替代授权。

首次使用按宿主提示打开插件配置的站点完成授权，确认账号和空间。通过标准 MCP `tools/list` 获取当前部署的工具及完整 inputSchema；不要调用旧本地适配器独有的 `canvas_status`、`canvas_describe_tools` 或 `canvas_list_projects`。若宿主已发现工具，直接读取其最新定义。使用 `listProjects` 返回的 `authorizationContext` 核对账号和空间；创建项目的回执也包含该字段。

工具不可用、未授权或权限不足时给出实际错误，不能使用过期工具目录冒充连接成功。项目与模型目录通过当前实际工具查询。

## 参数与画布状态

标准 v2 工具参数按实时 inputSchema **平铺**传递，不包裹旧版 `payload`，不传本地 `clientId`。projectId/nodeId 等使用服务端返回的原始不透明字符串，不解密、不转换成数据库数字，也不直接传整个 workbench URL。版本号和其他字段遵循实际 Schema 的类型。

先读取 `getCanvasContext(detail="compact")`，需要模型配置和资源详情时使用 `detail="full"`。主体分组在 `subjects` 中，保留节点、关系、位置、媒体、版本及状态摘要。读取返回的 scope 必须覆盖修改范围；过滤快照不能当作完整画布。缺少字段不等于空值，不建立另一个可写 Film DSL 副本。

主体读取仍使用 `getCanvasContext`：`subjects.subjectTypes` 是当前可用分类（含已有“其他”分类），`subjects.elements` 是正式主体资产；`detail="full"` 返回 assets、fileRefList、referenceLayout，可传 subjectId 精读或 subjectQuery 搜索。结果最多 100 个主体，缺少目标时精读或搜索，不推断主体不存在。character/environment/product/custom 分组中的 id/subjectNodeId 是画布节点，elementId 才是主体资产 ID；不要互换。

引用优先用读取结果的 mentionToken（例如 `[@主体资产ID]` 或 `[@主体节点ID]`），重名时不用裸名称。需要选定参考图时，在 createNode/updateNode 的 generationParams.elementBindings 中传 elementId、与提示词 token 一致的 mentionId、referenceMode="ASSET_SUBSET"、selectedAssetIds；附件 ID 来自 assets，不能用文件 ID 代替。引用整个主体使用 WHOLE_ELEMENT。不需要连线；更新后用 full 回读 elementBindings 核验。资产已存在但尚未应用到画布，也可按 elementId 引用。

createSubject 返回 elementId、subjectNodeId、generationNodeIds 和 assetTaskPlans；建档不扣费，生成仍走 calculateCredits → 用户确认费用 → generateNodes。成功图片由服务端归档到主体素材，随后精读主体核验；不要手工回写结果或因待生成而重建主体。角色的基础三视图用 threeView，旧 triView 仍是三视图别名，新造型用 look。

写入按实时定义提供 `idempotencyKey`、`expectedNodeStates`、`expectedDeletion`、`expectedSourceFiles` 等所需字段。摘要来自当前快照，不能凭空补造；冲突后先重新读取并检查用户改动。相同操作使用稳定幂等键，参数改变视为新操作。工具失败或超时先查原状态，不自动重复写入或付费生成。

## 生成与交付

1. 用户明确要求生成后，读取节点、参考文件及实时模型配置，准备实际生成参数。
2. 未指定时默认 **Creatly Sigma 2.5 Sunburst、2K**。当前模型标识为 `gpt-image-2.5-sunburst`、function 为 `gpt25_sunburst`、modelConfigId 为 `image_gpt25_sunburst`、resolution 为 `2k`；以当前模型目录验证可用性。用户明确指定的模型、分辨率、质量和数量优先。默认模型不可用时说明缺口，不擅自换模型。
3. 节点配置、费用估算和生成请求参数保持一致。每批图片或视频生成前，在当前对话中说明目标节点、模型、数量与预计积分，取得用户明确同意；同一批已确认内容不重复询问。确认后直接调用 `generateNodes`，将用户同意的本批总积分作为 `maxCredits`，无需再打开画布或网页确认费用。报价超过上限、生成范围改变或失败重试时，回到对话重新确认，不擅自增加额度或重复提交。仅提高同一批的费用上限时沿用原幂等键；生成参数或节点范围改变时使用新键。若旧部署仍返回网页费用确认，说明需要更新后端，停止提交，不伪造确认凭据。
4. 提交后查询原任务，回读非空 frameFiles/videoFiles/audioFiles 等实际媒体；受理、生成终态、挂载和视觉验收分别判断。
5. 保留成功结果。用户指定的待处理节点保持原状，不因默认参数改变而重生成。没有像素或音频证据时，不宣称质量验收通过。
6. 使用返回的 `projectUrl` 交付画布链接。精简目录不包含 previewAssemble、浏览器交接或 Film DSL 工具。


## 角色参考图（强制）

凡是画面中出现已建角色的 Frame 或 Video，生成前必须垫该角色的参考图来固定身份，没有例外：

1. 先有角色图：角色主体至少 3 个视角（正视图 + 侧/背视图或三视图）必须已经生成并回读到非空 frameFiles。角色图还没生成时，先生成角色图，不生成依赖它的分镜或视频。用户提供了真人照片或剧照时，先用这些照片垫图生成角色正视图，再用正视图垫分镜。
2. 用主体提及锁定，不连线：凡是涉及主体（角色、场景、色卡等）的 Frame 和 Video，都在提示词里用 `[@主体名]` 提及（画布保存后可能显示为 `[@主体ID]`，两种写法等价），系统据此建立正式 elementBindings 并带入主体素材；只有历史画布主体使用 mentionElementIds。主体不写进 `parentIds`，也不把主体图重复写进 referenceResources。Video 的 referenceResources 只放本镜分镜、补拍图和音频，提示词里原来的【图N】角色行改写成「[@角色名]：锁定的特征」，其余【图N】按新顺序重新编号。
3. 每个出场角色各垫一张：双人或多人镜头要把每个出场角色的正视图都垫上；只露背影、肩膀或手的角色同样要垫，以锁定服装与发型。
4. 提示词写明引用职责：说明每张参考图锁定什么（脸、发型、帽子、服装），并写明参考图不决定构图。
5. 生成前回读核对：用 `getCanvasContext(detail="full")` 检查每个待生成节点的提示词都用 `[@角色名]` 提及了全部出场角色；缺任何一个就先补齐，不提交 generateNodes。
6. 改角色图后传播：角色正视图重新生成后，列出所有引用它的分镜和视频，按用户确认的范围重生。

## 视频参考素材（全能参考，强制）

视频默认走全能参考（`videoType="referenceImg"`）：只垫资产，镜头关系写进提示词。

1. 垫什么：
   - 人物：每个出场角色至少 3 个视角（正视图 + 侧视图 / 背视图，或正视图 + 三视图）。角色主体里不足 3 个视角时，先补齐再出视频。
   - 道具：本镜出现、需要跨镜一致的关键道具，各一张或多角度。
   - 场景：本镜所在场景的空间图，覆盖本镜机位朝向（门窗、吧台、桌椅等地标可见）。
   - 站位图：每个场景一张站位图（俯视或大全景），标出每个人的位置、朝向、关键道具和摄影机轴线；站位在场景中途改变时（如起身、离场），按状态各出一张，标题写成 `站位｜<场景>｜<状态>`。
2. 不垫什么：正反打、过肩、补拍等镜头画面不作为视频参考；正反打、对白覆盖、机位切换全部写在提示词里。只有用户明确要求锁定构图或首尾帧时，才额外垫本镜分镜图（此时改用图片优先路线，并在回复中说明）。
3. 有几张垫几张：在模型上限内尽量把上述资产垫全。上限以 `listGenerationModels(scene="video", modelIds=[...], detail="full")` 返回的 `scenarioCapabilities.multi_graph.rules.inputs.referenceImages.max` 为准（元极 Seedance 2.5 当前为 30 张图、10 条音频），不按经验值写死；超出上限时按「本镜出场人物 → 站位图 → 场景 → 道具」的优先级取舍。
4. 怎么传：角色、场景、道具、色卡等主体在提示词里 `[@主体名]`，不连线；站位图和主体里没有的补充视角写进 `referenceResources`，不连线。生成前回读，核对实际传入张数与提示词里的【图N】编号一致；`@` 只带入主体主图时，把其余视角补进 referenceResources。
5. 提示词里写清正反打：参考职责之后写「执行与连续性」，明确轴线（谁在画面左、谁在右）、屏幕方向、每个镜头块的景别与机位（如「正打，越过汤米右肩拍亚瑟」），镜头块之间独立一行 `HARD CUT`。

## 强制关卡与用户自由度

下面几项是默认强制关卡，不满足就不提交对应的 generateNodes：

- 分镜前：色卡主体已有图片。
- 视频前：本镜出场角色各有至少 3 个视角；有场景图和对应状态的站位图；提示词 `[@]` 了全部出场主体，并写清轴线和正反打；每个镜头的物料已放进本镜组。
- 生成前：回读画布，把 `getCanvasContext(detail="full")` 存成 JSON，运行插件的 `scripts/film_gate_check.py`（用法见 scripts/README.md「生成前门禁」）；有未豁免的 FAIL 不提交 generateNodes。本批范围与费用已在对话中确认。

用户可以对任一关卡明确说「跳过」或「这次不用」，照做即可（运行门禁时用 `--skip <关卡名>`）：在回复里点明跳过了哪一项、可能的影响，不反复劝阻。风格、景别、镜头数量、时长、垫图多少、是否先出分镜图等创作选择由用户决定，skill 只给默认值和建议，不替用户做硬性决定。

## 色卡（强制，分镜前完成）

分镜图的色调由色卡控制。生成任何分镜 Frame 之前，先为本幕（色调不同的 Scene 各一张）生成色卡图，用户认可后再出分镜：

1. 顺序：风格参考 / 剧照复刻 → 角色与场景主体 → **色卡** → 分镜 Frame → Video。没有色卡时不提交分镜 Frame 的 generateNodes。
2. 色卡内容：一张 16:9 图片，按暗部、中间调、高光三档排列 8–10 个色块，每块标注 HEX；来源是已认可的参考剧照或已定稿画面的真实取色（按亮度分档取色），不要凭空编色。可以本地取色后拼图上传，也可以在画布上用图片模型生成色卡 Frame。
3. 做成色卡主体：新建一个 `type=element` 的色卡主体（如「色卡」），把色卡图片放进该主体，排在分镜组之前（画布上方或左侧，与角色主体同一排）。
4. 引用方式：每个分镜 Frame 和 Video 的提示词都用 `[@色卡]` 提及色卡主体，不连线，也不再把色卡图写进 referenceResources。
5. 生成前用 `getCanvasContext(detail="full")` 回读，确认每个待生成节点的提示词都含 `[@色卡]` 和全部出场角色的 `[@角色名]`，且色卡主体里有图片。
6. 提示词：加一行「【色卡】[@色卡] …」，写明它只锁定色调、明暗比例和饱和度，不决定构图、人物和道具，并抄录关键 HEX（如「暗部 #0F0D0A–#282017，中间调 #312C25–#6A523A，高光只在光源附近 #937151–#E4C59F」）。
7. 换色调（如日景转夜景、换场景）时新建对应色卡，不沿用旧色卡。

## 画布分组与排版（强制）

生成分镜图和视频时，必须用组框住每个镜头的相关物料，先建组、再生成，不把节点散放在画布上。

- 每个 Shot 建一个 `type=group` 的组（`content` 不能为空，可填组名），把该镜的分镜图、补拍图、音频和视频的 `parentNode` 设为该组；Shot 与 Scene 的结构归属来自 `parentIds` 连线和 nodeIndex，改 parentNode 不影响结构。
- 风格参考（剧照复刻）单独建一个组；色卡、角色、场景做成主体，放在同一排。过时版本直接用 deleteNodes 删除，不留存档区。
- `position` 相对于 `parentNode` 计算：组内子节点写相对坐标（建议从 (20, 46) 起，给组标题留出空间），组本身写绝对坐标。通过 MCP 写入不会自动适配尺寸，必须给组写 `dimensions`，否则只显示 284×160。
- 组内固定列：分镜图 → 音频列（每条 260×56，间距 72）→ 视频 → 补拍图，音频和图片不重叠。站位图放在对应场景主体旁或「风格参考」组里，跨镜复用。
- 连线只保留结构和生成必需的：Frame → 本镜 Shot；Video ← 本镜 Frame（归属用）、音频。所有主体都不连线，只在提示词里 `[@主体名]`。

## 本地参考素材上传

先通过实时工具目录确认 `upload` 已部署。使用插件 [本地上传脚本](../../../scripts/README.md)：本机计算文件元信息 → `upload(action="prepare")` → 本机按返回 URL/headers 直传原文件 → `upload(action="complete")` → 用返回的真实 `fileRef` 绑定节点并读回。支持图片、视频、音频和文本（txt/md）。媒体作为生成输入时用 referenceResource 绑定；文本只返回 fileRef，读取正文后用 createNode(type="text", content=正文) 直接展示，不把文本文件当图片参考。不通过浏览器交接完成上传，不把本地路径冒充远程资源 ID，不把 Base64 放入工具参数。签名 URL 只存私有临时文件，上传或登记超时先核对原 uploadId，不能自动重投或付费生成。宿主没有本地文件传输能力时明确说明缺口。

## 精简工具目录

默认最多 13 个工具：listProjects、projectCreate、getCanvasContext、createNode、updateNode、deleteNodes、createSubject、upload、listGenerationModels、listSystemVoices、calculateCredits、generateNodes、getGenerationStatus。以实时 tools/list 为准，生成能力可能关闭。createSubject(kind="character"|"scene"|"prop"|"custom") 将正式主体写入用户可见的主体库并应用到画布，不自动生成；custom 必须使用当前 subjectTypes 中真实存在的 subjectTypeId。删除一个或多个节点都使用 deleteNodes，在用户指定的删除范围内直接执行，无需网页确认或 confirmOperation。先读取目标 deletion 观察并传入 expectedDeletions，重试沿用原参数及幂等键。

节点连线使用 createNode/updateNode 的 parentIds：给 B 设置 parentIds=[A的ID] 建立 A → B。该字段替换完整输入列表，追加时保留已有 ID，[] 清空；parentNode 仅表示嵌套归属。需要指定参考图、首尾帧或音视频用途时同步设置 generationParams.referenceResources。

已上传配音需要作为节点自身播放文件时，使用 updateNode(nodes=[{nodeId, fileRef:{id:上传回执.fileRef.id}}])；20 条可一次批量挂载，按最新画布提供 expectedNodeStates 和幂等键。也可 createNode(nodes=[{clientRef,type:"audio",label,fileRef:{id}}]) 直接建可播放音频节点，此时 content 可省略。fileRef 仅传 id，目前只支持 audio，会替换当前播放文件。不重传已有文件，不调用 generateNodes 或 TTS；挂载后用 getCanvasContext 检查 audioFiles。仅用 SOURCE_AUDIO 参考或连线不会将文件挂成节点自身音频。以实时 Schema 含 fileRef 为前提，旧后端需要先部署更新。

视频的输入按「视频参考素材（全能参考，强制）」准备：主体 `[@主体名]`，站位图和补充视角写 referenceResources，音频按顺序连线；正反打、补拍画面不作为视频参考。跨镜头参考时显式加入本镜 Shot 并传 nodeIndex，人物图本身无需 Shot。多图模式使用 generationParams.videoType="referenceImg"；需要精确编号时按提示词顺序写 referenceResources，图片用 IMAGE/REFERENCE，配音用 AUDIO/SOURCE_AUDIO，分别对应图1…和音频1…。不要再将“一张图/一条音频”或“人物/补拍图不能连视频”当成通用限制。生成仍需核对具体模型的素材数量、格式与时长要求。首尾帧 keyframe 模式与多图 referenceImg 模式区分使用。
