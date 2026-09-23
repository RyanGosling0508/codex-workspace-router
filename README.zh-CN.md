# Codex Workspace Router

[English](README.md) | **简体中文**

一个以**质量优先、减少不必要代理**为目标的 Codex Skill。默认由主任务直接完成工作，只有具体需要才委派子代理。

**版本 1.1.0 · Python 标准库 · 路由器无需 API Key · MIT 协议**

> 它选择的是有明确边界的**子代理**，不能逐条消息切换主模型，也不是请求进入模型之前的网关。不保证节省费用或订阅额度。

## 使用后会发生什么

```text
你的需求 → 当前主模型
              ├─ 没有具体委派必要 → 直接完成
              └─ 存在具体委派必要
                   → 检查主机、目录、冲突、验收和模型能力
                   → 选择一个可用的子代理执行
                   → 主任务检查结果并回复
```

不额外启动分类模型，不运行常驻路由服务，也不另开汇总代理。主任务利用已有上下文判断，Python 脚本检查结构化输入和规则；脚本本身不理解自然语言、不调用模型，也不执行派发。

## 部署

需要：能加载 Skill 的 Codex 客户端、运行辅助脚本的 Python **3.10+**（已使用 3.12 测试）。如果要实际委派，当前运行环境还必须提供可指定模型的子代理工具；不支持时仍由主任务处理。Python 必须存在于真正执行任务的主机上。

克隆本仓库，或下载 ZIP 后解压。在仓库根目录操作：

### Windows / PowerShell

```powershell
git clone https://github.com/RyanGosling0508/codex-workspace-router.git
cd codex-workspace-router
python --version
python -X utf8 -B install_router.py
python -X utf8 -B install_router.py --install
```

### Linux / macOS

```bash
git clone https://github.com/RyanGosling0508/codex-workspace-router.git
cd codex-workspace-router
python3 --version
python3 -B install_router.py
python3 -B install_router.py --install
```

第一次运行安装器只**预览**；加 `--install` 才写入文件。默认安装到 `$CODEX_HOME/skills/workspace-router`，没有设置 `CODEX_HOME` 时使用 `~/.codex/skills/workspace-router`。自定义 Codex home 使用 `--codex-home /绝对路径`。如果 Python 不在 PATH 中，请使用已确认可用的解释器绝对路径。

