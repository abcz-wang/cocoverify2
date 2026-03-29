# RTLLM Batch Summary

- Benchmark root: `/workspace/I/qimeng6/wangchuanhao/QiMeng-Agent/VerilogBenchmark/Benchmarks/RTLLM_for_ivl`
- Output dir: `/workspace/I/qimeng6/wangchuanhao/cocoverify2/tmp/rtllm_batch_round6_definedness`
- Pipeline: `contract -> plan(hybrid) -> oracle(hybrid) -> render -> run -> triage`
- Experimental fill used: `False`
- LLM runtime policy: `provider=openai, model=oss, trust_env=False, disable_proxies=True`

## Aggregate Metrics

- Discovered tasks: 50
- Valid contract: 50
- Valid plan: 50
- Valid oracle: 50
- Valid render: 50
- Tasks with >=1 successful run: 49
- Tasks with all rendered modules successful: 46
- False positive count on verified RTL: 1
- Tasks with guarded/unresolved policies: 45
- LLM plan attempted/succeeded/fallback: 50/50/0
- LLM oracle attempted/succeeded/fallback: 50/50/0

## Histograms

- Triage: `{"insufficient_stimulus": 4, "no_failure": 103, "runtime_test_failure": 1}`
- Assertion strength: `{"exact": 184, "guarded": 80, "unresolved": 584}`
- LLM plan status: `{"merged": 50}`
- LLM oracle status: `{"merged": 50}`

## Per-Task Rollup

