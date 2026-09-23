# 当前画布 JSON 契约

接口 Schema 以 canvas_describe_tools 从当前后端取得的定义为准。具体调用方式见 [MCP 执行协议](mcp-execution.md)。

先读取 getCanvasContext，保留真实节点 ID、输入关系、容器关系、节点顺序、版本及媒体字段。缺失字段不代表空值，过滤读取不代表完整画布；删除或跨节点修订前须取得相关完整范围。

长整数 ID 和版本传字符串。外层 projectId 指向当前项目，业务字段在 payload 内。创建和修改后再次读取验证真实内容；节点位置只通过 Schema 提供的 position 字段设置，不把视觉坐标当作生成依赖。

status 为完成不能代替非空 frameFiles、videoFiles、audioFiles 等真实文件。读取结果没有生成参数时不要宣称已核对；费用计算可能更新版本，后续写入前按实际返回重新读取。
