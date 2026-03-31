# cocoverify2 Phase 7/8 闭环实现规划

## 摘要

本文档记录 `cocoverify2` 下一阶段的闭环实现规划，目标是在当前主线

`contract -> plan(hybrid optional) -> oracle(hybrid optional) -> render -> run -> triage`

的基础上，补齐：

1. Phase 7: Targeted Repair
2. Phase 8: Report / Verdict

最终实现“先验证 TB 本身是否可信，再将已验证 TB 交给 QiMeng-Agent 复用”的闭环。

本规划的核心原则是：

- 先把 `cocoverify2` 自己做好，再集成到 `QiMeng-Agent`
- 将“TB 正确性验证”和“candidate DUT 验证”严格分离
- 以 `golden DUT` 为 TB 正确性验证基准
- 不依赖 benchmark `testbench.v`、`reference.dat` 等 golden 输出作为生成输入
- 不把修复逻辑塞进 orchestrator；orchestrator 只负责调度和闭环控制

## 问题定义

当前 `cocoverify2` 已经实现了 Phase 1-6，但仍缺少两个关键能力：

1. 无法判断“当前生成的 TB 是否已经足够可信”
2. 无法在 TB 验证失败时，根据失败证据定向回退到某个阶段并重新生成

这会导致两个问题：

- 生成的 TB 一旦较弱或错误，只能人工观察 artifact，缺少系统化修复路径
- `QiMeng-Agent` 当前在反馈循环中同时混合了：
  - 待测 candidate DUT 是否正确
  - cocoverify 生成的 TB 是否正确

这两类问题本质不同，应该拆开处理。

## 总体目标

Phase 7/8 的闭环目标是：

1. 用 `golden DUT` 验证 TB 是否可信
2. 如果 TB 不可信，根据 `run + triage + repair` 信息判断最可能出错的阶段
3. 只从必要阶段重新生成 artifact，再次 render 和 rerun
4. 输出结构化 `VerificationReport`
5. 只有当 TB 已通过验证后，才交给 `QiMeng-Agent` 用于 candidate DUT 验证

最终我们希望得到两条明确分离的路径：

### 路径 A：TB 生产与验证路径

输入：

- task description / spec
- golden DUT

输出：

- verified TB artifact root
- verification report

### 路径 B：TB 使用路径

输入：

- candidate DUT
- verified TB artifact root

输出：

- candidate DUT 是否通过已验证 TB

路径 B 不再重新生成 TB，除非 task/spec/version 发生变化。

## 关键设计原则

### 1. `golden DUT pass` 是必要条件，但不是充分条件

如果只要求 golden DUT 能通过，那么一个过弱的 TB 也可能被误认为“正确”。

因此 TB 验证至少应包含两类检查：

- 正例验证：golden DUT 必须通过
- 负例验证：至少一小组 bad DUT / mutant DUT 必须被打下来

如果 golden DUT 通过，但简单 mutant DUT 也通过，则应标记为：

- `weak_testbench`
- 或 `inconclusive`

### 2. 不允许 benchmark leakage

允许使用：

- `verified_*.v`
- `design_description.txt`

不允许作为生成输入使用：

- `testbench.v`
- `reference.dat`
- golden waveform / golden outputs

换句话说：

- `golden DUT` 可以用于验证 TB
- 但不能作为 plan/oracle 生成时的隐藏答案来源

### 3. repair 必须是“定向回退”，而不是无脑全量重做

闭环的修复逻辑必须遵循“最早可能出错阶段优先”的原则。

例如：

- `compile_error` / `elaboration_error`
  - 优先怀疑 `contract` / `render` / runner config
- `runtime_test_failure` on golden DUT
  - 优先怀疑 `oracle` / `render`
  - 必要时再回退到 `plan`
- `insufficient_stimulus`
  - 优先怀疑 `plan` / `render`
- `golden pass but mutant also pass`
  - 优先怀疑 `plan` / `oracle` / `render`

## 当前仓库现状

当前代码状态已经具备 Phase 7/8 的基础骨架：

- `README.md` 中已定义 8 阶段主线
- `src/cocoverify2/cli.py` 已暴露：
  - `verify`
  - `repair`
  但目前还是 placeholder
- `src/cocoverify2/core/orchestrator.py` 目前还是薄壳
- `src/cocoverify2/core/models.py` 已经有：
  - `RepairAction`
  - `VerificationReport`
  - `FinalVerdict`

因此下一步应优先补：

