# 三套预设与依据 · 1.3

[English](presets.md) | **简体中文**

默认选 **稳定方案**。预设控制有必要委派时的子模型，不切换 Codex 主模型。主任务可直接完成的工作仍直接处理。所有预设都保留权限、目录、SSH 主机、冲突检查和验收标准。

| 任务 | 经济 | 稳定（默认） | 土豪 |
|---|---|---|---|
| 文本确定性提取 / 转换 | Luna / High | Luna / High | Luna / High |
| 精确、低风险、可测试的局部实现 / 修复 | Luna / High 先试 | Sol / Medium | Sol / High |
| 其他常规任务 | Sol / Medium | Sol / Medium | Sol / High |
| 跨组件、需求开放、复杂调试 / 判断 | Sol / High | Sol / High | Astra / High |
| 高影响决策、开放 / 高不确定性系统设计 | Astra / High | Astra / High | Astra / XHigh |
| 有依据的相邻档位模糊 | 不启用轻量试用；按已命中最高档 | 按已命中最高档 | 在已命中最高档上再升一级，最高关键档 |

经济方案先判断能否验收，再尝试更便宜的候选。没有实测前无法证明某个模型一定完成，所以称为“受限试用”。它不会为了省钱降低关键档，也不把验证失败当成功。土豪方案也不会让规则明确的文本转换一律使用 Astra，更高强度不保证每个任务都更好。

## 严格条件

经济局部试用仅在基础档为 routine、无恢复失败、kind 为 implement/debug、specification 为 exact、verification 为 tests、scope 为 local、输入仅文本、边界明确、风险和不确定性都低时触发。全部成立后，候选池复用当前 `lanes.mechanical`（出厂为 Luna/High → Sol/Medium → Astra/Low）。输出保留 routine 档与 `candidate_pool: mechanical`，不会把实现伪装成确定性任务。若实际验证失败且归因为推理问题，停止轻量试用，按 routine 升到 complex（Sol/High），最多一次恢复。范围扩大或验收缺失则重新评估，不能继续套用旧条件。

土豪的“模糊”必须填写 `assessment.boundary: adjacent` 与非空 `boundary_evidence`，指出哪个具体事实使相邻两档都可能适用。不能用“可能很难”凑依据。明确命中高风险或跨组件条件时，所有预设先按硬规则升档；经济和稳定不会因模糊而降低已确认档位。未解决的重要未知应标记高不确定性，不能用模糊标记规避它。

三套统一：同时 1 个子代理，每次用户请求累计最多 2 次启动，最多 1 次有依据的恢复，至少 5 分钟推理工作量。这个门槛是开销控制经验值，不是官方性能阈值。更贵的方案不自动多开代理。轻量模型没有验收通过，就不能宣称任务完成。

`routing_strategy` 保存经济/稳定/土豪行为；完整模板在 `presets.json`，稳定重置模板在 `default-policy.json`，正在使用的配置在 `policy.json`。控制台按完整配置匹配预设名称，修改参数后显示自定义。候选回退只处理运行时可用性，不等于执行失败重试。Terra 保留明确指定或自定义使用；当前证据不足以把它设为 GPT-6 任务的自动优选。Max/Ultra 不默认开启。

## 查证依据（2026-09-23 UTC）

1. **官方建议**：[Codex 子代理](https://learn.chatgpt.com/docs/agent-configuration/subagents)给出 Sol/Medium、Luna/High 的起始建议；[模型选择](https://learn.chatgpt.com/docs/model-selection)强调用相同任务验证满足质量的较轻配置。我们据此采用稳定的编程主力与经济的受限试用。
2. **用户亲测、小样本**：[merefield 原始测试帖](https://community.openai.com/t/announcing-gpt-6-sol-and-gpt-6-luna-in-the-api-codex-and-chatgpt/1399925/6)报告 Luna/High 与 Sol/High 都通过了三个编程任务。它支持尝试有明确验收的窄任务，不能证明 Luna 可替代复杂项目里的 Sol。未独立复跑；不是统计显著结论。帖子中的 API 等价费用不是订阅额度。
3. **独立实测、不同任务领域**：[Roboflow Luna Vision Evals](https://playground.roboflow.com/models/openai/gpt-6-luna)逐任务对比低/高推理强度，每项三次运行；额外推理并非每类视觉任务都有提升。它支持按任务验证而非盲目拉满；不直接证明代码能力。图片/OCR 提取不自动进入文本确定性档。
4. **独立基准的边界**：[ARC Prize Luna](https://arcprize.org/results/openai-gpt-6-luna)区分推理强度和运行框架，结果会随配置改变。这不是你的仓库验收结果，不据此制定绝对模型分数线。
5. **能力定位**：[Luna](https://developers.openai.com/api/docs/models/gpt-6-luna)、[Sol](https://developers.openai.com/api/docs/models/gpt-6-sol)、[Astra](https://developers.openai.com/api/docs/models/gpt-6-astra)的官方定位分别支持窄任务、编程主力和困难端到端工作。土豪方案的升档幅度与具体 High/XHigh 选择是我们的工程取舍，非官方保证。

三套预设不是都已经被用户完整验证过的方案。公开材料为设计提供依据，自动化测试验证分流与配置行为；本发布没有执行付费跨模型 A/B，也没有测得你的订阅额度节省比例。若要声称“最低成本完成”，必须用同一任务、相同工具与验收，记录主模型、子模型、重试、验收全过程开销；只比较单次子调用价格不够。

后续更新应保存模型版本、推理强度、任务集、提示词、工具、成功率、延迟、可观察用量与失败类型，再决定是否扩大经济试用范围。不会自动根据单次成功改写规则。
