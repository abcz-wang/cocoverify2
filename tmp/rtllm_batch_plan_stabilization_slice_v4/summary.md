# RTLLM Batch Summary

- Benchmark root: `/workspace/I/qimeng6/wangchuanhao/QiMeng-Agent/VerilogBenchmark/Benchmarks/RTLLM_for_ivl`
- Output dir: `/workspace/I/qimeng6/wangchuanhao/cocoverify2/tmp/rtllm_batch_plan_stabilization_slice_v4`
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
- Tasks with guarded/unresolved policies: 8
- LLM plan attempted/succeeded/fallback: 8/7/1
- LLM oracle attempted/succeeded/fallback: 8/8/0
- Resumed tasks: 0

## Histograms

- Triage: `{"no_failure": 15}`
- Assertion strength: `{"exact": 34, "guarded": 19, "unresolved": 121}`
- LLM plan status: `{"fallback": 1, "merged": 7}`
- LLM plan fallback reasons: `{"timeout": 1}`
- LLM oracle status: `{"merged": 8}`
- LLM oracle fallback reasons: `{}`

## Per-Task Rollup

| Task | Status | LLM(plan/oracle) | Modules | Assertion Strengths | Failure Summary |
| --- | --- | --- | --- | --- | --- |
| LIFObuffer | success | merged/merged | test_LIFObuffer_basic:success/no_failure, test_LIFObuffer_edge:success/no_failure | exact=7, guarded=0, unresolved=19 | - |
| alu | success | merged/merged | test_verified_alu_basic:success/no_failure, test_verified_alu_edge:success/no_failure | exact=0, guarded=14, unresolved=21 | - |
| asyn_fifo | success | fallback/merged | test_dual_port_RAM_basic:success/no_failure, test_dual_port_RAM_edge:success/no_failure | exact=0, guarded=0, unresolved=9 | - |
| calendar | success | merged/merged | test_verified_calendar_basic:success/no_failure | exact=0, guarded=0, unresolved=18 | - |
| multi_booth_8bit | success | merged/merged | test_verified_multi_booth_8bit_basic:success/no_failure, test_verified_multi_booth_8bit_edge:success/no_failure | exact=11, guarded=2, unresolved=8 | - |
| parallel2serial | success | merged/merged | test_verified_parallel2serial_basic:success/no_failure, test_verified_parallel2serial_edge:success/no_failure | exact=16, guarded=0, unresolved=1 | - |
| sub_64bit | success | merged/merged | test_sub_64bit_basic:success/no_failure, test_sub_64bit_edge:success/no_failure | exact=0, guarded=1, unresolved=3 | - |
| traffic_light | success | merged/merged | test_verified_traffic_light_basic:success/no_failure, test_verified_traffic_light_edge:success/no_failure | exact=0, guarded=2, unresolved=42 | - |
