# RTLLM Batch Summary

- Benchmark root: `/workspace/I/qimeng6/wangchuanhao/QiMeng-Agent/VerilogBenchmark/Benchmarks/RTLLM_for_ivl`
- Output dir: `/workspace/I/qimeng6/wangchuanhao/cocoverify2/tmp/hybrid_generalization_slice_20260331`
- Pipeline: `contract -> plan(hybrid) -> oracle(hybrid) -> render -> run -> triage`
- Experimental fill used: `False`
- LLM runtime policy: `provider=openai, model=oss, trust_env=False, disable_proxies=True`
- Batch execution policy: `jobs=2, resume=False`

## Aggregate Metrics

- Discovered tasks: 9
- Valid contract: 9
- Valid plan: 9
- Valid oracle: 9
- Valid render: 9
- Tasks with >=1 successful run: 8
- Tasks with all rendered modules successful: 6
- False positive count on verified RTL: 3
- Tasks with guarded/unresolved policies: 8
- LLM plan attempted/succeeded/fallback: 9/0/9
- LLM oracle attempted/succeeded/fallback: 9/7/2
- Resumed tasks: 0

## Histograms

- Triage: `{"no_failure": 12, "runtime_test_failure": 5}`
- Assertion strength: `{"exact": 12, "guarded": 0, "unresolved": 85}`
- LLM plan status: `{"fallback": 9}`
- LLM plan fallback reasons: `{"timeout": 9}`
- LLM oracle status: `{"fallback": 2, "merged": 7}`
- LLM oracle fallback reasons: `{"timeout": 2}`

## Per-Task Rollup

| Task | Status | LLM(plan/oracle) | Modules | Assertion Strengths | Failure Summary |
| --- | --- | --- | --- | --- | --- |
| accu | failed | fallback/fallback | test_accu_basic:runtime_error/runtime_test_failure, test_accu_protocol:runtime_error/runtime_test_failure, test_accu_edge:runtime_error/runtime_test_failure | exact=1, guarded=0, unresolved=9 | module_failures=test_accu_basic:runtime_error/runtime_test_failure, test_accu_protocol:runtime_error/runtime_test_failure, test_accu_edge:runtime_error/runtime_test_failure |
| asyn_fifo | success | fallback/fallback | test_dual_port_RAM_basic:success/no_failure, test_dual_port_RAM_edge:success/no_failure | exact=0, guarded=0, unresolved=3 | - |
| freq_divbyeven | success | fallback/merged | test_freq_divbyeven_basic:success/no_failure | exact=0, guarded=0, unresolved=3 | - |
| multi_pipe_8bit | success | fallback/merged | test_verified_multi_pipe_8bit_basic:success/no_failure, test_verified_multi_pipe_8bit_edge:success/no_failure | exact=10, guarded=0, unresolved=12 | - |
| ring_counter | success | fallback/merged | test_ring_counter_basic:success/no_failure | exact=0, guarded=0, unresolved=9 | - |
| sequence_detector | success | fallback/merged | test_sequence_detector_basic:success/no_failure, test_sequence_detector_edge:success/no_failure | exact=0, guarded=0, unresolved=0 | - |
| serial2parallel | partial_success | fallback/merged | test_verified_serial2parallel_basic:success/no_failure, test_verified_serial2parallel_edge:runtime_error/runtime_test_failure | exact=0, guarded=0, unresolved=12 | module_failures=test_verified_serial2parallel_edge:runtime_error/runtime_test_failure |
| traffic_light | partial_success | fallback/merged | test_verified_traffic_light_basic:runtime_error/runtime_test_failure, test_verified_traffic_light_edge:success/no_failure | exact=0, guarded=0, unresolved=33 | module_failures=test_verified_traffic_light_basic:runtime_error/runtime_test_failure |
| width_8to16 | success | fallback/merged | test_verified_width_8to16_basic:success/no_failure, test_verified_width_8to16_edge:success/no_failure | exact=1, guarded=0, unresolved=4 | - |
