# RTLLM Batch Summary

- Benchmark root: `/workspace/I/qimeng6/wangchuanhao/QiMeng-Agent/VerilogBenchmark/Benchmarks/RTLLM_for_ivl`
- Output dir: `/workspace/I/qimeng6/wangchuanhao/cocoverify2/tmp/rtllm_batch_round3_full`
- Pipeline: `contract -> plan(hybrid) -> oracle(hybrid) -> render -> run -> triage`
- Experimental fill used: `False`

## Aggregate Metrics

- Discovered tasks: 50
- Valid contract: 50
- Valid plan: 50
- Valid oracle: 50
- Valid render: 50
- Tasks with >=1 successful run: 46
- Tasks with all rendered modules successful: 31
- False positive count on verified RTL: 18
- Tasks with guarded/unresolved policies: 45

## Histograms

- Triage: `{"insufficient_stimulus": 1, "no_failure": 65, "runtime_test_failure": 21}`
- Assertion strength: `{"exact": 0, "guarded": 102, "unresolved": 348}`

## Per-Task Rollup

| Task | Status | Modules | Assertion Strengths | Failure Summary |
| --- | --- | --- | --- | --- |
| JC_counter | success | test_verified_JC_counter_basic:success/no_failure | exact=0, guarded=0, unresolved=5 | - |
| LFSR | success | test_LFSR_basic:success/no_failure | exact=0, guarded=0, unresolved=5 | - |
| LIFObuffer | failed | test_LIFObuffer_basic:runtime_error/runtime_test_failure, test_LIFObuffer_edge:runtime_error/runtime_test_failure | exact=0, guarded=4, unresolved=23 | module_failures=test_LIFObuffer_basic:runtime_error/runtime_test_failure, test_LIFObuffer_edge:runtime_error/runtime_test_failure |
| RAM | success | test_verified_RAM_basic:success/no_failure, test_verified_RAM_edge:success/no_failure | exact=0, guarded=4, unresolved=5 | - |
| ROM | partial_success | test_ROM_basic:success/no_failure, test_ROM_edge:runtime_error/runtime_test_failure | exact=0, guarded=1, unresolved=1 | module_failures=test_ROM_edge:runtime_error/runtime_test_failure |
| accu | partial_success | test_accu_basic:success/no_failure, test_accu_edge:runtime_error/runtime_test_failure | exact=0, guarded=2, unresolved=8 | module_failures=test_accu_edge:runtime_error/runtime_test_failure |
| adder_16bit | partial_success | test_verified_adder_16bit_basic:success/no_failure, test_verified_adder_16bit_edge:runtime_error/runtime_test_failure | exact=0, guarded=2, unresolved=6 | module_failures=test_verified_adder_16bit_edge:runtime_error/runtime_test_failure |
| adder_32bit | success | test_verified_adder_32bit_basic:success/no_failure | exact=0, guarded=0, unresolved=4 | - |
| adder_8bit | partial_success | test_verified_adder_8bit_basic:success/no_failure, test_verified_adder_8bit_edge:runtime_error/runtime_test_failure | exact=0, guarded=2, unresolved=6 | module_failures=test_verified_adder_8bit_edge:runtime_error/runtime_test_failure |
| adder_bcd | partial_success | test_adder_bcd_basic:success/no_failure, test_adder_bcd_edge:runtime_error/runtime_test_failure | exact=0, guarded=2, unresolved=6 | module_failures=test_adder_bcd_edge:runtime_error/runtime_test_failure |
| adder_pipe_64bit | success | test_verified_adder_64bit_basic:success/no_failure, test_verified_adder_64bit_edge:success/no_failure | exact=0, guarded=0, unresolved=18 | - |
| alu | partial_success | test_verified_alu_basic:success/no_failure, test_verified_alu_edge:runtime_error/runtime_test_failure | exact=0, guarded=2, unresolved=22 | module_failures=test_verified_alu_edge:runtime_error/runtime_test_failure |
| asyn_fifo | success | test_dual_port_RAM_basic:success/no_failure, test_dual_port_RAM_edge:success/no_failure | exact=0, guarded=0, unresolved=3 | - |
| barrel_shifter | success | test_barrel_shifter_basic:success/no_failure | exact=0, guarded=0, unresolved=1 | - |
| calendar | success | test_verified_calendar_basic:success/no_failure | exact=0, guarded=0, unresolved=9 | - |
| clkgenerator | failed | test_clkgenerator_basic:success/insufficient_stimulus | exact=0, guarded=0, unresolved=0 | module_failures=test_clkgenerator_basic:success/insufficient_stimulus |
| comparator_3bit | success | test_comparator_3bit_basic:success/no_failure, test_comparator_3bit_edge:success/no_failure | exact=0, guarded=0, unresolved=12 | - |
| comparator_4bit | success | test_comparator_4bit_basic:success/no_failure, test_comparator_4bit_edge:success/no_failure | exact=0, guarded=0, unresolved=12 | - |
| counter_12 | partial_success | test_verified_counter_12_basic:success/no_failure, test_verified_counter_12_edge:runtime_error/runtime_test_failure | exact=0, guarded=4, unresolved=5 | module_failures=test_verified_counter_12_edge:runtime_error/runtime_test_failure |
| div_16bit | success | test_verified_div_16bit_basic:success/no_failure, test_verified_div_16bit_edge:success/no_failure | exact=0, guarded=4, unresolved=4 | - |
| edge_detect | success | test_verified_edge_detect_basic:success/no_failure, test_verified_edge_detect_edge:success/no_failure | exact=0, guarded=0, unresolved=18 | - |
| fixed_point_adder | success | test_fixed_point_adder_basic:success/no_failure, test_fixed_point_adder_edge:success/no_failure | exact=0, guarded=0, unresolved=4 | - |
| fixed_point_subtractor | success | test_fixed_point_subtractor_basic:success/no_failure, test_fixed_point_subtractor_edge:success/no_failure | exact=0, guarded=0, unresolved=4 | - |
| float_multi | partial_success | test_float_multi_basic:success/no_failure, test_float_multi_edge:runtime_error/runtime_test_failure | exact=0, guarded=4, unresolved=5 | module_failures=test_float_multi_edge:runtime_error/runtime_test_failure |
| freq_div | success | test_freq_div_basic:success/no_failure | exact=0, guarded=0, unresolved=0 | - |
| freq_divbyeven | success | test_freq_divbyeven_basic:success/no_failure | exact=0, guarded=0, unresolved=0 | - |
| freq_divbyfrac | success | test_freq_divbyfrac_basic:success/no_failure | exact=0, guarded=0, unresolved=0 | - |
| freq_divbyodd | success | test_freq_divbyodd_basic:success/no_failure | exact=0, guarded=0, unresolved=0 | - |
| fsm | success | test_verified_fsm_basic:success/no_failure, test_verified_fsm_edge:success/no_failure | exact=0, guarded=0, unresolved=9 | - |
| instr_reg | partial_success | test_instr_reg_basic:success/no_failure, test_instr_reg_edge:runtime_error/runtime_test_failure | exact=0, guarded=12, unresolved=15 | module_failures=test_instr_reg_edge:runtime_error/runtime_test_failure |
| multi_16bit | partial_success | test_verified_multi_16bit_basic:success/no_failure, test_verified_multi_16bit_protocol:runtime_error/runtime_test_failure, test_verified_multi_16bit_edge:runtime_error/runtime_test_failure | exact=0, guarded=14, unresolved=3 | module_failures=test_verified_multi_16bit_protocol:runtime_error/runtime_test_failure, test_verified_multi_16bit_edge:runtime_error/runtime_test_failure |
| multi_8bit | success | test_multi_8bit_basic:success/no_failure, test_multi_8bit_edge:success/no_failure | exact=0, guarded=1, unresolved=1 | - |
| multi_booth_8bit | partial_success | test_verified_multi_booth_8bit_basic:success/no_failure, test_verified_multi_booth_8bit_edge:runtime_error/runtime_test_failure | exact=0, guarded=4, unresolved=14 | module_failures=test_verified_multi_booth_8bit_edge:runtime_error/runtime_test_failure |
| multi_pipe_4bit | success | test_verified_multi_pipe_basic:success/no_failure, test_verified_multi_pipe_edge:success/no_failure | exact=0, guarded=0, unresolved=9 | - |
| multi_pipe_8bit | success | test_verified_multi_pipe_8bit_basic:success/no_failure, test_verified_multi_pipe_8bit_edge:success/no_failure | exact=0, guarded=0, unresolved=18 | - |
| parallel2serial | success | test_verified_parallel2serial_basic:success/no_failure, test_verified_parallel2serial_edge:success/no_failure | exact=0, guarded=0, unresolved=10 | - |
| pe | failed | test_verified_pe_basic:runtime_error/runtime_test_failure, test_verified_pe_edge:runtime_error/runtime_test_failure | exact=0, guarded=4, unresolved=5 | module_failures=test_verified_pe_basic:runtime_error/runtime_test_failure, test_verified_pe_edge:runtime_error/runtime_test_failure |
| pulse_detect | success | test_verified_pulse_detect_basic:success/no_failure, test_verified_pulse_detect_edge:success/no_failure | exact=0, guarded=0, unresolved=9 | - |
| radix2_div | partial_success | test_verified_radix2_div_basic:success/no_failure, test_verified_radix2_div_protocol:success/no_failure, test_verified_radix2_div_edge:runtime_error/runtime_test_failure | exact=0, guarded=23, unresolved=7 | module_failures=test_verified_radix2_div_edge:runtime_error/runtime_test_failure |
| right_shifter | success | test_verified_right_shifter_basic:success/no_failure, test_verified_right_shifter_edge:success/no_failure | exact=0, guarded=4, unresolved=2 | - |
| ring_counter | success | test_ring_counter_basic:success/no_failure | exact=0, guarded=0, unresolved=5 | - |
| sequence_detector | success | test_sequence_detector_basic:success/no_failure | exact=0, guarded=0, unresolved=3 | - |
| serial2parallel | partial_success | test_verified_serial2parallel_basic:success/no_failure, test_verified_serial2parallel_edge:runtime_error/runtime_test_failure | exact=0, guarded=2, unresolved=8 | module_failures=test_verified_serial2parallel_edge:runtime_error/runtime_test_failure |
| signal_generator | success | test_verified_signal_generator_basic:success/no_failure | exact=0, guarded=0, unresolved=5 | - |
| square_wave | failed | test_square_wave_basic:runtime_error/runtime_test_failure | exact=0, guarded=0, unresolved=2 | module_failures=test_square_wave_basic:runtime_error/runtime_test_failure |
| sub_64bit | success | test_sub_64bit_basic:success/no_failure, test_sub_64bit_edge:success/no_failure | exact=0, guarded=1, unresolved=3 | - |
| synchronizer | success | test_verified_synchronizer_basic:success/no_failure, test_verified_synchronizer_edge:success/no_failure | exact=0, guarded=2, unresolved=3 | - |
| traffic_light | partial_success | test_verified_traffic_light_basic:success/no_failure, test_verified_traffic_light_edge:runtime_error/runtime_test_failure | exact=0, guarded=2, unresolved=18 | module_failures=test_verified_traffic_light_edge:runtime_error/runtime_test_failure |
| up_down_counter | success | test_up_down_counter_basic:success/no_failure | exact=0, guarded=0, unresolved=5 | - |
| width_8to16 | partial_success | test_verified_width_8to16_basic:success/no_failure, test_verified_width_8to16_edge:runtime_error/runtime_test_failure | exact=0, guarded=2, unresolved=8 | module_failures=test_verified_width_8to16_edge:runtime_error/runtime_test_failure |
