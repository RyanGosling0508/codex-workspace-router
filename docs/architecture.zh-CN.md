# 架构与目录

[English](architecture.md) | **简体中文** · [文档目录](README.zh-CN.md)

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

## 各部分负责什么

| 组件 | 职责 |
|---|---|
| Skill | 告诉主代理何时值得委派、需收集哪些事实 |
| 规则脚本 | 用确定性规则检查输入事实，返回路线建议 |
| Codex 运行环境 | 提供真实工具、可用模型、权限与子代理执行 |
| Router Studio | 编辑一个明确指定的配置文件，模拟决策并保存历史 |
| 安装器 | 预览或复制完整 Skill，替换前备份旧安装 |

## 配置以哪里为准

`references/policy.json` 是当前可编辑配置；`presets.json` 保存三套出厂模板；`default-policy.json` 是稳定方案重置模板。它们都在安装后的 Skill 内。公开仓库保留通用工作区说明，私人说明和 `.local/` 历史不应提交。

控制台只在编辑时需要。Skill 和脚本不依赖常驻 Web 服务。脚本输出的是建议，不派发代理，也不建立权限边界；真正权限由运行环境决定。

## 保持入口稳定

Skill 目录保持完整，可独立安装。根目录启动脚本及 `CONSOLE*.md` 旧链接保留；面向用户的指南放在 `docs/`，供代理执行的规则留在 Skill 内，避免两份规则逐渐不一致。[请求协议（英文）](../workspace-router/references/protocol.md)
