# RTLLM Batch Summary

- Benchmark root: `/workspace/I/qimeng6/wangchuanhao/QiMeng-Agent/VerilogBenchmark/Benchmarks/RTLLM_for_ivl`
- Output dir: `/workspace/I/qimeng6/wangchuanhao/cocoverify2/tmp/rtllm_batch_round5_slice3`
- Pipeline: `contract -> plan(hybrid) -> oracle(hybrid) -> render -> run -> triage`
- Experimental fill used: `False`
- LLM runtime policy: `provider=openai, model=oss, trust_env=False, disable_proxies=True`

## Aggregate Metrics

- Discovered tasks: 4
- Valid contract: 4
- Valid plan: 4
- Valid oracle: 4
- Valid render: 4
- Tasks with >=1 successful run: 4
- Tasks with all rendered modules successful: 3
- False positive count on verified RTL: 1
- Tasks with guarded/unresolved policies: 4
- LLM plan attempted/succeeded/fallback: 4/4/0
- LLM oracle attempted/succeeded/fallback: 4/4/0

## Histograms

- Triage: `{"no_failure": 7, "runtime_test_failure": 1}`
- Assertion strength: `{"exact": 29, "guarded": 17, "unresolved": 87}`
- LLM plan status: `{"merged": 4}`
- LLM oracle status: `{"merged": 4}`

## Per-Task Rollup

| Task | Status | LLM(plan/oracle) | Modules | Assertion Strengths | Failure Summary |
| --- | --- | --- | --- | --- | --- |
| LIFObuffer | partial_success | merged/merged | test_LIFObuffer_basic:success/no_failure, test_LIFObuffer_edge:runtime_error/runtime_test_failure | exact=16, guarded=0, unresolved=35 | module_failures=test_LIFObuffer_edge:runtime_error/runtime_test_failure |
| ROM | success | merged/merged | test_ROM_basic:success/no_failure, test_ROM_edge:success/no_failure | exact=0, guarded=0, unresolved=7 | - |
| alu | success | merged/merged | test_verified_alu_basic:success/no_failure, test_verified_alu_edge:success/no_failure | exact=0, guarded=17, unresolved=39 | - |
| serial2parallel | success | merged/merged | test_verified_serial2parallel_basic:success/no_failure, test_verified_serial2parallel_edge:success/no_failure | exact=13, guarded=0, unresolved=6 | - |