| Task | Status | LLM(plan/oracle) | Modules | Assertion Strengths | Failure Summary |
| --- | --- | --- | --- | --- | --- |
| JC_counter | success | merged/merged | test_verified_JC_counter_basic:success/no_failure, test_verified_JC_counter_edge:success/no_failure | exact=5, guarded=0, unresolved=4 | - |
| LFSR | success | merged/merged | test_LFSR_basic:success/no_failure, test_LFSR_edge:success/no_failure | exact=0, guarded=1, unresolved=10 | - |
| LIFObuffer | success | merged/merged | test_LIFObuffer_basic:success/no_failure, test_LIFObuffer_edge:success/no_failure | exact=8, guarded=0, unresolved=26 | - |
| RAM | success | merged/merged | test_verified_RAM_basic:success/no_failure, test_verified_RAM_edge:success/no_failure | exact=2, guarded=0, unresolved=7 | - |
| ROM | success | merged/merged | test_ROM_basic:success/no_failure, test_ROM_edge:success/no_failure | exact=0, guarded=1, unresolved=6 | - |
| accu | success | merged/merged | test_accu_basic:success/no_failure, test_accu_protocol:success/no_failure, test_accu_edge:success/no_failure | exact=13, guarded=0, unresolved=8 | - |
| adder_16bit | success | merged/merged | test_verified_adder_16bit_basic:success/no_failure, test_verified_adder_16bit_edge:success/no_failure | exact=0, guarded=1, unresolved=15 | - |
| adder_32bit | partial_success | merged/merged | test_verified_adder_32bit_basic:success/no_failure, test_verified_adder_32bit_edge:success/insufficient_stimulus | exact=0, guarded=1, unresolved=15 | module_failures=test_verified_adder_32bit_edge:success/insufficient_stimulus |
| adder_8bit | success | merged/merged | test_verified_adder_8bit_basic:success/no_failure, test_verified_adder_8bit_edge:success/no_failure | exact=0, guarded=1, unresolved=14 | - |
| adder_bcd | success | merged/merged | test_adder_bcd_basic:success/no_failure, test_adder_bcd_edge:success/no_failure | exact=0, guarded=2, unresolved=20 | - |
| adder_pipe_64bit | success | merged/merged | test_verified_adder_64bit_basic:success/no_failure, test_verified_adder_64bit_protocol:success/no_failure, test_verified_adder_64bit_edge:success/no_failure | exact=0, guarded=0, unresolved=26 | - |
| alu | success | merged/merged | test_verified_alu_basic:success/no_failure, test_verified_alu_edge:success/no_failure | exact=0, guarded=14, unresolved=33 | - |
| asyn_fifo | success | merged/merged | test_dual_port_RAM_basic:success/no_failure, test_dual_port_RAM_protocol:success/no_failure, test_dual_port_RAM_edge:success/no_failure | exact=0, guarded=0, unresolved=6 | - |
| barrel_shifter | partial_success | merged/merged | test_barrel_shifter_basic:success/no_failure, test_barrel_shifter_edge:success/insufficient_stimulus | exact=0, guarded=0, unresolved=4 | module_failures=test_barrel_shifter_edge:success/insufficient_stimulus |
| calendar | success | merged/merged | test_verified_calendar_basic:success/no_failure, test_verified_calendar_edge:success/no_failure | exact=0, guarded=0, unresolved=18 | - |
| clkgenerator | failed | merged/merged | test_clkgenerator_basic:success/insufficient_stimulus, test_clkgenerator_edge:success/insufficient_stimulus | exact=0, guarded=0, unresolved=4 | module_failures=test_clkgenerator_basic:success/insufficient_stimulus, test_clkgenerator_edge:success/insufficient_stimulus |
| comparator_3bit | success | merged/merged | test_comparator_3bit_basic:success/no_failure, test_comparator_3bit_edge:success/no_failure | exact=21, guarded=0, unresolved=0 | - |
| comparator_4bit | success | merged/merged | test_comparator_4bit_basic:success/no_failure, test_comparator_4bit_edge:success/no_failure | exact=0, guarded=0, unresolved=21 | - |
| counter_12 | success | merged/merged | test_verified_counter_12_basic:success/no_failure, test_verified_counter_12_edge:success/no_failure | exact=0, guarded=0, unresolved=14 | - |
| div_16bit | success | merged/merged | test_verified_div_16bit_basic:success/no_failure, test_verified_div_16bit_edge:success/no_failure | exact=0, guarded=2, unresolved=14 | - |
| edge_detect | success | merged/merged | test_verified_edge_detect_basic:success/no_failure, test_verified_edge_detect_edge:success/no_failure | exact=11, guarded=0, unresolved=14 | - |
| fixed_point_adder | success | merged/merged | test_fixed_point_adder_basic:success/no_failure, test_fixed_point_adder_edge:success/no_failure | exact=0, guarded=0, unresolved=9 | - |
| fixed_point_subtractor | success | merged/merged | test_fixed_point_subtractor_basic:success/no_failure, test_fixed_point_subtractor_edge:success/no_failure | exact=0, guarded=0, unresolved=10 | - |
| float_multi | success | merged/merged | test_float_multi_basic:success/no_failure, test_float_multi_edge:success/no_failure | exact=0, guarded=2, unresolved=11 | - |
| freq_div | success | merged/merged | test_freq_div_basic:success/no_failure, test_freq_div_edge:success/no_failure | exact=0, guarded=0, unresolved=0 | - |
| freq_divbyeven | success | merged/merged | test_freq_divbyeven_basic:success/no_failure, test_freq_divbyeven_edge:success/no_failure | exact=0, guarded=0, unresolved=12 | - |
| freq_divbyfrac | success | merged/merged | test_freq_divbyfrac_basic:success/no_failure, test_freq_divbyfrac_edge:success/no_failure | exact=0, guarded=0, unresolved=10 | - |
| freq_divbyodd | success | merged/merged | test_freq_divbyodd_basic:success/no_failure, test_freq_divbyodd_edge:success/no_failure | exact=0, guarded=0, unresolved=12 | - |
| fsm | success | merged/merged | test_verified_fsm_basic:success/no_failure, test_verified_fsm_edge:success/no_failure | exact=12, guarded=0, unresolved=1 | - |
| instr_reg | success | merged/merged | test_instr_reg_basic:success/no_failure, test_instr_reg_edge:success/no_failure | exact=0, guarded=9, unresolved=36 | - |
| multi_16bit | success | merged/merged | test_verified_multi_16bit_basic:success/no_failure, test_verified_multi_16bit_protocol:success/no_failure, test_verified_multi_16bit_edge:success/no_failure | exact=8, guarded=15, unresolved=9 | - |
| multi_8bit | success | merged/merged | test_multi_8bit_basic:success/no_failure, test_multi_8bit_edge:success/no_failure | exact=1, guarded=0, unresolved=4 | - |
| multi_booth_8bit | success | merged/merged | test_verified_multi_booth_8bit_basic:success/no_failure, test_verified_multi_booth_8bit_protocol:success/no_failure, test_verified_multi_booth_8bit_edge:success/no_failure | exact=12, guarded=2, unresolved=12 | - |
| multi_pipe_4bit | success | merged/merged | test_verified_multi_pipe_basic:success/no_failure, test_verified_multi_pipe_edge:success/no_failure | exact=12, guarded=0, unresolved=0 | - |
| multi_pipe_8bit | success | merged/merged | test_verified_multi_pipe_8bit_basic:success/no_failure, test_verified_multi_pipe_8bit_protocol:success/no_failure, test_verified_multi_pipe_8bit_edge:success/no_failure | exact=11, guarded=0, unresolved=18 | - |
| parallel2serial | partial_success | merged/merged | test_verified_parallel2serial_basic:runtime_error/runtime_test_failure, test_verified_parallel2serial_edge:success/no_failure | exact=24, guarded=0, unresolved=0 | module_failures=test_verified_parallel2serial_basic:runtime_error/runtime_test_failure |
| pe | success | merged/merged | test_verified_pe_basic:success/no_failure, test_verified_pe_edge:success/no_failure | exact=8, guarded=0, unresolved=7 | - |
| pulse_detect | success | merged/merged | test_verified_pulse_detect_basic:success/no_failure, test_verified_pulse_detect_edge:success/no_failure | exact=0, guarded=0, unresolved=12 | - |
| radix2_div | success | merged/merged | test_verified_radix2_div_basic:success/no_failure, test_verified_radix2_div_protocol:success/no_failure, test_verified_radix2_div_edge:success/no_failure | exact=0, guarded=23, unresolved=18 | - |
| right_shifter | success | merged/merged | test_verified_right_shifter_basic:success/no_failure, test_verified_right_shifter_edge:success/no_failure | exact=0, guarded=2, unresolved=7 | - |
| ring_counter | success | merged/merged | test_ring_counter_basic:success/no_failure, test_ring_counter_edge:success/no_failure | exact=0, guarded=0, unresolved=9 | - |
| sequence_detector | success | merged/merged | test_sequence_detector_basic:success/no_failure, test_sequence_detector_edge:success/no_failure | exact=11, guarded=0, unresolved=0 | - |
| serial2parallel | success | merged/merged | test_verified_serial2parallel_basic:success/no_failure, test_verified_serial2parallel_edge:success/no_failure | exact=10, guarded=0, unresolved=14 | - |
| signal_generator | success | merged/merged | test_verified_signal_generator_basic:success/no_failure, test_verified_signal_generator_edge:success/no_failure | exact=0, guarded=1, unresolved=8 | - |
| square_wave | success | merged/merged | test_square_wave_basic:success/no_failure, test_square_wave_edge:success/no_failure | exact=0, guarded=0, unresolved=11 | - |
| sub_64bit | success | merged/merged | test_sub_64bit_basic:success/no_failure, test_sub_64bit_edge:success/no_failure | exact=0, guarded=0, unresolved=5 | - |
| synchronizer | success | merged/merged | test_verified_synchronizer_basic:success/no_failure, test_verified_synchronizer_edge:success/no_failure | exact=1, guarded=0, unresolved=7 | - |
| traffic_light | success | merged/merged | test_verified_traffic_light_basic:success/no_failure, test_verified_traffic_light_edge:success/no_failure | exact=0, guarded=1, unresolved=45 | - |
| up_down_counter | success | merged/merged | test_up_down_counter_basic:success/no_failure, test_up_down_counter_edge:success/no_failure | exact=0, guarded=2, unresolved=9 | - |
| width_8to16 | success | merged/merged | test_verified_width_8to16_basic:success/no_failure, test_verified_width_8to16_protocol:success/no_failure, test_verified_width_8to16_edge:success/no_failure | exact=14, guarded=0, unresolved=9 | - |
