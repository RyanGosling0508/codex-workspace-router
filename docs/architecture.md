# Architecture

**English** | [简体中文](architecture.zh-CN.md) · [Documentation](README.md)

```text
codex-workspace-router/
├── README.md / README.zh-CN.md
├── docs/                     # User guides and original diagrams
├── workspace-router/         # Self-contained installable Skill
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   ├── scripts/router.py
│   ├── references/           # Policy, presets and agent-facing references
│   └── tests/
├── console/                  # Local server, web UI and console tests
├── install_router.py         # Preview, install and backup
├── run_console.py            # Console entry point
├── scripts/check_package.py  # Package and link checks
├── test_installer.py
└── .github/                  # CI and contribution templates
```

## Responsibilities

| Component | Responsibility |
|---|---|
| Skill | Tell the main agent when delegation is justified and what evidence to gather |
| Router helper | Deterministically validate supplied observations and return a recommendation |
| Codex runtime | Supply actual tools, model availability, permissions and child execution |
| Router Studio | Edit one selected policy file; simulate with synthetic inputs; save history |
| Installer | Preview or copy the complete Skill; back up a differing installation |

## Sources of truth

`references/policy.json` is the current editable policy. `presets.json` contains the three factory templates; `default-policy.json` is the Balanced reset template. These are inside the installed Skill. The public source uses generic workspace notes; personal notes and `.local/` history do not belong in commits.

The console is optional at runtime. The Skill and helper do not depend on a running web server. The helper emits advice, not authority: it never dispatches agents or creates a permission boundary. The runtime remains authoritative.

## Keep paths stable

The Skill folder stays self-contained for direct installation. Root entry points and `CONSOLE*.md` compatibility links remain available. User guides live under `docs/`; policy references remain with the Skill to avoid duplicating executable rules. Internal request details are in the [protocol](../workspace-router/references/protocol.md).
