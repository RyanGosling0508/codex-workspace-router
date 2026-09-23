"""Validate shipped paths, policy version and local Markdown links; no dependencies."""
import importlib.util
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'workspace-router'


def main():
    spec = importlib.util.spec_from_file_location('router', SKILL / 'scripts/router.py')
    router = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(router)
    policy = router.validate_policy(json.loads((SKILL / 'references/policy.json').read_text(encoding='utf-8')))
    assert policy['version'] == router.VERSION, 'Policy/code version mismatch'
    recommended = router.validate_policy(router.read_json(router.RECOMMENDED_POLICY))
    assert recommended['version'] == router.VERSION, 'Recommended defaults/code version mismatch'
    assert recommended['classification_mode'] == 'evidence-v1'
    presets = router.read_json(router.PRESETS)
    assert set(presets) == {'economy', 'balanced', 'premium'}
    assert presets['balanced'] == recommended
    for name, preset in presets.items():
        router.validate_policy(preset)
        assert preset['routing_strategy'] == name
        assert preset['version'] == router.VERSION
    entry = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
    assert entry.startswith('---\nname: workspace-router\n'), 'Invalid skill name/frontmatter'
    assert '\ndescription: ' in entry.split('---', 2)[1], 'Missing description'
    for readme in ['README.md', 'README.zh-CN.md']:
        assert (ROOT / readme).is_file(), 'Missing language README'
    assert '](README.zh-CN.md)' in (ROOT / 'README.md').read_text(encoding='utf-8')
    assert '](README.md)' in (ROOT / 'README.zh-CN.md').read_text(encoding='utf-8')
    for path in ROOT.rglob('*.md'):
        if '.git' in path.parts:
            continue
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            target = target.strip().strip('<>')
            parsed = urlparse(target)
            if parsed.scheme or target.startswith('#'):
                continue
            resolved = (path.parent / unquote(parsed.path)).resolve()
            assert resolved.is_relative_to(ROOT.resolve()), f'Link escapes repository: {path.name}'
            assert resolved.exists(), f'Broken link in {path.name}: {target}'
    print(f'Package checks passed: version {router.VERSION}, bilingual links and references.')


if __name__ == '__main__':
    main()
