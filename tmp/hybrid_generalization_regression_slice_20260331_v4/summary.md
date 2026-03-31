# RTLLM Batch Summary

- Benchmark root: `/workspace/I/qimeng6/wangchuanhao/QiMeng-Agent/VerilogBenchmark/Benchmarks/RTLLM_for_ivl`
- Output dir: `/workspace/I/qimeng6/wangchuanhao/cocoverify2/tmp/hybrid_generalization_regression_slice_20260331_v4`
- Pipeline: `contract -> plan(hybrid) -> oracle(hybrid) -> render -> run -> triage`
- Experimental fill used: `False`
- LLM runtime policy: `provider=openai, model=oss, trust_env=False, disable_proxies=True`
- Batch execution policy: `jobs=2, resume=False`

## Aggregate Metrics

- Discovered tasks: 6
- Valid contract: 6
- Valid plan: 6
- Valid oracle: 6
- Valid render: 6
- Tasks with >=1 successful run: 5
- Tasks with all rendered modules successful: 5
- False positive count on verified RTL: 1
- Tasks with guarded/unresolved policies: 6
- LLM plan attempted/succeeded/fallback: 6/6/0
- LLM oracle attempted/succeeded/fallback: 6/6/0
- Resumed tasks: 0

## Histograms

- Triage: `{"no_failure": 10, "runtime_test_failure": 3}`
- Assertion strength: `{"exact": 14, "guarded": 18, "unresolved": 91}`
- LLM plan status: `{"merged": 6}`
- LLM plan fallback reasons: `{}`
- LLM oracle status: `{"merged": 6}`
- LLM oracle fallback reasons: `{}`

## Per-Task Rollup

| Task | Status | LLM(plan/oracle) | Modules | Assertion Strengths | Failure Summary |
| --- | --- | --- | --- | --- | --- |
| accu | failed | merged/merged | test_accu_basic:runtime_error/runtime_test_failure, test_accu_protocol:runtime_error/runtime_test_failure, test_accu_edge:runtime_error/runtime_test_failure | exact=1, guarded=0, unresolved=9 | module_failures=test_accu_basic:runtime_error/runtime_test_failure, test_accu_protocol:runtime_error/runtime_test_failure, test_accu_edge:runtime_error/runtime_test_failure |
| multi_16bit | success | merged/merged | test_verified_multi_16bit_basic:success/no_failure, test_verified_multi_16bit_protocol:success/no_failure, test_verified_multi_16bit_edge:success/no_failure | exact=2, guarded=14, unresolved=9 | - |
| multi_booth_8bit | success | merged/merged | test_verified_multi_booth_8bit_basic:success/no_failure, test_verified_multi_booth_8bit_edge:success/no_failure | exact=11, guarded=2, unresolved=10 | - |
| ring_counter | success | merged/merged | test_ring_counter_basic:success/no_failure | exact=0, guarded=0, unresolved=9 | - |
| serial2parallel | success | merged/merged | test_verified_serial2parallel_basic:success/no_failure, test_verified_serial2parallel_edge:success/no_failure | exact=0, guarded=0, unresolved=10 | - |
| traffic_light | success | merged/merged | test_verified_traffic_light_basic:success/no_failure, test_verified_traffic_light_edge:success/no_failure | exact=0, guarded=2, unresolved=44 | - |
