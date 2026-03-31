# RTLLM Batch Summary

- Benchmark root: `/workspace/I/qimeng6/wangchuanhao/QiMeng-Agent/VerilogBenchmark/Benchmarks/RTLLM_for_ivl`
- Output dir: `/workspace/I/qimeng6/wangchuanhao/cocoverify2/tmp/hybrid_generalization_full_20260331`
- Pipeline: `contract -> plan(hybrid) -> oracle(hybrid) -> render -> run -> triage`
- Experimental fill used: `False`
- LLM runtime policy: `provider=openai, model=oss, trust_env=False, disable_proxies=True`
- Batch execution policy: `jobs=2, resume=False`

## Aggregate Metrics

- Discovered tasks: 50
- Valid contract: 50
- Valid plan: 50
- Valid oracle: 50
- Valid render: 50
- Tasks with >=1 successful run: 46
- Tasks with all rendered modules successful: 44
- False positive count on verified RTL: 5
- Tasks with guarded/unresolved policies: 46
- LLM plan attempted/succeeded/fallback: 50/19/31
- LLM oracle attempted/succeeded/fallback: 50/42/8
- Resumed tasks: 0

## Histograms

- Triage: `{"insufficient_stimulus": 1, "no_failure": 80, "runtime_test_failure": 10}`
- Assertion strength: `{"exact": 112, "guarded": 91, "unresolved": 434}`
- LLM plan status: `{"fallback": 31, "merged": 19}`
- LLM plan fallback reasons: `{"timeout": 31}`
- LLM oracle status: `{"fallback": 8, "merged": 42}`
- LLM oracle fallback reasons: `{"timeout": 8}`

## Per-Task Rollup

