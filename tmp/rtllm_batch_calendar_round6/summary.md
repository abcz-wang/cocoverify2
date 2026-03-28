# RTLLM Batch Summary

- Benchmark root: `/workspace/I/qimeng6/wangchuanhao/QiMeng-Agent/VerilogBenchmark/Benchmarks/RTLLM_for_ivl`
- Output dir: `/workspace/I/qimeng6/wangchuanhao/cocoverify2/tmp/rtllm_batch_calendar_round6`
- Pipeline: `contract -> plan(hybrid) -> oracle(hybrid) -> render -> run -> triage`
- Experimental fill used: `False`

## Aggregate Metrics

- Discovered tasks: 1
- Valid contract: 1
- Valid plan: 1
- Valid oracle: 1
- Valid render: 1
- Tasks with >=1 successful run: 1
- Tasks with all rendered modules successful: 1
- False positive count on verified RTL: 0
- Tasks with guarded/unresolved policies: 1

## Histograms

- Triage: `{"no_failure": 1}`
- Assertion strength: `{"exact": 0, "guarded": 0, "unresolved": 9}`

## Per-Task Rollup

| Task | Status | Modules | Assertion Strengths | Failure Summary |
| --- | --- | --- | --- | --- |
| calendar | success | test_verified_calendar_basic:success/no_failure | exact=0, guarded=0, unresolved=9 | - |
