# RTLLM Batch Summary

- Benchmark root: `/workspace/I/qimeng6/wangchuanhao/QiMeng-Agent/VerilogBenchmark/Benchmarks/RTLLM_for_ivl`
- Output dir: `/workspace/I/qimeng6/wangchuanhao/cocoverify2/tmp/hybrid_generalization_regression_slice_20260331_v3`
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
- Tasks with >=1 successful run: 3
- Tasks with all rendered modules successful: 2
- False positive count on verified RTL: 4
- Tasks with guarded/unresolved policies: 6
- LLM plan attempted/succeeded/fallback: 6/6/0
- LLM oracle attempted/succeeded/fallback: 6/6/0
- Resumed tasks: 0

## Histograms

- Triage: `{"no_failure": 4, "runtime_test_failure": 9}`
- Assertion strength: `{"exact": 56, "guarded": 27, "unresolved": 94}`
- LLM plan status: `{"merged": 6}`
- LLM plan fallback reasons: `{}`
- LLM oracle status: `{"merged": 6}`
- LLM oracle fallback reasons: `{}`

## Per-Task Rollup

| Task | Status | LLM(plan/oracle) | Modules | Assertion Strengths | Failure Summary |
| --- | --- | --- | --- | --- | --- |
| accu | failed | merged/merged | test_accu_basic:runtime_error/runtime_test_failure, test_accu_protocol:runtime_error/runtime_test_failure, test_accu_edge:runtime_error/runtime_test_failure | exact=25, guarded=0, unresolved=10 | module_failures=test_accu_basic:runtime_error/runtime_test_failure, test_accu_protocol:runtime_error/runtime_test_failure, test_accu_edge:runtime_error/runtime_test_failure |
| multi_16bit | failed | merged/merged | test_verified_multi_16bit_basic:runtime_error/runtime_test_failure, test_verified_multi_16bit_protocol:runtime_error/runtime_test_failure, test_verified_multi_16bit_edge:runtime_error/runtime_test_failure | exact=3, guarded=19, unresolved=5 | module_failures=test_verified_multi_16bit_basic:runtime_error/runtime_test_failure, test_verified_multi_16bit_protocol:runtime_error/runtime_test_failure, test_verified_multi_16bit_edge:runtime_error/runtime_test_failure |
| multi_booth_8bit | failed | merged/merged | test_verified_multi_booth_8bit_basic:runtime_error/runtime_test_failure, test_verified_multi_booth_8bit_edge:runtime_error/runtime_test_failure | exact=16, guarded=5, unresolved=9 | module_failures=test_verified_multi_booth_8bit_basic:runtime_error/runtime_test_failure, test_verified_multi_booth_8bit_edge:runtime_error/runtime_test_failure |
| ring_counter | success | merged/merged | test_ring_counter_basic:success/no_failure | exact=0, guarded=0, unresolved=9 | - |
| serial2parallel | success | merged/merged | test_verified_serial2parallel_basic:success/no_failure, test_verified_serial2parallel_edge:success/no_failure | exact=12, guarded=0, unresolved=13 | - |
| traffic_light | partial_success | merged/merged | test_verified_traffic_light_basic:success/no_failure, test_verified_traffic_light_edge:runtime_error/runtime_test_failure | exact=0, guarded=3, unresolved=48 | module_failures=test_verified_traffic_light_edge:runtime_error/runtime_test_failure |