| Task | Status | LLM(plan/oracle) | Modules | Assertion Strengths | Failure Summary |
| --- | --- | --- | --- | --- | --- |
| JC_counter | success | fallback/merged | test_verified_JC_counter_basic:success/no_failure | exact=4, guarded=0, unresolved=3 | - |
| LFSR | success | fallback/merged | test_LFSR_basic:success/no_failure | exact=0, guarded=0, unresolved=6 | - |
| LIFObuffer | success | fallback/fallback | test_LIFObuffer_basic:success/no_failure, test_LIFObuffer_edge:success/no_failure | exact=7, guarded=0, unresolved=18 | - |
| RAM | success | fallback/fallback | test_verified_RAM_basic:success/no_failure, test_verified_RAM_edge:success/no_failure | exact=2, guarded=0, unresolved=4 | - |
| ROM | success | merged/merged | test_ROM_basic:success/no_failure, test_ROM_edge:success/no_failure | exact=0, guarded=1, unresolved=3 | - |
| accu | failed | fallback/merged | test_accu_basic:runtime_error/runtime_test_failure, test_accu_protocol:runtime_error/runtime_test_failure, test_accu_edge:runtime_error/runtime_test_failure | exact=1, guarded=0, unresolved=9 | module_failures=test_accu_basic:runtime_error/runtime_test_failure, test_accu_protocol:runtime_error/runtime_test_failure, test_accu_edge:runtime_error/runtime_test_failure |
| adder_16bit | success | merged/merged | test_verified_adder_16bit_basic:success/no_failure, test_verified_adder_16bit_edge:success/no_failure | exact=0, guarded=2, unresolved=10 | - |
| adder_32bit | success | merged/merged | test_verified_adder_32bit_basic:success/no_failure | exact=0, guarded=0, unresolved=8 | - |
| adder_8bit | success | fallback/merged | test_verified_adder_8bit_basic:success/no_failure, test_verified_adder_8bit_edge:success/no_failure | exact=0, guarded=2, unresolved=12 | - |
| adder_bcd | success | fallback/merged | test_adder_bcd_basic:success/no_failure, test_adder_bcd_edge:success/no_failure | exact=0, guarded=1, unresolved=11 | - |
| adder_pipe_64bit | success | fallback/merged | test_verified_adder_64bit_basic:success/no_failure, test_verified_adder_64bit_edge:success/no_failure | exact=0, guarded=0, unresolved=22 | - |
| alu | success | merged/merged | test_verified_alu_basic:success/no_failure, test_verified_alu_edge:success/no_failure | exact=0, guarded=13, unresolved=17 | - |
| asyn_fifo | success | merged/merged | test_dual_port_RAM_basic:success/no_failure, test_dual_port_RAM_edge:success/no_failure | exact=0, guarded=0, unresolved=4 | - |
| barrel_shifter | success | merged/merged | test_barrel_shifter_basic:success/no_failure | exact=0, guarded=0, unresolved=5 | - |
| calendar | success | fallback/fallback | test_verified_calendar_basic:success/no_failure | exact=0, guarded=0, unresolved=9 | - |
| clkgenerator | failed | fallback/merged | test_clkgenerator_basic:success/insufficient_stimulus | exact=0, guarded=0, unresolved=2 | module_failures=test_clkgenerator_basic:success/insufficient_stimulus |
| comparator_3bit | success | fallback/fallback | test_comparator_3bit_basic:success/no_failure, test_comparator_3bit_edge:success/no_failure | exact=12, guarded=0, unresolved=0 | - |
| comparator_4bit | success | fallback/merged | test_comparator_4bit_basic:success/no_failure, test_comparator_4bit_edge:success/no_failure | exact=0, guarded=0, unresolved=18 | - |
| counter_12 | success | fallback/merged | test_verified_counter_12_basic:success/no_failure, test_verified_counter_12_edge:success/no_failure | exact=0, guarded=0, unresolved=11 | - |
| div_16bit | success | fallback/fallback | test_verified_div_16bit_basic:success/no_failure, test_verified_div_16bit_edge:success/no_failure | exact=0, guarded=4, unresolved=8 | - |
| edge_detect | success | fallback/fallback | test_verified_edge_detect_basic:success/no_failure, test_verified_edge_detect_edge:success/no_failure | exact=7, guarded=0, unresolved=9 | - |
| fixed_point_adder | success | merged/merged | test_fixed_point_adder_basic:success/no_failure, test_fixed_point_adder_edge:success/no_failure | exact=0, guarded=0, unresolved=6 | - |
| fixed_point_subtractor | success | fallback/merged | test_fixed_point_subtractor_basic:success/no_failure, test_fixed_point_subtractor_edge:success/no_failure | exact=0, guarded=0, unresolved=4 | - |
| float_multi | success | fallback/merged | test_float_multi_basic:success/no_failure, test_float_multi_edge:success/no_failure | exact=0, guarded=2, unresolved=10 | - |
| freq_div | success | fallback/merged | test_freq_div_basic:success/no_failure | exact=0, guarded=0, unresolved=0 | - |
| freq_divbyeven | success | merged/merged | test_freq_divbyeven_basic:success/no_failure | exact=0, guarded=0, unresolved=6 | - |
| freq_divbyfrac | success | merged/merged | test_freq_divbyfrac_basic:success/no_failure | exact=0, guarded=0, unresolved=7 | - |
| freq_divbyodd | success | fallback/merged | test_freq_divbyodd_basic:success/no_failure | exact=0, guarded=0, unresolved=3 | - |
| fsm | success | fallback/merged | test_verified_fsm_basic:success/no_failure, test_verified_fsm_edge:success/no_failure | exact=10, guarded=0, unresolved=1 | - |
| instr_reg | success | fallback/merged | test_instr_reg_basic:success/no_failure, test_instr_reg_edge:success/no_failure | exact=0, guarded=6, unresolved=30 | - |
| multi_16bit | failed | fallback/fallback | test_verified_multi_16bit_basic:runtime_error/runtime_test_failure, test_verified_multi_16bit_protocol:runtime_error/runtime_test_failure, test_verified_multi_16bit_edge:runtime_error/runtime_test_failure | exact=1, guarded=30, unresolved=10 | module_failures=test_verified_multi_16bit_basic:runtime_error/runtime_test_failure, test_verified_multi_16bit_protocol:runtime_error/runtime_test_failure, test_verified_multi_16bit_edge:runtime_error/runtime_test_failure |
| multi_8bit | success | merged/merged | test_multi_8bit_basic:success/no_failure, test_multi_8bit_edge:success/no_failure | exact=3, guarded=0, unresolved=2 | - |
| multi_booth_8bit | failed | merged/merged | test_verified_multi_booth_8bit_basic:runtime_error/runtime_test_failure, test_verified_multi_booth_8bit_edge:runtime_error/runtime_test_failure | exact=16, guarded=5, unresolved=15 | module_failures=test_verified_multi_booth_8bit_basic:runtime_error/runtime_test_failure, test_verified_multi_booth_8bit_edge:runtime_error/runtime_test_failure |
| multi_pipe_4bit | success | merged/merged | test_verified_multi_pipe_basic:success/no_failure, test_verified_multi_pipe_edge:success/no_failure | exact=11, guarded=0, unresolved=0 | - |
| multi_pipe_8bit | success | fallback/merged | test_verified_multi_pipe_8bit_basic:success/no_failure, test_verified_multi_pipe_8bit_edge:success/no_failure | exact=11, guarded=0, unresolved=17 | - |
| parallel2serial | success | fallback/merged | test_verified_parallel2serial_basic:success/no_failure, test_verified_parallel2serial_edge:success/no_failure | exact=0, guarded=0, unresolved=0 | - |
| pe | success | fallback/merged | test_verified_pe_basic:success/no_failure, test_verified_pe_edge:success/no_failure | exact=6, guarded=0, unresolved=6 | - |
| pulse_detect | success | merged/merged | test_verified_pulse_detect_basic:success/no_failure, test_verified_pulse_detect_edge:success/no_failure | exact=0, guarded=0, unresolved=11 | - |
| radix2_div | success | fallback/merged | test_verified_radix2_div_basic:success/no_failure, test_verified_radix2_div_protocol:success/no_failure, test_verified_radix2_div_edge:success/no_failure | exact=0, guarded=19, unresolved=11 | - |
| right_shifter | success | fallback/merged | test_verified_right_shifter_basic:success/no_failure, test_verified_right_shifter_edge:success/no_failure | exact=0, guarded=2, unresolved=8 | - |
| ring_counter | success | merged/merged | test_ring_counter_basic:success/no_failure | exact=0, guarded=0, unresolved=9 | - |
| sequence_detector | success | merged/merged | test_sequence_detector_basic:success/no_failure, test_sequence_detector_edge:success/no_failure | exact=9, guarded=0, unresolved=1 | - |
| serial2parallel | partial_success | fallback/fallback | test_verified_serial2parallel_basic:success/no_failure, test_verified_serial2parallel_edge:runtime_error/runtime_test_failure | exact=0, guarded=0, unresolved=11 | module_failures=test_verified_serial2parallel_edge:runtime_error/runtime_test_failure |
| signal_generator | success | fallback/merged | test_verified_signal_generator_basic:success/no_failure | exact=0, guarded=0, unresolved=6 | - |
| square_wave | success | fallback/merged | test_square_wave_basic:success/no_failure, test_square_wave_edge:success/no_failure | exact=0, guarded=0, unresolved=8 | - |
| sub_64bit | success | fallback/merged | test_sub_64bit_basic:success/no_failure, test_sub_64bit_edge:success/no_failure | exact=0, guarded=0, unresolved=3 | - |
| synchronizer | success | merged/merged | test_verified_synchronizer_basic:success/no_failure, test_verified_synchronizer_edge:success/no_failure | exact=1, guarded=0, unresolved=4 | - |
| traffic_light | partial_success | merged/merged | test_verified_traffic_light_basic:runtime_error/runtime_test_failure, test_verified_traffic_light_edge:success/no_failure | exact=0, guarded=2, unresolved=41 | module_failures=test_verified_traffic_light_basic:runtime_error/runtime_test_failure |
| up_down_counter | success | merged/merged | test_up_down_counter_basic:success/no_failure, test_up_down_counter_edge:success/no_failure | exact=0, guarded=2, unresolved=10 | - |
| width_8to16 | success | merged/merged | test_verified_width_8to16_basic:success/no_failure, test_verified_width_8to16_edge:success/no_failure | exact=11, guarded=0, unresolved=5 | - |