1. Phase 7 repair 逻辑
2. Phase 8 report / verdict 逻辑
3. `verify` orchestrator 的闭环执行

## 分阶段实施计划

## 第一步：实现 Phase 7 的 Repair Planner

### 目标

先实现“只出修复建议、不自动重跑”的版本。

输入：

- `simulation_result.json`
- `runner_selection.json`
- `triage.json`
- 必要的 upstream artifact metadata

输出：

- 一组 `RepairAction`

### 责任边界

这一阶段只回答：

- 哪个阶段最可能有问题
- 应该从哪个阶段重新开始
- 哪些 artifact 可以保留
- 哪些 artifact 需要重新生成

不负责真正执行重跑。

### 建议落点

- `src/cocoverify2/stages/repair.py`
- 使用 `core/models.py` 中已有的 `RepairAction`

### 最小修复建议类型

- `refresh_run_only`
- `rerender_and_rerun`
- `regenerate_oracle_render_run`
- `regenerate_plan_oracle_render_run`
- `reextract_contract_and_downstream`

### 测试策略

先做纯单元测试，不依赖真实 simulator 或真实 LLM。

建议新增：

- `tests/test_repair.py`

覆盖场景：

1. golden DUT compile fail
2. golden DUT runtime fail
3. golden DUT pass but mutant DUT also pass
4. insufficient stimulus
5. multi-module only one rendered module fail

### 预期结果

这一阶段结束后，系统可以稳定给出：

- 从哪个阶段重新开始最合适
- 无需每次都从 `contract` 全量重做

## 第二步：实现最小版 Verify Orchestrator

### 目标

将当前线性主线包装成一个最小闭环：

1. 首次执行：
   - `contract -> plan -> oracle -> render -> run -> triage`
2. 如果 TB 验证不通过：
   - 调用 repair planner
   - 根据 `RepairAction` 只回退必要阶段
   - 重新 `render -> run -> triage`
3. 设置最大 repair 轮数，避免无限循环

### 建议落点

- `src/cocoverify2/core/orchestrator.py`
- `src/cocoverify2/cli.py` 的 `verify`

### 约束

- orchestrator 只负责调度
- 业务逻辑仍留在各 stage
- 不引入“run 失败就全量重做”的粗暴逻辑
- 不把 `fill` 变成主路径

### 测试策略

先做 orchestrator 级单元测试，不用真 LLM。

建议：

- 使用 fake stage / monkeypatch
- 模拟：
  - 第一次 `run/triage` 失败
  - repair 建议回退 `oracle`
  - 第二次 render+run 成功

需要验证：

- 只重跑必要阶段
- repair 轮数受限
- 旧 artifact 在可保留时不被覆盖
- 最终生成 `VerificationReport`

### 预期结果

这一阶段结束后，`verify` 不再是 placeholder，而是能执行一个最小可用闭环。

## 第三步：定义 TB 验证标准

### 目标

明确“TB 已验证”的判定标准，而不是只看某次 run 成不成功。

### 建议标准

TB 要被认为 `verified`，至少满足：

1. Golden pass
   - 所有 rendered test modules 在 golden DUT 上通过

2. Negative sanity
   - 至少一组 bad DUT / mutant DUT 被打下来

3. Triage consistency
   - 失败路径能给出稳定 triage，而不是大量 `environment_error` / `unknown`

### mutant 策略

第一版不要做复杂 mutation 框架，只做少量通用、可控 mutant：

- 输出常零
- valid 逻辑失效
- 状态不更新
- pipeline output 不产生
- counter / FSM stuck

### 测试策略

对小 fixture 做验证：

1. golden DUT 应通过
2. 一个明显坏的 mutant DUT 应失败
3. 如果 golden 过、mutant 也过，则 verdict 应是：
   - `weak_testbench`
   - 或 `inconclusive`

### 预期结果

这一阶段之后，“TB 是否正确”会从主观判断变成有 acceptance bar 的结构化结论。

## 第四步：实现 Phase 8 Report / Verdict

### 目标

把完整闭环结果结构化输出出来，便于：

- 人工审阅
- 后续 QiMeng-Agent 消费
- benchmark 统计

### 建议输出内容

`VerificationReport` 至少应包含：

- golden DUT 路径
- candidate / mutant DUT 路径列表
- rendered test modules 列表
- 每个 module 的 run/triage 结果
- repair trace
- coverage / assertion strength 摘要
- final verdict：
  - `verified`
  - `weak_testbench`
  - `likely_oracle_error`
  - `likely_render_error`
  - `inconclusive`

