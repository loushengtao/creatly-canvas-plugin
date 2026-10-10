import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('configure', ROOT / 'scripts/configure-environment.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class EnvironmentPackagesTest(unittest.TestCase):
    def test_registered_account_panel_binding_survives_upgrades_and_cannot_leak_between_environments(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for directory in ['plugins', '.claude-plugin', '.codebuddy-plugin']:
                shutil.copytree(ROOT / directory, root / directory, ignore=shutil.ignore_patterns('node_modules'))
            shutil.copy(ROOT / 'README.md', root / 'README.md')
            plugin = root / 'plugins/creatly-video-director'
            # This fixture ID never goes into a released package or a live platform request.
            app_id = 'asdk_app_testfixture'
            module.configure(root, 'test', app_id)
            expected = {'apps': {'yuanji': {'id': app_id, 'required': True}}}
            self.assertEqual(json.loads((plugin / '.app.json').read_text()), expected)
            self.assertEqual(json.loads((plugin / '.codex-plugin/plugin.json').read_text())['apps'], './.app.json')
            for host in ['claude', 'codebuddy']:
                self.assertNotIn('apps', json.loads((plugin / f'.{host}-plugin/plugin.json').read_text()))
            module.configure(root, 'test')
            self.assertEqual(json.loads((plugin / '.app.json').read_text()), expected)
            module.configure(root, 'dev')
            self.assertFalse((plugin / '.app.json').exists())
            self.assertNotIn('apps', json.loads((plugin / '.codex-plugin/plugin.json').read_text()))
            module.configure(root, 'test')
            self.assertEqual(json.loads((plugin / '.app.json').read_text()), expected)
            self.assertEqual(json.loads((root / 'config/openai-apps.json').read_text())['test'], app_id)

    def test_bad_platform_id_does_not_modify_the_package(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for directory in ['plugins', '.claude-plugin', '.codebuddy-plugin']:
                shutil.copytree(ROOT / directory, root / directory, ignore=shutil.ignore_patterns('node_modules'))
            shutil.copy(ROOT / 'README.md', root / 'README.md')
            snapshot = {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            with self.assertRaises(ValueError):
                module.configure(root, 'test', 'oauth-client-or-access-token')
            self.assertEqual(snapshot, {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()})

    def test_each_environment_and_repeated_render(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for directory in ['plugins', '.claude-plugin', '.codebuddy-plugin']:
                shutil.copytree(ROOT / directory, root / directory, ignore=shutil.ignore_patterns('node_modules'))
            shutil.copy(ROOT / 'README.md', root / 'README.md')
            for env in ['dev', 'test', 'production', 'dev']:
                with self.subTest(environment=env):
                    module.configure(root, env)
                    branch, domain, _, version = module.ENVIRONMENTS[env]
                    plugin = root / 'plugins/creatly-video-director'
                    endpoint = f'https://{domain}/api/agent/mcp/v2'
                    expected = {'yuanji': {'type': 'http', 'url': endpoint}}
                    for filename in ['.mcp.json', '.mcp.claude.json']:
                        self.assertEqual(json.loads((plugin / filename).read_text())['mcpServers'], expected)
                    for host in ['codex', 'claude', 'codebuddy']:
                        manifest = json.loads((plugin / f'.{host}-plugin/plugin.json').read_text())
                        self.assertEqual(manifest['version'], version)
                        self.assertEqual(manifest['homepage'], f'https://{domain}')
                        if host == 'codebuddy': self.assertEqual(manifest['mcpServers'], expected)
                    for path in [root / 'README.md', plugin / 'README.md']:
                        text = path.read_text()
                        self.assertIn(f'--ref {branch}', text)
                        self.assertIn(f'.git#{branch}', text)
                        self.assertIn(f'/heads/{branch}.zip', text)
                    for path in plugin.glob('skills/*/references/mcp-execution.md'):
                        self.assertIn(endpoint, path.read_text())
                    snapshot = {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}
                    module.configure(root, env)
                    self.assertEqual(snapshot, {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()})

    def test_same_environment_upgrade_keeps_oauth_connection_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for directory in ['plugins', '.claude-plugin', '.codebuddy-plugin']:
                shutil.copytree(ROOT / directory, root / directory, ignore=shutil.ignore_patterns('node_modules'))
            shutil.copy(ROOT / 'README.md', root / 'README.md')
            plugin = root / 'plugins/creatly-video-director'
            module.configure(root, 'test')
            connections = {name: (plugin / name).read_bytes() for name in ['.mcp.json', '.mcp.claude.json']}
            codebuddy_connection = json.loads((plugin / '.codebuddy-plugin/plugin.json').read_text())['mcpServers']
            branch, domain, label, _ = module.ENVIRONMENTS['test']
            with patch.dict(module.ENVIRONMENTS, {'test': (branch, domain, label, '9.9.9-test')}):
                module.configure(root, 'test')
            for name, previous in connections.items():
                self.assertEqual((plugin / name).read_bytes(), previous)
            for host in ['codex', 'claude', 'codebuddy']:
                manifest = json.loads((plugin / f'.{host}-plugin/plugin.json').read_text())
                self.assertEqual(manifest['name'], 'creatly-video-director')
                self.assertEqual(manifest['version'], '9.9.9-test')
                if host == 'codebuddy':
                    self.assertEqual(manifest['mcpServers'], codebuddy_connection)
            self.assertEqual(list(codebuddy_connection), ['yuanji'])
            for path in [root / 'README.md', plugin / 'README.md']:
                self.assertIn('一次授权与自动续期', path.read_text())

    def test_release_packages_only_declare_remote_oauth_no_local_bridge_or_credentials(self):
        plugin = ROOT / 'plugins/creatly-video-director'
        site = json.loads((plugin / '.codex-plugin/plugin.json').read_text())['homepage']
        self.assertIn(site, {f'https://{domain}'
                             for _, domain, _, _ in module.ENVIRONMENTS.values()})
        for name in ['.mcp.json', '.mcp.claude.json']:
            config = json.loads((plugin / name).read_text())
            self.assertEqual(set(config), {'mcpServers'})
            self.assertEqual(set(config['mcpServers']), {'yuanji'})
            server = config['mcpServers']['yuanji']
            self.assertEqual(set(server), {'type', 'url'})
            self.assertEqual(server['type'], 'http')
            self.assertEqual(server['url'], f'{site}/api/agent/mcp/v2')

if __name__ == '__main__': unittest.main()
