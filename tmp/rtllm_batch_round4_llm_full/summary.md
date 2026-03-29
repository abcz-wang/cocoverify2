# RTLLM Batch Summary

- Benchmark root: `/workspace/I/qimeng6/wangchuanhao/QiMeng-Agent/VerilogBenchmark/Benchmarks/RTLLM_for_ivl`
- Output dir: `/workspace/I/qimeng6/wangchuanhao/cocoverify2/tmp/rtllm_batch_round4_llm_full`
- Pipeline: `contract -> plan(hybrid) -> oracle(hybrid) -> render -> run -> triage`
- Experimental fill used: `False`
- LLM runtime policy: `provider=openai, model=oss, trust_env=False, disable_proxies=True`

## Aggregate Metrics

- Discovered tasks: 50
- Valid contract: 50
- Valid plan: 50
- Valid oracle: 50
- Valid render: 50
- Tasks with >=1 successful run: 45
- Tasks with all rendered modules successful: 31
- False positive count on verified RTL: 16
- Tasks with guarded/unresolved policies: 50
- LLM plan attempted/succeeded/fallback: 50/49/1
- LLM oracle attempted/succeeded/fallback: 50/32/18

## Histograms

- Triage: `{"insufficient_stimulus": 4, "no_failure": 85, "runtime_test_failure": 22}`
- Assertion strength: `{"exact": 0, "guarded": 162, "unresolved": 654}`
- LLM plan status: `{"fallback": 1, "merged": 49}`
- LLM oracle status: `{"fallback": 18, "merged": 32}`

## Per-Task Rollup

