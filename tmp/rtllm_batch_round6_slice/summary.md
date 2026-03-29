# RTLLM Batch Summary

- Benchmark root: `/workspace/I/qimeng6/wangchuanhao/QiMeng-Agent/VerilogBenchmark/Benchmarks/RTLLM_for_ivl`
- Output dir: `tmp/rtllm_batch_round6_slice`
- Pipeline: `contract -> plan(hybrid) -> oracle(hybrid) -> render -> run -> triage`
- Experimental fill used: `False`
- LLM runtime policy: `provider=openai, model=oss, trust_env=False, disable_proxies=True`

## Aggregate Metrics

- Discovered tasks: 7
- Valid contract: 7
- Valid plan: 7
- Valid oracle: 7
- Valid render: 7
- Tasks with >=1 successful run: 7
- Tasks with all rendered modules successful: 7
- False positive count on verified RTL: 0
- Tasks with guarded/unresolved policies: 6
- LLM plan attempted/succeeded/fallback: 7/7/0
- LLM oracle attempted/succeeded/fallback: 7/7/0

## Histograms

- Triage: `{"no_failure": 16}`
- Assertion strength: `{"exact": 38, "guarded": 14, "unresolved": 112}`
- LLM plan status: `{"merged": 7}`
- LLM oracle status: `{"merged": 7}`

## Per-Task Rollup

| Task | Status | LLM(plan/oracle) | Modules | Assertion Strengths | Failure Summary |
| --- | --- | --- | --- | --- | --- |
| RAM | success | merged/merged | test_verified_RAM_basic:success/no_failure, test_verified_RAM_edge:success/no_failure | exact=2, guarded=0, unresolved=7 | - |
| alu | success | merged/merged | test_verified_alu_basic:success/no_failure, test_verified_alu_edge:success/no_failure | exact=0, guarded=11, unresolved=25 | - |
| clkgenerator | success | merged/merged | test_clkgenerator_basic:success/no_failure, test_clkgenerator_edge:success/no_failure | exact=0, guarded=0, unresolved=4 | - |
| edge_detect | success | merged/merged | test_verified_edge_detect_basic:success/no_failure, test_verified_edge_detect_edge:success/no_failure | exact=10, guarded=0, unresolved=16 | - |
| parallel2serial | success | merged/merged | test_verified_parallel2serial_basic:success/no_failure, test_verified_parallel2serial_protocol:success/no_failure, test_verified_parallel2serial_edge:success/no_failure | exact=18, guarded=0, unresolved=0 | - |
| serial2parallel | success | merged/merged | test_verified_serial2parallel_basic:success/no_failure, test_verified_serial2parallel_protocol:success/no_failure, test_verified_serial2parallel_edge:success/no_failure | exact=8, guarded=0, unresolved=11 | - |
| traffic_light | success | merged/merged | test_verified_traffic_light_basic:success/no_failure, test_verified_traffic_light_edge:success/no_failure | exact=0, guarded=3, unresolved=49 | - |
