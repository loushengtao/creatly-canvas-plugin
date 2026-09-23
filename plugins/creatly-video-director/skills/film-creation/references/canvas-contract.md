# 当前画布 JSON 契约

接口 Schema 以 标准 MCP tools/list 从 dev 站点取得的定义为准。具体调用方式见 [MCP 执行协议](mcp-execution.md)。

先读取 getCanvasContext，保留真实节点 ID、输入关系、容器关系、节点顺序、版本及媒体字段。缺失字段不代表空值，过滤读取不代表完整画布；删除或跨节点修订前须取得相关完整范围。

项目与节点 ID 使用服务端返回的不透明字符串，版本类型遵循实时 Schema。projectId 与业务字段平铺传入，不使用 payload 包装。创建和修改后再次读取验证真实内容；节点位置只通过 Schema 提供的 position 字段设置，不把视觉坐标当作生成依赖。

status 为完成不能代替非空 frameFiles、videoFiles、audioFiles 等真实文件。读取结果没有生成参数时不要宣称已核对；费用计算可能更新版本，后续写入前按实际返回重新读取。
