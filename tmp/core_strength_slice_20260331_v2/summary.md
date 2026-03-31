# RTLLM Batch Summary

- Benchmark root: `/workspace/I/qimeng6/wangchuanhao/QiMeng-Agent/VerilogBenchmark/Benchmarks/RTLLM_for_ivl`
- Output dir: `/workspace/I/qimeng6/wangchuanhao/cocoverify2/tmp/core_strength_slice_20260331_v2`
- Pipeline: `contract -> plan(rule_based) -> oracle(rule_based) -> render -> run -> triage`
- Experimental fill used: `False`
- LLM runtime policy: `provider=openai, model=oss, trust_env=False, disable_proxies=False`
- Batch execution policy: `jobs=1, resume=False`

## Aggregate Metrics

- Discovered tasks: 4
- Valid contract: 4
- Valid plan: 4
- Valid oracle: 4
- Valid render: 4
- Tasks with >=1 successful run: 3
- Tasks with all rendered modules successful: 2
- False positive count on verified RTL: 2
- Tasks with guarded/unresolved policies: 4
- LLM plan attempted/succeeded/fallback: 0/0/0
- LLM oracle attempted/succeeded/fallback: 0/0/0
- Resumed tasks: 0

## Histograms

- Triage: `{"no_failure": 4, "runtime_test_failure": 4}`
- Assertion strength: `{"exact": 33, "guarded": 2, "unresolved": 61}`
- LLM plan status: `{"not_attempted": 4}`
- LLM plan fallback reasons: `{}`
- LLM oracle status: `{"not_attempted": 4}`
- LLM oracle fallback reasons: `{}`

## Per-Task Rollup

| Task | Status | LLM(plan/oracle) | Modules | Assertion Strengths | Failure Summary |
| --- | --- | --- | --- | --- | --- |
| accu | failed | not_attempted/not_attempted | test_accu_basic:runtime_error/runtime_test_failure, test_accu_protocol:runtime_error/runtime_test_failure, test_accu_edge:runtime_error/runtime_test_failure | exact=24, guarded=0, unresolved=9 | module_failures=test_accu_basic:runtime_error/runtime_test_failure, test_accu_protocol:runtime_error/runtime_test_failure, test_accu_edge:runtime_error/runtime_test_failure |
| ring_counter | success | not_attempted/not_attempted | test_ring_counter_basic:success/no_failure | exact=0, guarded=0, unresolved=6 | - |
| serial2parallel | partial_success | not_attempted/not_attempted | test_verified_serial2parallel_basic:success/no_failure, test_verified_serial2parallel_edge:runtime_error/runtime_test_failure | exact=9, guarded=0, unresolved=12 | module_failures=test_verified_serial2parallel_edge:runtime_error/runtime_test_failure |
| traffic_light | success | not_attempted/not_attempted | test_verified_traffic_light_basic:success/no_failure, test_verified_traffic_light_edge:success/no_failure | exact=0, guarded=2, unresolved=34 | - |
