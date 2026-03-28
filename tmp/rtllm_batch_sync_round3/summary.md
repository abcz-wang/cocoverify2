# RTLLM Batch Summary

- Benchmark root: `/workspace/I/qimeng6/wangchuanhao/QiMeng-Agent/VerilogBenchmark/Benchmarks/RTLLM_for_ivl`
- Output dir: `/workspace/I/qimeng6/wangchuanhao/cocoverify2/tmp/rtllm_batch_sync_round3`
- Pipeline: `contract -> plan(hybrid) -> oracle(hybrid) -> render -> run -> triage`
- Experimental fill used: `False`

## Aggregate Metrics

- Discovered tasks: 1
- Valid contract: 1
- Valid plan: 1
- Valid oracle: 1
- Valid render: 1
- Tasks with >=1 successful run: 1
- Tasks with all rendered modules successful: 0
- False positive count on verified RTL: 1
- Tasks with guarded/unresolved policies: 1

## Histograms

- Triage: `{"no_failure": 1, "runtime_test_failure": 1}`
- Assertion strength: `{"exact": 0, "guarded": 2, "unresolved": 3}`

## Per-Task Rollup

| Task | Status | Modules | Assertion Strengths | Failure Summary |
| --- | --- | --- | --- | --- |
| synchronizer | partial_success | test_verified_synchronizer_basic:success/no_failure, test_verified_synchronizer_edge:runtime_error/runtime_test_failure | exact=0, guarded=2, unresolved=3 | module_failures=test_verified_synchronizer_edge:runtime_error/runtime_test_failure |
