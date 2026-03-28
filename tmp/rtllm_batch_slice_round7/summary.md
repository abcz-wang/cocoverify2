# RTLLM Batch Summary

- Benchmark root: `/workspace/I/qimeng6/wangchuanhao/QiMeng-Agent/VerilogBenchmark/Benchmarks/RTLLM_for_ivl`
- Output dir: `/workspace/I/qimeng6/wangchuanhao/cocoverify2/tmp/rtllm_batch_slice_round7`
- Pipeline: `contract -> plan(hybrid) -> oracle(hybrid) -> render -> run -> triage`
- Experimental fill used: `False`

## Aggregate Metrics

- Discovered tasks: 6
- Valid contract: 6
- Valid plan: 6
- Valid oracle: 6
- Valid render: 6
- Tasks with >=1 successful run: 6
- Tasks with all rendered modules successful: 6
- False positive count on verified RTL: 0
- Tasks with guarded/unresolved policies: 6

## Histograms

- Triage: `{"no_failure": 8}`
- Assertion strength: `{"exact": 0, "guarded": 6, "unresolved": 30}`

## Per-Task Rollup

| Task | Status | Modules | Assertion Strengths | Failure Summary |
| --- | --- | --- | --- | --- |
| JC_counter | success | test_verified_JC_counter_basic:success/no_failure | exact=0, guarded=0, unresolved=5 | - |
| LFSR | success | test_LFSR_basic:success/no_failure | exact=0, guarded=0, unresolved=5 | - |
| RAM | success | test_verified_RAM_basic:success/no_failure, test_verified_RAM_edge:success/no_failure | exact=0, guarded=4, unresolved=5 | - |
| calendar | success | test_verified_calendar_basic:success/no_failure | exact=0, guarded=0, unresolved=9 | - |
| sequence_detector | success | test_sequence_detector_basic:success/no_failure | exact=0, guarded=0, unresolved=3 | - |
| synchronizer | success | test_verified_synchronizer_basic:success/no_failure, test_verified_synchronizer_edge:success/no_failure | exact=0, guarded=2, unresolved=3 | - |
