# RTLLM Batch Summary

- Benchmark root: `/workspace/I/qimeng6/wangchuanhao/QiMeng-Agent/VerilogBenchmark/Benchmarks/RTLLM_for_ivl`
- Output dir: `/workspace/I/qimeng6/wangchuanhao/cocoverify2/tmp/rtllm_batch_targeted_reliability_v4`
- Pipeline: `contract -> plan(hybrid) -> oracle(hybrid) -> render -> run -> triage`
- Experimental fill used: `False`
- LLM runtime policy: `provider=openai, model=oss, trust_env=False, disable_proxies=True`
- Batch execution policy: `jobs=1, resume=False`

## Aggregate Metrics

- Discovered tasks: 6
- Valid contract: 6
- Valid plan: 6
- Valid oracle: 6
- Valid render: 6
- Tasks with >=1 successful run: 6
- Tasks with all rendered modules successful: 6
- False positive count on verified RTL: 0
- Tasks with guarded/unresolved policies: 5
- LLM plan attempted/succeeded/fallback: 6/1/5
- LLM oracle attempted/succeeded/fallback: 6/6/0
- Resumed tasks: 0

## Histograms

- Triage: `{"no_failure": 12}`
- Assertion strength: `{"exact": 21, "guarded": 16, "unresolved": 63}`
- LLM plan status: `{"fallback": 5, "merged": 1}`
- LLM oracle status: `{"merged": 6}`

## Per-Task Rollup

| Task | Status | LLM(plan/oracle) | Modules | Assertion Strengths | Failure Summary |
| --- | --- | --- | --- | --- | --- |
| adder_pipe_64bit | success | fallback/merged | test_verified_adder_64bit_basic:success/no_failure, test_verified_adder_64bit_edge:success/no_failure | exact=0, guarded=0, unresolved=18 | - |
| alu | success | fallback/merged | test_verified_alu_basic:success/no_failure, test_verified_alu_edge:success/no_failure | exact=0, guarded=14, unresolved=21 | - |
| multi_booth_8bit | success | fallback/merged | test_verified_multi_booth_8bit_basic:success/no_failure, test_verified_multi_booth_8bit_edge:success/no_failure | exact=11, guarded=2, unresolved=9 | - |
| parallel2serial | success | fallback/merged | test_verified_parallel2serial_basic:success/no_failure, test_verified_parallel2serial_edge:success/no_failure | exact=0, guarded=0, unresolved=0 | - |
| square_wave | success | fallback/merged | test_square_wave_basic:success/no_failure, test_square_wave_edge:success/no_failure | exact=0, guarded=0, unresolved=8 | - |
| width_8to16 | success | merged/merged | test_verified_width_8to16_basic:success/no_failure, test_verified_width_8to16_edge:success/no_failure | exact=10, guarded=0, unresolved=7 | - |
