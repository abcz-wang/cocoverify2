# RTLLM Batch Summary

- Benchmark root: `/workspace/I/qimeng6/wangchuanhao/QiMeng-Agent/VerilogBenchmark/Benchmarks/RTLLM_for_ivl`
- Output dir: `/workspace/I/qimeng6/wangchuanhao/cocoverify2/tmp/rtllm_batch_adder_timeout60_check`
- Pipeline: `contract -> plan(hybrid) -> oracle(hybrid) -> render -> run -> triage`
- Experimental fill used: `False`
- LLM runtime policy: `provider=openai, model=oss, trust_env=False, disable_proxies=True`
- Batch execution policy: `jobs=1, resume=False`

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
- LLM plan attempted/succeeded/fallback: 1/1/0
- LLM oracle attempted/succeeded/fallback: 1/1/0
- Resumed tasks: 0

## Histograms

- Triage: `{"no_failure": 3}`
- Assertion strength: `{"exact": 0, "guarded": 0, "unresolved": 31}`
- LLM plan status: `{"merged": 1}`
- LLM oracle status: `{"merged": 1}`

## Per-Task Rollup

| Task | Status | LLM(plan/oracle) | Modules | Assertion Strengths | Failure Summary |
| --- | --- | --- | --- | --- | --- |
| adder_pipe_64bit | success | merged/merged | test_verified_adder_64bit_basic:success/no_failure, test_verified_adder_64bit_protocol:success/no_failure, test_verified_adder_64bit_edge:success/no_failure | exact=0, guarded=0, unresolved=31 | - |