| Task | Status | LLM(plan/oracle) | Modules | Assertion Strengths | Failure Summary |
| --- | --- | --- | --- | --- | --- |
| JC_counter | success | merged/merged | test_verified_JC_counter_basic:success/no_failure, test_verified_JC_counter_edge:success/no_failure | exact=0, guarded=1, unresolved=9 | - |
| LFSR | success | merged/merged | test_LFSR_basic:success/no_failure, test_LFSR_edge:success/no_failure | exact=0, guarded=2, unresolved=9 | - |
| LIFObuffer | failed | merged/merged | test_LIFObuffer_basic:runtime_error/runtime_test_failure, test_LIFObuffer_edge:runtime_error/runtime_test_failure | exact=0, guarded=6, unresolved=34 | module_failures=test_LIFObuffer_basic:runtime_error/runtime_test_failure, test_LIFObuffer_edge:runtime_error/runtime_test_failure |
| RAM | success | merged/merged | test_verified_RAM_basic:success/no_failure, test_verified_RAM_protocol:success/no_failure, test_verified_RAM_edge:success/no_failure | exact=0, guarded=7, unresolved=8 | - |
| ROM | failed | merged/fallback | test_ROM_basic:runtime_error/runtime_test_failure, test_ROM_edge:runtime_error/runtime_test_failure | exact=0, guarded=3, unresolved=1 | module_failures=test_ROM_basic:runtime_error/runtime_test_failure, test_ROM_edge:runtime_error/runtime_test_failure |
| accu | partial_success | merged/fallback | test_accu_basic:success/no_failure, test_accu_protocol:success/no_failure, test_accu_edge:runtime_error/runtime_test_failure | exact=0, guarded=4, unresolved=22 | module_failures=test_accu_edge:runtime_error/runtime_test_failure |
| adder_16bit | partial_success | merged/merged | test_verified_adder_16bit_basic:success/no_failure, test_verified_adder_16bit_edge:runtime_error/runtime_test_failure | exact=0, guarded=3, unresolved=11 | module_failures=test_verified_adder_16bit_edge:runtime_error/runtime_test_failure |
| adder_32bit | partial_success | merged/merged | test_verified_adder_32bit_basic:success/no_failure, test_verified_adder_32bit_edge:success/insufficient_stimulus | exact=0, guarded=5, unresolved=15 | module_failures=test_verified_adder_32bit_edge:success/insufficient_stimulus |
| adder_8bit | partial_success | merged/fallback | test_verified_adder_8bit_basic:success/no_failure, test_verified_adder_8bit_edge:runtime_error/runtime_test_failure | exact=0, guarded=4, unresolved=10 | module_failures=test_verified_adder_8bit_edge:runtime_error/runtime_test_failure |
| adder_bcd | success | merged/merged | test_adder_bcd_basic:success/no_failure, test_adder_bcd_edge:success/no_failure | exact=0, guarded=1, unresolved=15 | - |
| adder_pipe_64bit | success | merged/fallback | test_verified_adder_64bit_basic:success/no_failure, test_verified_adder_64bit_protocol:success/no_failure, test_verified_adder_64bit_edge:success/no_failure | exact=0, guarded=0, unresolved=22 | - |
| alu | failed | merged/merged | test_verified_alu_basic:runtime_error/runtime_test_failure, test_verified_alu_edge:runtime_error/runtime_test_failure | exact=0, guarded=6, unresolved=42 | module_failures=test_verified_alu_basic:runtime_error/runtime_test_failure, test_verified_alu_edge:runtime_error/runtime_test_failure |
| asyn_fifo | success | merged/fallback | test_dual_port_RAM_basic:success/no_failure, test_dual_port_RAM_protocol:success/no_failure, test_dual_port_RAM_edge:success/no_failure | exact=0, guarded=0, unresolved=6 | - |
| barrel_shifter | partial_success | merged/fallback | test_barrel_shifter_basic:success/no_failure, test_barrel_shifter_edge:success/insufficient_stimulus | exact=0, guarded=0, unresolved=2 | module_failures=test_barrel_shifter_edge:success/insufficient_stimulus |
| calendar | success | merged/fallback | test_verified_calendar_basic:success/no_failure, test_verified_calendar_edge:success/no_failure | exact=0, guarded=0, unresolved=15 | - |
| clkgenerator | failed | merged/merged | test_clkgenerator_basic:success/insufficient_stimulus, test_clkgenerator_edge:success/insufficient_stimulus | exact=0, guarded=0, unresolved=3 | module_failures=test_clkgenerator_basic:success/insufficient_stimulus, test_clkgenerator_edge:success/insufficient_stimulus |
| comparator_3bit | success | merged/merged | test_comparator_3bit_basic:success/no_failure, test_comparator_3bit_edge:success/no_failure | exact=0, guarded=0, unresolved=24 | - |
| comparator_4bit | success | merged/merged | test_comparator_4bit_basic:success/no_failure, test_comparator_4bit_edge:success/no_failure | exact=0, guarded=0, unresolved=27 | - |
| counter_12 | partial_success | merged/fallback | test_verified_counter_12_basic:success/no_failure, test_verified_counter_12_edge:runtime_error/runtime_test_failure | exact=0, guarded=5, unresolved=6 | module_failures=test_verified_counter_12_edge:runtime_error/runtime_test_failure |
| div_16bit | success | merged/fallback | test_verified_div_16bit_basic:success/no_failure, test_verified_div_16bit_edge:success/no_failure | exact=0, guarded=8, unresolved=8 | - |
| edge_detect | success | merged/fallback | test_verified_edge_detect_basic:success/no_failure, test_verified_edge_detect_edge:success/no_failure | exact=0, guarded=0, unresolved=24 | - |
| fixed_point_adder | success | merged/fallback | test_fixed_point_adder_basic:success/no_failure, test_fixed_point_adder_edge:success/no_failure | exact=0, guarded=0, unresolved=7 | - |
| fixed_point_subtractor | success | merged/fallback | test_fixed_point_subtractor_basic:success/no_failure, test_fixed_point_subtractor_edge:success/no_failure | exact=0, guarded=0, unresolved=6 | - |
| float_multi | partial_success | merged/merged | test_float_multi_basic:success/no_failure, test_float_multi_edge:runtime_error/runtime_test_failure | exact=0, guarded=7, unresolved=7 | module_failures=test_float_multi_edge:runtime_error/runtime_test_failure |
| freq_div | success | merged/merged | test_freq_div_basic:success/no_failure, test_freq_div_edge:success/no_failure | exact=0, guarded=0, unresolved=21 | - |
| freq_divbyeven | success | merged/fallback | test_freq_divbyeven_basic:success/no_failure, test_freq_divbyeven_edge:success/no_failure | exact=0, guarded=0, unresolved=4 | - |
| freq_divbyfrac | success | merged/merged | test_freq_divbyfrac_basic:success/no_failure, test_freq_divbyfrac_edge:success/no_failure | exact=0, guarded=0, unresolved=12 | - |
| freq_divbyodd | success | merged/merged | test_freq_divbyodd_basic:success/no_failure, test_freq_divbyodd_edge:success/no_failure | exact=0, guarded=0, unresolved=11 | - |
| fsm | success | merged/merged | test_verified_fsm_basic:success/no_failure, test_verified_fsm_edge:success/no_failure | exact=0, guarded=0, unresolved=18 | - |
| instr_reg | partial_success | merged/merged | test_instr_reg_basic:success/no_failure, test_instr_reg_edge:runtime_error/runtime_test_failure | exact=0, guarded=12, unresolved=21 | module_failures=test_instr_reg_edge:runtime_error/runtime_test_failure |
| multi_16bit | partial_success | merged/merged | test_verified_multi_16bit_basic:success/no_failure, test_verified_multi_16bit_protocol:runtime_error/runtime_test_failure, test_verified_multi_16bit_edge:runtime_error/runtime_test_failure | exact=0, guarded=18, unresolved=7 | module_failures=test_verified_multi_16bit_protocol:runtime_error/runtime_test_failure, test_verified_multi_16bit_edge:runtime_error/runtime_test_failure |
| multi_8bit | success | merged/merged | test_multi_8bit_basic:success/no_failure, test_multi_8bit_edge:success/no_failure | exact=0, guarded=5, unresolved=1 | - |
| multi_booth_8bit | partial_success | merged/merged | test_verified_multi_booth_8bit_basic:success/no_failure, test_verified_multi_booth_8bit_protocol:runtime_error/runtime_test_failure, test_verified_multi_booth_8bit_edge:runtime_error/runtime_test_failure | exact=0, guarded=8, unresolved=22 | module_failures=test_verified_multi_booth_8bit_protocol:runtime_error/runtime_test_failure, test_verified_multi_booth_8bit_edge:runtime_error/runtime_test_failure |
| multi_pipe_4bit | success | merged/fallback | test_verified_multi_pipe_basic:success/no_failure, test_verified_multi_pipe_edge:success/no_failure | exact=0, guarded=0, unresolved=12 | - |
| multi_pipe_8bit | success | merged/fallback | test_verified_multi_pipe_8bit_basic:success/no_failure, test_verified_multi_pipe_8bit_protocol:success/no_failure, test_verified_multi_pipe_8bit_edge:success/no_failure | exact=0, guarded=0, unresolved=22 | - |
| parallel2serial | success | merged/merged | test_verified_parallel2serial_basic:success/no_failure, test_verified_parallel2serial_protocol:success/no_failure, test_verified_parallel2serial_edge:success/no_failure | exact=0, guarded=0, unresolved=16 | - |
| pe | failed | merged/merged | test_verified_pe_basic:runtime_error/runtime_test_failure, test_verified_pe_edge:runtime_error/runtime_test_failure | exact=0, guarded=4, unresolved=7 | module_failures=test_verified_pe_basic:runtime_error/runtime_test_failure, test_verified_pe_edge:runtime_error/runtime_test_failure |
| pulse_detect | success | merged/merged | test_verified_pulse_detect_basic:success/no_failure, test_verified_pulse_detect_edge:success/no_failure | exact=0, guarded=0, unresolved=13 | - |
| radix2_div | partial_success | merged/merged | test_verified_radix2_div_basic:success/no_failure, test_verified_radix2_div_protocol:success/no_failure, test_verified_radix2_div_edge:runtime_error/runtime_test_failure | exact=0, guarded=32, unresolved=12 | module_failures=test_verified_radix2_div_edge:runtime_error/runtime_test_failure |
| right_shifter | success | merged/merged | test_verified_right_shifter_basic:success/no_failure, test_verified_right_shifter_edge:success/no_failure | exact=0, guarded=5, unresolved=5 | - |
| ring_counter | success | merged/fallback | test_ring_counter_basic:success/no_failure, test_ring_counter_edge:success/no_failure | exact=0, guarded=2, unresolved=5 | - |
| sequence_detector | success | merged/merged | test_sequence_detector_basic:success/no_failure, test_sequence_detector_edge:success/no_failure | exact=0, guarded=0, unresolved=11 | - |
| serial2parallel | partial_success | fallback/merged | test_verified_serial2parallel_basic:success/no_failure, test_verified_serial2parallel_edge:runtime_error/runtime_test_failure | exact=0, guarded=2, unresolved=8 | module_failures=test_verified_serial2parallel_edge:runtime_error/runtime_test_failure |
| signal_generator | success | merged/merged | test_verified_signal_generator_basic:success/no_failure, test_verified_signal_generator_edge:success/no_failure | exact=0, guarded=0, unresolved=7 | - |
| square_wave | success | merged/merged | test_square_wave_basic:success/no_failure, test_square_wave_edge:success/no_failure | exact=0, guarded=0, unresolved=10 | - |
| sub_64bit | success | merged/merged | test_sub_64bit_basic:success/no_failure, test_sub_64bit_edge:success/no_failure | exact=0, guarded=1, unresolved=7 | - |
| synchronizer | success | merged/merged | test_verified_synchronizer_basic:success/no_failure, test_verified_synchronizer_protocol:success/no_failure, test_verified_synchronizer_edge:success/no_failure | exact=0, guarded=4, unresolved=5 | - |
| traffic_light | partial_success | merged/merged | test_verified_traffic_light_basic:success/no_failure, test_verified_traffic_light_edge:runtime_error/runtime_test_failure | exact=0, guarded=4, unresolved=46 | module_failures=test_verified_traffic_light_edge:runtime_error/runtime_test_failure |
| up_down_counter | partial_success | merged/fallback | test_up_down_counter_basic:success/no_failure, test_up_down_counter_edge:runtime_error/runtime_test_failure | exact=0, guarded=2, unresolved=5 | module_failures=test_up_down_counter_edge:runtime_error/runtime_test_failure |
| width_8to16 | success | merged/fallback | test_verified_width_8to16_basic:success/no_failure, test_verified_width_8to16_protocol:success/no_failure, test_verified_width_8to16_edge:success/no_failure | exact=0, guarded=1, unresolved=13 | - |
