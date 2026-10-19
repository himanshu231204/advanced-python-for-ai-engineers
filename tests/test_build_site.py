import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import build_site


class BuildSiteTests(unittest.TestCase):
    def test_child_navigation_and_safe_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            module = root / '00-foundation'
            module.mkdir()
            (module / 'README.md').write_text('# Foundation\n**Status:** Planned\n', encoding='utf-8')
            (module / 'child.md').write_text('\ufeff# Child\nsearchable lesson', encoding='utf-8')
            for name in ('examples/demo.py', 'examples/.venv/pkg/dependency.py',
                         'examples/__pycache__/cache.py', '.scratch/report.md',
                         'examples/node_modules/dependency.py', 'examples/scratch/report.json'):
                path = module / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('example', encoding='utf-8')
            with patch.object(build_site, 'ROOT', root), patch.object(build_site, 'DOCS', root / 'docs'):
                with contextlib.redirect_stdout(io.StringIO()):
                    build_site.main()
            data = json.loads((root / 'docs/content.json').read_text(encoding='utf-8'))
            child = data['docs']['00-foundation/child']
            self.assertEqual(child['title'], 'Child')
            self.assertEqual((child['source'], child['kind'], child['parent']),
                             ('00-foundation/child.md', 'topic', '00-foundation'))
            nav = next(item['children'] for item in data['nav'] if item['id'] == 'modules')
            self.assertEqual([item['id'] for item in nav], ['00-foundation', '00-foundation/child'])
            self.assertEqual(data['meta']['modules_total'], 1)
            self.assertEqual(data['meta']['modules_written'], 0)
            self.assertEqual([item['name'].replace('\\', '/') for item in data['docs']['00-foundation']['code']],
                             ['examples/demo.py'])

    def test_real_module_metrics_and_children(self) -> None:
        data = json.loads((build_site.DOCS / 'content.json').read_text(encoding='utf-8'))
        self.assertEqual(data['meta']['modules_total'], 29)
        self.assertEqual(len(data['meta']['module_order']), 29)
        self.assertEqual(data['meta']['modules_written'], sum(
            data['docs'][key]['status'] == 'Written' for key in data['meta']['module_order']))
        module_nav = next(item['children'] for item in data['nav'] if item['id'] == 'modules')
        for doc in data['docs'].values():
            for attachment in doc.get('code', []):
                parts = attachment['name'].replace('\\', '/').split('/')
                self.assertFalse(any(part.startswith('.') or part in {'__pycache__', 'node_modules'} for part in parts))
        for path in (build_site.ROOT / '00-python-foundation-review').glob('*.md'):
            if path.name == 'README.md':
                continue
            matches = [doc for doc in data['docs'].values() if doc['source'] == path.relative_to(build_site.ROOT).as_posix()]
            self.assertEqual(len(matches), 1, path.name)
            child_id = '00-python-foundation-review/' + path.stem
            self.assertEqual(sum(item['id'] == child_id for item in module_nav), 1)


if __name__ == '__main__':
    unittest.main()
