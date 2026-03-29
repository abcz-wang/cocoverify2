# RTLLM Batch Summary

- Benchmark root: `/workspace/I/qimeng6/wangchuanhao/QiMeng-Agent/VerilogBenchmark/Benchmarks/RTLLM_for_ivl`
- Output dir: `/workspace/I/qimeng6/wangchuanhao/cocoverify2/tmp/rtllm_batch_round5_slice`
- Pipeline: `contract -> plan(hybrid) -> oracle(hybrid) -> render -> run -> triage`
- Experimental fill used: `False`
- LLM runtime policy: `provider=openai, model=oss, trust_env=False, disable_proxies=True`

## Aggregate Metrics

- Discovered tasks: 4
- Valid contract: 4
- Valid plan: 4
- Valid oracle: 4
- Valid render: 4
- Tasks with >=1 successful run: 3
- Tasks with all rendered modules successful: 1
- False positive count on verified RTL: 3
- Tasks with guarded/unresolved policies: 4
- LLM plan attempted/succeeded/fallback: 4/4/0
- LLM oracle attempted/succeeded/fallback: 4/4/0

## Histograms

- Triage: `{"no_failure": 4, "runtime_test_failure": 4}`
- Assertion strength: `{"exact": 33, "guarded": 23, "unresolved": 82}`
- LLM plan status: `{"merged": 4}`
- LLM oracle status: `{"merged": 4}`

## Per-Task Rollup

| Task | Status | LLM(plan/oracle) | Modules | Assertion Strengths | Failure Summary |
| --- | --- | --- | --- | --- | --- |
| LIFObuffer | partial_success | merged/merged | test_LIFObuffer_basic:success/no_failure, test_LIFObuffer_edge:runtime_error/runtime_test_failure | exact=13, guarded=0, unresolved=31 | module_failures=test_LIFObuffer_edge:runtime_error/runtime_test_failure |
| ROM | success | merged/merged | test_ROM_basic:success/no_failure, test_ROM_edge:success/no_failure | exact=0, guarded=0, unresolved=5 | - |
| alu | failed | merged/merged | test_verified_alu_basic:runtime_error/runtime_test_failure, test_verified_alu_edge:runtime_error/runtime_test_failure | exact=0, guarded=23, unresolved=38 | module_failures=test_verified_alu_basic:runtime_error/runtime_test_failure, test_verified_alu_edge:runtime_error/runtime_test_failure |
| serial2parallel | partial_success | merged/merged | test_verified_serial2parallel_basic:success/no_failure, test_verified_serial2parallel_edge:runtime_error/runtime_test_failure | exact=20, guarded=0, unresolved=8 | module_failures=test_verified_serial2parallel_edge:runtime_error/runtime_test_failure |
