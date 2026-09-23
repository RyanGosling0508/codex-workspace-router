# 贡献指南

[English](CONTRIBUTING.md) | **简体中文**


欢迎小而明确的修复。问题和建议使用仓库模板；大幅修改分流行为前，先说明具体问题与方案。中英文报告均可。

## 本地开发

克隆仓库，使用 Python 3.10+（当前 CI 为 3.12）。运行时仅用标准库。开发界面时运行 `python -B run_console.py --port 0 --open`，编辑仓库示例配置；测试不要指向他人的私人安装配置。

## 验证

在仓库根目录运行，Linux/macOS 使用 `python3`：

```sh
python -B scripts/check_package.py
python -B -m unittest discover -s workspace-router/tests -v
python -B -m unittest discover -s . -p test_installer.py -v
python -B -m unittest console.test_console -v
```

修改界面时，如有 Node，补充 `node --check console/web/app.js`；检查两种语言、键盘操作、草稿保留、保存冲突和减少动态效果。纯文档修改做链接检查与渲染检查；行为变化增加相关回归验证。

规则测试不能证明模型质量或省额度。明确报告跳过项和限制。CI 覆盖 Windows 与 Ubuntu；不允许创建符号链接的环境可能跳过该项。

## 修改分流策略需附依据

提供具体任务、模型与强度、工具、验收标准、结果、重试和可观察用量。区分官方建议、亲测结果和工程判断，不用 API 标价推算订阅额度。保留直接工作优先、用户明确选择、主机边界与验收检查。

## 文档与 PR

- 同步修改对应中英文页面，Skill 参考文件保持自包含。
- 清楚区分源码示例与安装配置，保留现有入口。
- 在 PR 模板说明改前/改后行为和实际验证。
- 不提交凭据、启动令牌、私人提示词、工作区说明或本地历史。
- 保持修复聚焦，不因排版改动引入依赖。

贡献采用仓库 [MIT 协议](LICENSE)。
