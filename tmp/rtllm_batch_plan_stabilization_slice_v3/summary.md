# RTLLM Batch Summary

- Benchmark root: `/workspace/I/qimeng6/wangchuanhao/QiMeng-Agent/VerilogBenchmark/Benchmarks/RTLLM_for_ivl`
- Output dir: `/workspace/I/qimeng6/wangchuanhao/cocoverify2/tmp/rtllm_batch_plan_stabilization_slice_v3`
- Pipeline: `contract -> plan(hybrid) -> oracle(hybrid) -> render -> run -> triage`
- Experimental fill used: `False`
- LLM runtime policy: `provider=openai, model=oss, trust_env=False, disable_proxies=True`
- Batch execution policy: `jobs=2, resume=False`

## Aggregate Metrics

- Discovered tasks: 8
- Valid contract: 8
- Valid plan: 8
- Valid oracle: 8
- Valid render: 8
- Tasks with >=1 successful run: 8
- Tasks with all rendered modules successful: 8
- False positive count on verified RTL: 0
- Tasks with guarded/unresolved policies: 7
- LLM plan attempted/succeeded/fallback: 8/2/6
- LLM oracle attempted/succeeded/fallback: 8/7/1
- Resumed tasks: 0

## Histograms

- Triage: `{"no_failure": 15}`
- Assertion strength: `{"exact": 19, "guarded": 14, "unresolved": 94}`
- LLM plan status: `{"fallback": 6, "merged": 2}`
- LLM plan fallback reasons: `{"timeout": 6}`
- LLM oracle status: `{"fallback": 1, "merged": 7}`
- LLM oracle fallback reasons: `{"timeout": 1}`

## Per-Task Rollup

| Task | Status | LLM(plan/oracle) | Modules | Assertion Strengths | Failure Summary |
| --- | --- | --- | --- | --- | --- |
| LIFObuffer | success | merged/merged | test_LIFObuffer_basic:success/no_failure, test_LIFObuffer_edge:success/no_failure | exact=9, guarded=0, unresolved=22 | - |
| alu | success | merged/merged | test_verified_alu_basic:success/no_failure, test_verified_alu_edge:success/no_failure | exact=0, guarded=12, unresolved=20 | - |
| asyn_fifo | success | fallback/merged | test_dual_port_RAM_basic:success/no_failure, test_dual_port_RAM_edge:success/no_failure | exact=0, guarded=0, unresolved=5 | - |
| calendar | success | fallback/merged | test_verified_calendar_basic:success/no_failure | exact=0, guarded=0, unresolved=12 | - |
| multi_booth_8bit | success | fallback/merged | test_verified_multi_booth_8bit_basic:success/no_failure, test_verified_multi_booth_8bit_edge:success/no_failure | exact=10, guarded=2, unresolved=8 | - |
| parallel2serial | success | fallback/fallback | test_verified_parallel2serial_basic:success/no_failure, test_verified_parallel2serial_edge:success/no_failure | exact=0, guarded=0, unresolved=0 | - |
| sub_64bit | success | fallback/merged | test_sub_64bit_basic:success/no_failure, test_sub_64bit_edge:success/no_failure | exact=0, guarded=0, unresolved=3 | - |
| traffic_light | success | fallback/merged | test_verified_traffic_light_basic:success/no_failure, test_verified_traffic_light_edge:success/no_failure | exact=0, guarded=0, unresolved=24 | - |
