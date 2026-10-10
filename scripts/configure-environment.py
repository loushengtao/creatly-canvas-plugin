#!/usr/bin/env python3
"""Render the released branch's HTTP MCP configuration and install documentation."""
import argparse
import json
import re
from pathlib import Path

ENVIRONMENTS = {
    'dev': ('dev', 'dev.yuanji.studio', '开发', '0.2.4-dev'),
    'test': ('test', 'test.yuanji.studio', '测试', '0.2.11-test'),
    'production': ('main', 'yuanji.studio', '生产', '0.2.4'),
}

# Keep the host's OAuth credential identity stable when releasing a new plugin version.
MCP_SERVER_NAME = 'yuanji'

def normalize_openai_app_id(value):
    if not isinstance(value, str):
        raise ValueError('Use the actual registered OpenAI app ID, not an OAuth client ID or URL.')
    # The platform detail URL uses plugin_<app ID>; .app.json requires the app ID itself.
    value = value.removeprefix('plugin_')
    if not re.fullmatch(r'(?:asdk_app|connector|templated_apps)_[A-Za-z0-9][A-Za-z0-9_-]*', value):
        raise ValueError('Use the actual registered OpenAI app ID, not an OAuth client ID or URL.')
    return value

def configure(root, environment, openai_app_id=None):
    branch, domain, label, version = ENVIRONMENTS[environment]
    plugin = root / 'plugins/creatly-video-director'
    site = f'https://{domain}'
    endpoint = f'{site}/api/agent/mcp/v2'
    server = 'creatly' if environment == 'production' else f'creatly-{environment}'
    servers = {MCP_SERVER_NAME: {'type': 'http', 'url': endpoint}}
    def write_json(path, data):
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    mapping_path = root / 'config/openai-apps.json'
    mappings = json.loads(mapping_path.read_text()) if mapping_path.exists() else {}
    previous_mappings = mappings.copy()
    if openai_app_id is not None:
        mappings[environment] = normalize_openai_app_id(openai_app_id)
    registered_app_id = mappings.get(environment)
    if registered_app_id is not None:
        registered_app_id = normalize_openai_app_id(registered_app_id)
        mappings[environment] = registered_app_id
    if openai_app_id is not None or mappings != previous_mappings:
        mapping_path.parent.mkdir(parents=True, exist_ok=True)
        write_json(mapping_path, mappings)
    app_path = plugin / '.app.json'
    if registered_app_id:
        write_json(app_path, {'apps': {MCP_SERVER_NAME: {'id': registered_app_id, 'required': True}}})
    elif app_path.exists():
        app_path.unlink()
    for name in ['.mcp.json', '.mcp.claude.json']:
        write_json(plugin / name, {'mcpServers': servers})
    for host in ['codex', 'claude', 'codebuddy']:
        path = plugin / f'.{host}-plugin/plugin.json'
        data = json.loads(path.read_text())
        assert data['name'] == 'creatly-video-director'
        data.update(version=version, homepage=site)
        if 'url' in data.get('author', {}): data['author']['url'] = site
        if 'interface' in data: data['interface']['websiteURL'] = site
        if host == 'codebuddy': data['mcpServers'] = servers
        if host == 'codex':
            if registered_app_id:
                data['apps'] = './.app.json'
            else:
                data.pop('apps', None)
        write_json(path, data)
    for host in ['claude', 'codebuddy']:
        path = root / f'.{host}-plugin/marketplace.json'
        data = json.loads(path.read_text())
        assert data['name'] == 'creatly'
        for item in data['plugins']:
            if item['name'] == 'creatly-video-director':
                item.update(version=version, homepage=site)
        write_json(path, data)
    for path in plugin.glob('skills/*/references/mcp-execution.md'):
        text = path.read_text()
        for _, known_domain, _, _ in ENVIRONMENTS.values():
            text = text.replace(f'https://{known_domain}/api/agent/mcp/v2', endpoint)
        path.write_text(text)
    for path in [root / 'README.md', plugin / 'README.md']:
        old = path.read_text()
        # Keep workflow documentation separate from generated installation instructions.
        tail = old[old.index('## 图片、视频、音频上传'):] if '## 图片、视频、音频上传' in old else old[old.index('## 生成确认'):]
        protocol = 'skills/film-skill/references/mcp-execution.md'
        connection_guide = 'docs/oauth-connection.md'
        if path == root / 'README.md': protocol = 'plugins/creatly-video-director/' + protocol
        if path == root / 'README.md': connection_guide = 'plugins/creatly-video-director/' + connection_guide
        header = f'''# Creatly Canvas Plugin · {label}环境

本分支 `{branch}` 通过远程 MCP 连接 [{domain}]({site}/)，无需启动本地画布服务。

## 环境对应

| 环境 | 网站 | GitHub 分支 |
| --- | --- | --- |
| 开发 | https://dev.yuanji.studio | dev |
| 测试 | https://test.yuanji.studio | test |
| 生产 | https://yuanji.studio | main |

安装的分支决定连接的环境，打开另一个网站不会自动切换插件。切换环境前，在宿主中移除旧的 `creatly` marketplace 来源，再添加目标分支并重新加载插件；在目标环境完成授权，确认账号与空间。三个环境不共用授权和画布数据。

## Codex 安装

```bash
codex plugin marketplace add https://github.com/loushengtao/creatly-canvas-plugin.git --ref {branch}
codex plugin add creatly-video-director@creatly
```

## Claude Code 安装

```text
/plugin marketplace add https://github.com/loushengtao/creatly-canvas-plugin.git#{branch}
/plugin install creatly-video-director@creatly
```

首次连接时，按宿主提示完成 yuanji 的 OAuth 授权，在 **{domain}** 登录并选择空间。之后由宿主保存凭据和自动刷新访问令牌；开启新任务、重启宿主或更新同一环境的插件时先复用已有连接，不每天执行 `/mcp` 验证。完整失效条件与排障见 [账号连接与续期]({connection_guide})。

## 一次授权与自动续期

- 元极采用标准 OAuth：访问令牌默认 30 分钟，刷新令牌默认 30 天；成功刷新会返回新的访问令牌和刷新令牌，由宿主安全保存。30 天指刷新令牌有效期，不是让一个访问令牌使用 30 天；实际有效期以服务端签发结果为准。
- 同一环境更新时保持插件名 `creatly-video-director`、MCP 名 `yuanji` 和 MCP 地址稳定。通过宿主的更新流程升级，不为日常更新卸载重装、登出或重复添加手动 MCP。
- 正常续期不需要浏览器、保持画布打开或重新输入密码。撤销授权、刷新令牌到期、凭据丢失或切换环境后，才按宿主提示重新连接。网站登录与插件授权是两套凭据。
- 403 是资源权限问题；429、5xx 和连接超时是请求问题。不要因此清除授权或反复登录。`invalid_client` 表示客户端注册/认证异常，`invalid_grant` 表示刷新凭据异常，应先诊断具体原因。

持续授权依赖后端部署：必须发布保留关联授权的 OAuth 客户端清理修复。已被旧服务误删的客户端无法只靠更新插件恢复，修复发布后需重新授权一次；之后使用正常自动续期流程。

## Codex 已连接账户面板

{'本环境已关联平台注册的元极应用。安装后在插件设置中连接账户；账户名称由后端的 `getProfile` 返回，面板由平台展示。' if registered_app_id else '本环境尚未填写平台注册的元极应用 ID，因此当前安装包仍通过 MCP 连接管理授权，尚不显示平台账户面板。'}

维护者在平台创建对应环境的自定义 MCP 插件后，将实际应用 ID 写入 `config/openai-apps.json`；详细步骤见 [账号连接与续期]({connection_guide})。平台注册、后端部署和真实账户连接均完成后才算面板验收通过。三个环境使用各自的应用 ID，升级时保留已有映射。

## WorkBuddy

下载 [{branch} 分支 ZIP](https://github.com/loushengtao/creatly-canvas-plugin/archive/refs/heads/{branch}.zip)，按宿主的本地 marketplace 安装流程导入。需要支持 HTTP MCP 与 OAuth；完整安装与授权流程尚未端到端验证。

## CLI / 手动 MCP 配置

Codex：

```bash
codex mcp add {server} --url {endpoint}
codex mcp login {server}
```

Claude Code：

```text
claude mcp add --transport http {server} {endpoint}
/mcp
```

手动 HTTP MCP 配置：

```json
{{"mcpServers": {{"{server}": {{"type": "http", "url": "{endpoint}"}}}}}}
```

手动 MCP 配置不包含插件创作技能；已通过插件连接时无需重复添加。

## 创作与协议

技能统一为 `film-skill`：一个入口覆盖剧本、选角、分镜、运镜、视频提示词、画布执行和剪辑，按叙事短片或写实电影路线推进，细节按需读取 `references/`。视频默认 Seedance 2.5、480p、开启音频；用户明确指定的模型、画质和音频参数优先。

配置使用标准 HTTP MCP，由宿主管理 OAuth 授权与令牌刷新，不打包凭据。通过实时 `tools/list` 获取工具及 Schema，具体见 [执行协议]({protocol})。工具能力取决于对应环境的后端部署；插件升级不等于后端已发布，也不代表已完成付费生成验收。

仓库中的旧 stdio 适配器仅为历史开发工具，本版本插件不加载它。

## 维护环境版本

在仓库根目录执行 `python3 scripts/configure-environment.py {'production' if environment == 'production' else branch}`，同步三个宿主的配置、版本、技能连接说明和安装文档；开发、测试、生产必须分别发布到 `dev`、`test`、`main`。

'''
        path.write_text(header + tail)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('environment', choices=ENVIRONMENTS)
    parser.add_argument('--openai-app-id', help='Actual registered OpenAI app ID for this environment.')
    args = parser.parse_args()
    configure(Path(__file__).resolve().parents[1], args.environment, args.openai_app_id)
