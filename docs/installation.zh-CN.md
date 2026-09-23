# 安装、升级与回滚

[English](installation.md) | **简体中文** · [文档目录](README.zh-CN.md)

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

## 修改、关闭、升级与回滚

修改**已安装版本**的 `references/policy.json` 可以调整支持的模型候选或限额。将 `enabled` 改为 `false` 可关闭本 Router 的委派，继续由主任务处理。临时关闭直接说“不要子代理”。修改下载目录里的源文件不会自动更新已安装版本。

使用配套安装器升级前，先把个人配置改动合并到准备安装的源包：

```bash
python3 -B install_router.py
python3 -B install_router.py --install --replace
```

Windows 换成 `python -X utf8 -B`。已有内容发生变化时必须加 `--replace`，相同内容不会重复安装。替换前会备份到 `<Codex home>/router-backups/`，避免备份被重复识别成 Skill；安装器会输出备份路径。回滚时用 `--source /备份绝对路径` 先预览，再加 `--install --replace`。不要同时运行多个安装器。手动部署到 `.agents/skills` 的版本，要在同一选定目录手动备份和更新。

## 打开已安装策略的控制台

安装完成后，在仓库根目录运行：

```sh
python run_console.py --installed --port 0 --open
```

Linux/macOS 使用 `python3`。确认页面的配置来源指向实际安装目录。默认采用稳定方案；点击恢复推荐默认可恢复整套稳定配置。若手动安装在 `.agents/skills`，请用 `--policy /absolute/path/workspace-router/references/policy.json` 指定文件。详见[控制台指南](console.zh-CN.md)。
