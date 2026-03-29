# RTLLM Batch Summary

- Benchmark root: `/workspace/I/qimeng6/wangchuanhao/QiMeng-Agent/VerilogBenchmark/Benchmarks/RTLLM_for_ivl`
- Output dir: `/workspace/I/qimeng6/wangchuanhao/cocoverify2/tmp/rtllm_batch_alu_llm_round5`
- Pipeline: `contract -> plan(hybrid) -> oracle(hybrid) -> render -> run -> triage`
- Experimental fill used: `False`
- LLM runtime policy: `provider=openai, model=oss, trust_env=False, disable_proxies=True`

## Aggregate Metrics

- Discovered tasks: 1
- Valid contract: 1
- Valid plan: 1
- Valid oracle: 1
- Valid render: 1
- Tasks with >=1 successful run: 1
- Tasks with all rendered modules successful: 0
- False positive count on verified RTL: 1
- Tasks with guarded/unresolved policies: 1
- LLM plan attempted/succeeded/fallback: 1/1/0
- LLM oracle attempted/succeeded/fallback: 1/0/1

## Histograms

- Triage: `{"no_failure": 1, "runtime_test_failure": 1}`
- Assertion strength: `{"exact": 0, "guarded": 4, "unresolved": 56}`
- LLM plan status: `{"merged": 1}`
- LLM oracle status: `{"fallback": 1}`

## Per-Task Rollup

| Task | Status | LLM(plan/oracle) | Modules | Assertion Strengths | Failure Summary |
| --- | --- | --- | --- | --- | --- |
| alu | partial_success | merged/fallback | test_verified_alu_basic:success/no_failure, test_verified_alu_edge:runtime_error/runtime_test_failure | exact=0, guarded=4, unresolved=56 | module_failures=test_verified_alu_edge:runtime_error/runtime_test_failure |