### 建议 artifact

- `verification_report.json`
- `verification_summary.yaml`
- 可选 `verification_summary.md`

### 测试策略

- CLI smoke test
- schema roundtrip test
- report completeness test

### 预期结果

这一阶段结束后，框架可以正式输出“TB 是否可信、若不可信则原因是什么”的最终结论。

## 第五步：先跑 Hard Representative Slice

### 目标

在少量高难任务上验证 Phase 7/8 闭环，而不是一开始就全量跑。

### 建议任务

- `accu`
- `serial2parallel`
- `asyn_fifo`
- `traffic_light`
- `sequence_detector`
- `multi_pipe_8bit`
- `ring_counter`
- `freq_divbyeven`

### 关注指标

- golden DUT 全通过率
- mutant DUT 检出率
- repair 平均轮数
- `weak_testbench` / `inconclusive` 占比
- false positive / false negative 变化

### 预期结果

如果闭环设计合理，这一步应看到：

- golden DUT 大部分可稳定通过
- 明显错误 DUT 不再轻易被放过
- repair loop 能在少数轮内收敛

## 第六步：再做 RTLLM 全量评估

### 目标

在 representative slice 稳定后，再对 RTLLM 全量评估 cocoverify2 自身质量。

### 全量统计应新增的核心指标

除了传统的 pass/fail，还应统计：

- TB `verified` 数量
- `weak_testbench` 数量
- `inconclusive` 数量
- average repair rounds
- golden pass rate
- mutant rejection rate

### 预期结果

这一阶段完成后，我们才能回答：

- cocoverify2 是否已经能稳定产出“可复用的已验证 TB”

## 第七步：最后再集成到 QiMeng-Agent

### 目标

让 QiMeng-Agent 使用“已验证 TB”，而不是在反馈循环里动态混合：

- TB 生成
- TB 验证
- candidate DUT 验证

### 推荐集成方式

1. 先由 cocoverify2 生成并验证 TB
2. 产出一个 verified artifact root / manifest
3. QiMeng-Agent 仅消费：
   - verified render metadata
   - verified test modules
   - verification report
4. 对 candidate DUT 只做 run + triage
5. candidate DUT 失败时，不再重建 TB

### 何时重新验证 TB

只有当下列条件变化时，才重新进入 TB 生成与验证路径：

- task description / spec changed
- cocoverify2 semantic version changed
- semantic-family logic / render runtime changed
- verification policy changed

## 建议的开发顺序

推荐实际开发顺序如下：

1. Repair planner（只规划，不自动修）
2. Verify orchestrator（自动定向重跑）
3. TB acceptance bar（golden pass + mutant fail）
4. Final report / verdict
5. Hard representative slice
6. RTLLM 全量评估
7. QiMeng-Agent 集成

## 非目标

当前阶段不做：

- 直接把 benchmark `testbench.v` 当生成输入
- 直接把 golden 输出喂给 oracle 生成
- 让 QiMeng-Agent 在 feedback 环路里自动生成/修复 TB
- 把 `todo_fill.py` 变成 benchmark 主路径
- 用 task-specific hardcode 解决 Phase 7/8 闭环问题

## 第一轮实施建议

如果按最小闭环先落地，第一轮建议只做：

1. `repair.py`
2. `verify` orchestrator 最小版本
3. `VerificationReport` artifact 落盘
4. 小规模 fixture 测试

暂时不做：

- QiMeng-Agent 集成
- RTLLM 全量
- 大规模 mutant 框架

这样能最快把“架构闭环”搭起来，同时把风险控制在最小范围。

## 成功标准

当以下条件满足时，可以认为 Phase 7/8 第一阶段落地成功：

1. `cocoverify2 verify` 能跑通最小闭环
2. `repair planner` 能输出合理的 stage-local 修复建议
3. golden DUT 能通过
4. 至少一组 bad DUT / mutant DUT 能被拦下
5. `verification_report.json` 可稳定产出
6. 整个流程不依赖 benchmark leakage
7. 还没有接入 QiMeng-Agent，也能单独证明 TB 验证闭环成立

## 结语

Phase 7/8 的目标不是“让 cocoverify2 再多跑一轮”，而是建立一条清晰、可审计、可收敛的 TB 验证闭环：

- 先验证 TB 是否可信
- 再把可信 TB 提供给外部 agent 使用

只有先把这件事在 `cocoverify2` 内部做好，后续 `QiMeng-Agent` 的反馈验证才会真正稳定。