不同客户端/版本的技能发现目录可能不同。如果你的客户端采用当前文档中的 `~/.agents/skills` 或项目 `.agents/skills` 目录，请把 **`workspace-router` 文件夹**放入对应技能目录。不要在多个被扫描目录重复安装同名技能。具体以客户端的[技能发现文档](https://learn.chatgpt.com/docs/build-skills)为准。

也可以在提供 skill-installer 的 Codex 中直接说：

```text
使用 $skill-installer，从下面地址安装 workspace-router：
https://github.com/RyanGosling0508/codex-workspace-router/tree/main/workspace-router
```

安装后确认技能列表出现 `workspace-router`，开一个新任务加载更新后的规则；没有发现时重启客户端。安装器不更改默认主模型、全局 `config.toml` 或项目的 `AGENTS.md`。

### SSH 远端

在**实际连接的远端执行主机**上完成相同的克隆和安装步骤，使用远端 Python 与 Codex home，再检查该主机上的技能发现和模型/子代理能力。本机装好不代表服务器装好；不要复制认证信息或假设 Windows 路径在远端有效。安装器不会自行建立 SSH 连接。

## 怎么触发

`agents/openai.yaml` 已设置 `allow_implicit_invocation: true`。当需求匹配技能描述时，Codex 可以自动加载它；**这不是每条消息必执行的 Hook**。加载 Skill 也不意味着一定启动子代理。

显式调用：

```text
$workspace-router 按现有验收标准继续实现这个功能。
```

即使显式调用，仍默认直接做。具体示例：

| 请求 / 实际情况 | 预期行为 |
|---|---|
| “修复这个问题，尽量少用代理。” | 主模型直接处理，大任务也一样。 |
| “单独用一个 Sol/medium 子代理复核坐标变换。” | 检查范围和能力后，考虑指定路线。 |
| 出现需要独立视角的具体正确性问题，例如轴交换后的多边形方向未被测试覆盖 | 考虑一次针对性的**只读**复核，不重复实现整个功能。 |
| “这次优先赶时间，可以并行处理独立部分。” | 考虑有限并行；更快不代表更省。 |
| “另一个模型可能便宜”或“还有空闲槽位” | 这些理由不足以启动子代理。 |
| “这次直接做，不要子代理。” | 不委派。 |
| 目标文件正在被修改，或共享构建目录被占用 | 等待，或选择真正无冲突的工作。 |

主模型可以自己发现具体复核缺口，你不必每次手选子模型或重复规则。但主模型不能编造用户同意或复核需求来通过检查。

## 策略是什么

**只有已经确定需要子代理时**，才进入下面的初始模型分档：

| 符合条件的工作 | 首选 | 依次回退 |
|---|---|---|
| 机械处理、低不确定性、低影响 | `gpt-6-luna` / medium | Sol / medium → Astra / low |
| 范围明确的常规实现或分析 | `gpt-6-sol` / medium | Astra / medium |
| 复杂调试或较高不确定性 | `gpt-6-sol` / high | Astra / high |
| 出错影响大的正确性决策 | `gpt-6-astra` / high | 不回退到较低档位 |

这是可修改的初始选择，**不是性能评测排名**。模型 ID 和强度必须由当前执行主机的实际工具支持，脚本不会自行发现它们。你明确指定的路线不可用时会说明，不会偷偷换模型。Terra 不自动选择；Max 需要明确指定且运行时支持；Ultra 不在本 Router 的嵌套流程内。

[`policy.json`](workspace-router/references/policy.json) 的默认规则：

- 开启、质量优先，先检查具体委派必要。
- **同时最多一个子代理**；**同一用户请求累计最多启动两次**，包含替换和重试。
- 子代理不能再派代理；每个独立子任务最多一次有证据的推理/验证恢复。
- 预计至少三分钟推理工作量才考虑委派；这是额外门槛，达到三分钟不代表应该拆分。
- 同一已确认主机，明确读写范围和受保护文件，避免并发写入与共享资源冲突。
- 模型能力记录最多六小时；重连或更换主机后需重新确认。
- 上下文不足、收益不明、工具缺失、输入无效或质量档位不可用时，交回主任务。
- 断网、认证失败、权限不足、缺依赖不被当作“模型太弱”。
- 子代理结束不代表验收通过；主任务根据实际标准和证据检查。

脚本检查输入结构，不证明输入事实真实。提示词中的目录约束不是新的权限沙箱，资源检查也不是全局文件锁；原有权限和项目规则始终有效。没有保证省额度的算法、训练过的难度分类器或隐藏用量采集。

## 修改、关闭、升级与回滚

修改**已安装版本**的 `references/policy.json` 可以调整支持的模型候选或限额。将 `enabled` 改为 `false` 可关闭本 Router 的委派，继续由主任务处理。临时关闭直接说“不要子代理”。修改下载目录里的源文件不会自动更新已安装版本。

使用配套安装器升级前，先把个人配置改动合并到准备安装的源包：

```bash
python3 -B install_router.py
python3 -B install_router.py --install --replace
```

Windows 换成 `python -X utf8 -B`。已有内容发生变化时必须加 `--replace`，相同内容不会重复安装。替换前会备份到 `<Codex home>/router-backups/`，避免备份被重复识别成 Skill；安装器会输出备份路径。回滚时用 `--source /备份绝对路径` 先预览，再加 `--install --replace`。不要同时运行多个安装器。手动部署到 `.agents/skills` 的版本，要在同一选定目录手动备份和更新。

## 检查与验证

```bash
python3 -B -m unittest discover -s workspace-router/tests -v
python3 -B -m unittest discover -s . -p test_installer.py -v
python3 -B scripts/check_package.py
```

Windows 将 `python3 -B` 替换为 `python -X utf8 -B`。CI 配置会在 Windows 与 Ubuntu、Python 3.12 下执行检查；是否真正通过应查看实际运行结果，不能把配置好的矩阵当成验证结果。

发布前 Windows 测试通过，受主机权限限制的符号链接测试单独跳过。规则测试说明已覆盖行为符合预期，不证明模型质量更高、长期绝对稳定或实际省钱。

- [`SKILL.md`](workspace-router/SKILL.md)：供代理读取的工作流程。
- [`protocol.md`](workspace-router/references/protocol.md)：输入、决策和子代理生命周期协议。
- [`workspaces.md`](workspace-router/references/workspaces.md)：通用多目录 / SSH 检查清单。
- [`maintenance.md`](workspace-router/references/maintenance.md)：评估、可选元数据记录和策略维护。

公开包使用通用示例，不包含作者的本机路径或私人项目清单。核心路由代码和策略与个人版 1.1.0 一致；私人项目规则留在本地适用的项目说明中。

## 来源与许可

参考 [codex-auto-model-router](https://github.com/orange-the-weak/codex-auto-model-router) 的工作流思路独立实现，未复制其路由代码或旧 agent presets。本项目为独立社区项目，不是 OpenAI 官方产品。

接口参考：[Skills](https://learn.chatgpt.com/docs/build-skills)、[Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)、[App Server](https://learn.chatgpt.com/docs/app-server)、[Remote connections](https://learn.chatgpt.com/docs/remote-connections)。

采用 [MIT 协议](LICENSE)。
