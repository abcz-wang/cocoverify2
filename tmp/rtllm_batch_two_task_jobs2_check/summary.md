# RTLLM Batch Summary

- Benchmark root: `/workspace/I/qimeng6/wangchuanhao/QiMeng-Agent/VerilogBenchmark/Benchmarks/RTLLM_for_ivl`
- Output dir: `/workspace/I/qimeng6/wangchuanhao/cocoverify2/tmp/rtllm_batch_two_task_jobs2_check`
- Pipeline: `contract -> plan(hybrid) -> oracle(hybrid) -> render -> run -> triage`
- Experimental fill used: `False`
- LLM runtime policy: `provider=openai, model=oss, trust_env=False, disable_proxies=True`
- Batch execution policy: `jobs=2, resume=False`

## Aggregate Metrics

- Discovered tasks: 2
- Valid contract: 2
- Valid plan: 2
- Valid oracle: 2
- Valid render: 2
- Tasks with >=1 successful run: 2
- Tasks with all rendered modules successful: 2
- False positive count on verified RTL: 0
- Tasks with guarded/unresolved policies: 2
- LLM plan attempted/succeeded/fallback: 2/2/0
- LLM oracle attempted/succeeded/fallback: 2/2/0
- Resumed tasks: 0

## Histograms

- Triage: `{"no_failure": 5}`
- Assertion strength: `{"exact": 0, "guarded": 22, "unresolved": 49}`
- LLM plan status: `{"merged": 2}`
- LLM oracle status: `{"merged": 2}`

## Per-Task Rollup

| Task | Status | LLM(plan/oracle) | Modules | Assertion Strengths | Failure Summary |
| --- | --- | --- | --- | --- | --- |
| adder_pipe_64bit | success | merged/merged | test_verified_adder_64bit_basic:success/no_failure, test_verified_adder_64bit_protocol:success/no_failure, test_verified_adder_64bit_edge:success/no_failure | exact=0, guarded=0, unresolved=26 | - |
| alu | success | merged/merged | test_verified_alu_basic:success/no_failure, test_verified_alu_edge:success/no_failure | exact=0, guarded=22, unresolved=23 | - |
