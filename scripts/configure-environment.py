#!/usr/bin/env python3
"""Render the released branch's HTTP MCP configuration and install documentation."""
import argparse
import json
from pathlib import Path

ENVIRONMENTS = {
    'dev': ('dev', 'dev.yuanji.studio', '开发', '0.2.4-dev'),
    'test': ('test', 'test.yuanji.studio', '测试', '0.2.8-test'),
    'production': ('main', 'yuanji.studio', '生产', '0.2.4'),
}

def configure(root, environment):
    branch, domain, label, version = ENVIRONMENTS[environment]
    plugin = root / 'plugins/creatly-video-director'
    site = f'https://{domain}'
    endpoint = f'{site}/api/agent/mcp/v2'
    server = 'creatly' if environment == 'production' else f'creatly-{environment}'
    servers = {'yuanji': {'type': 'http', 'url': endpoint}}
    def write_json(path, data):
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
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
        if path == root / 'README.md': protocol = 'plugins/creatly-video-director/' + protocol
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

安装后开启新任务，使用 `/mcp` 或宿主提示完成 yuanji 的 OAuth 授权，在 **{domain}** 登录。单纯打开网站不等于完成插件授权。

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
    args = parser.parse_args()
    configure(Path(__file__).resolve().parents[1], args.environment)
