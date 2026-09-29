import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('configure', ROOT / 'scripts/configure-environment.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class EnvironmentPackagesTest(unittest.TestCase):
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

if __name__ == '__main__': unittest.main()
