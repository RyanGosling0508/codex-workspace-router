# Contributing

**English** | [简体中文](CONTRIBUTING.zh-CN.md)


Small, reviewable fixes are welcome. Use the issue templates for bugs and proposals; discuss changes to routing behavior before a large implementation. English and Chinese reports are both welcome.

## Development

Clone the repository and use Python 3.10+ (CI currently uses 3.12). The runtime uses only the standard library. Start `python -B run_console.py --port 0 --open` against the repository sample policy while developing. Do not point tests at someone's installed private configuration.

## Validation

Run from the repository root; use `python3` on Linux/macOS:

```sh
python -B scripts/check_package.py
python -B -m unittest discover -s workspace-router/tests -v
python -B -m unittest discover -s . -p test_installer.py -v
python -B -m unittest console.test_console -v
```

For UI changes, also run `node --check console/web/app.js` if Node is available, then inspect both languages, keyboard access, draft preservation, save conflicts and reduced-motion behavior. Pure documentation changes need package/link checks and a rendered-page review; new behavior needs relevant regression tests.

Tests verify routing and configuration behavior, not model quality or measured savings. Report skipped checks and limitations. CI runs on Windows and Ubuntu; a platform without symlink privileges may skip the symlink check.

## Policy changes need evidence

Provide the task, exact model and effort, tools, acceptance criteria, outcome, retries and observed usage. Distinguish official guidance, first-hand tests and engineering judgment. Do not infer subscription quota from API prices. Preserve the direct-work gate, explicit user choices, host boundaries and acceptance checks.

## Documentation and pull requests

- Update the corresponding English and Chinese pages together; keep Skill references self-contained.
- Preserve current source/installed-policy distinctions and existing entry points.
- Explain the concrete before/after behavior and relevant validation in the PR template.
- Keep credentials, launch tokens, private prompts, workspace notes and local history out of reports and commits.
- Keep fixes focused; do not add dependencies for formatting-only work.

Contributions use the repository's [MIT license](LICENSE).
