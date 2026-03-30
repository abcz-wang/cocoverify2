# RTLLM Batch Summary

- Benchmark root: `/workspace/I/qimeng6/wangchuanhao/QiMeng-Agent/VerilogBenchmark/Benchmarks/RTLLM_for_ivl`
- Output dir: `/workspace/I/qimeng6/wangchuanhao/cocoverify2/tmp/rtllm_batch_full_20260330`
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
- Tasks with all rendered modules successful: 49
- False positive count on verified RTL: 0
- Tasks with guarded/unresolved policies: 44
- LLM plan attempted/succeeded/fallback: 50/0/50
- LLM oracle attempted/succeeded/fallback: 50/0/50

## Histograms

- Triage: `{"insufficient_stimulus": 1, "no_failure": 87}`
- Assertion strength: `{"exact": 78, "guarded": 54, "unresolved": 294}`
- LLM plan status: `{"fallback": 50}`
- LLM oracle status: `{"fallback": 50}`

## Per-Task Rollup

| Task | Status | LLM(plan/oracle) | Modules | Assertion Strengths | Failure Summary |
| --- | --- | --- | --- | --- | --- |
| JC_counter | success | fallback/fallback | test_verified_JC_counter_basic:success/no_failure | exact=3, guarded=0, unresolved=2 | - |
| LFSR | success | fallback/fallback | test_LFSR_basic:success/no_failure | exact=0, guarded=0, unresolved=5 | - |
| LIFObuffer | success | fallback/fallback | test_LIFObuffer_basic:success/no_failure, test_LIFObuffer_edge:success/no_failure | exact=7, guarded=0, unresolved=18 | - |
| RAM | success | fallback/fallback | test_verified_RAM_basic:success/no_failure, test_verified_RAM_edge:success/no_failure | exact=2, guarded=0, unresolved=4 | - |
| ROM | success | fallback/fallback | test_ROM_basic:success/no_failure, test_ROM_edge:success/no_failure | exact=0, guarded=0, unresolved=2 | - |
| accu | success | fallback/fallback | test_accu_basic:success/no_failure, test_accu_edge:success/no_failure | exact=1, guarded=0, unresolved=4 | - |
| adder_16bit | success | fallback/fallback | test_verified_adder_16bit_basic:success/no_failure, test_verified_adder_16bit_edge:success/no_failure | exact=0, guarded=1, unresolved=7 | - |
| adder_32bit | success | fallback/fallback | test_verified_adder_32bit_basic:success/no_failure | exact=0, guarded=0, unresolved=4 | - |
| adder_8bit | success | fallback/fallback | test_verified_adder_8bit_basic:success/no_failure, test_verified_adder_8bit_edge:success/no_failure | exact=0, guarded=1, unresolved=7 | - |
| adder_bcd | success | fallback/fallback | test_adder_bcd_basic:success/no_failure, test_adder_bcd_edge:success/no_failure | exact=0, guarded=1, unresolved=7 | - |
| adder_pipe_64bit | success | fallback/fallback | test_verified_adder_64bit_basic:success/no_failure, test_verified_adder_64bit_edge:success/no_failure | exact=0, guarded=0, unresolved=18 | - |
| alu | success | fallback/fallback | test_verified_alu_basic:success/no_failure, test_verified_alu_edge:success/no_failure | exact=0, guarded=9, unresolved=14 | - |
| asyn_fifo | success | fallback/fallback | test_dual_port_RAM_basic:success/no_failure, test_dual_port_RAM_edge:success/no_failure | exact=0, guarded=0, unresolved=3 | - |
| barrel_shifter | success | fallback/fallback | test_barrel_shifter_basic:success/no_failure | exact=0, guarded=0, unresolved=1 | - |
| calendar | success | fallback/fallback | test_verified_calendar_basic:success/no_failure | exact=0, guarded=0, unresolved=9 | - |
| clkgenerator | failed | fallback/fallback | test_clkgenerator_basic:success/insufficient_stimulus | exact=0, guarded=0, unresolved=1 | module_failures=test_clkgenerator_basic:success/insufficient_stimulus |
| comparator_3bit | success | fallback/fallback | test_comparator_3bit_basic:success/no_failure, test_comparator_3bit_edge:success/no_failure | exact=12, guarded=0, unresolved=0 | - |
| comparator_4bit | success | fallback/fallback | test_comparator_4bit_basic:success/no_failure, test_comparator_4bit_edge:success/no_failure | exact=0, guarded=0, unresolved=12 | - |
| counter_12 | success | fallback/fallback | test_verified_counter_12_basic:success/no_failure, test_verified_counter_12_edge:success/no_failure | exact=0, guarded=0, unresolved=9 | - |
| div_16bit | success | fallback/fallback | test_verified_div_16bit_basic:success/no_failure, test_verified_div_16bit_edge:success/no_failure | exact=0, guarded=2, unresolved=6 | - |
| edge_detect | success | fallback/fallback | test_verified_edge_detect_basic:success/no_failure, test_verified_edge_detect_edge:success/no_failure | exact=7, guarded=0, unresolved=9 | - |
| fixed_point_adder | success | fallback/fallback | test_fixed_point_adder_basic:success/no_failure, test_fixed_point_adder_edge:success/no_failure | exact=0, guarded=0, unresolved=4 | - |
| fixed_point_subtractor | success | fallback/fallback | test_fixed_point_subtractor_basic:success/no_failure, test_fixed_point_subtractor_edge:success/no_failure | exact=0, guarded=0, unresolved=4 | - |
| float_multi | success | fallback/fallback | test_float_multi_basic:success/no_failure, test_float_multi_edge:success/no_failure | exact=0, guarded=2, unresolved=7 | - |
| freq_div | success | fallback/fallback | test_freq_div_basic:success/no_failure | exact=0, guarded=0, unresolved=0 | - |
| freq_divbyeven | success | fallback/fallback | test_freq_divbyeven_basic:success/no_failure | exact=0, guarded=0, unresolved=3 | - |
| freq_divbyfrac | success | fallback/fallback | test_freq_divbyfrac_basic:success/no_failure | exact=0, guarded=0, unresolved=3 | - |
| freq_divbyodd | success | fallback/fallback | test_freq_divbyodd_basic:success/no_failure | exact=0, guarded=0, unresolved=3 | - |
| fsm | success | fallback/fallback | test_verified_fsm_basic:success/no_failure, test_verified_fsm_edge:success/no_failure | exact=9, guarded=0, unresolved=0 | - |
| instr_reg | success | fallback/fallback | test_instr_reg_basic:success/no_failure, test_instr_reg_edge:success/no_failure | exact=0, guarded=6, unresolved=21 | - |
| multi_16bit | success | fallback/fallback | test_verified_multi_16bit_basic:success/no_failure, test_verified_multi_16bit_protocol:success/no_failure, test_verified_multi_16bit_edge:success/no_failure | exact=3, guarded=9, unresolved=5 | - |
| multi_8bit | success | fallback/fallback | test_multi_8bit_basic:success/no_failure, test_multi_8bit_edge:success/no_failure | exact=0, guarded=0, unresolved=2 | - |
| multi_booth_8bit | success | fallback/fallback | test_verified_multi_booth_8bit_basic:success/no_failure, test_verified_multi_booth_8bit_edge:success/no_failure | exact=9, guarded=2, unresolved=7 | - |
| multi_pipe_4bit | success | fallback/fallback | test_verified_multi_pipe_basic:success/no_failure, test_verified_multi_pipe_edge:success/no_failure | exact=9, guarded=0, unresolved=0 | - |
| multi_pipe_8bit | success | fallback/fallback | test_verified_multi_pipe_8bit_basic:success/no_failure, test_verified_multi_pipe_8bit_edge:success/no_failure | exact=9, guarded=0, unresolved=9 | - |
| parallel2serial | success | fallback/fallback | test_verified_parallel2serial_basic:success/no_failure, test_verified_parallel2serial_edge:success/no_failure | exact=0, guarded=0, unresolved=0 | - |
| pe | success | fallback/fallback | test_verified_pe_basic:success/no_failure, test_verified_pe_edge:success/no_failure | exact=5, guarded=0, unresolved=4 | - |
| pulse_detect | success | fallback/fallback | test_verified_pulse_detect_basic:success/no_failure, test_verified_pulse_detect_edge:success/no_failure | exact=0, guarded=0, unresolved=9 | - |
| radix2_div | success | fallback/fallback | test_verified_radix2_div_basic:success/no_failure, test_verified_radix2_div_protocol:success/no_failure, test_verified_radix2_div_edge:success/no_failure | exact=0, guarded=19, unresolved=11 | - |
| right_shifter | success | fallback/fallback | test_verified_right_shifter_basic:success/no_failure, test_verified_right_shifter_edge:success/no_failure | exact=0, guarded=2, unresolved=4 | - |
| ring_counter | success | fallback/fallback | test_ring_counter_basic:success/no_failure | exact=0, guarded=0, unresolved=5 | - |
| sequence_detector | success | fallback/fallback | test_sequence_detector_basic:success/no_failure | exact=0, guarded=0, unresolved=0 | - |
| serial2parallel | success | fallback/fallback | test_verified_serial2parallel_basic:success/no_failure, test_verified_serial2parallel_edge:success/no_failure | exact=0, guarded=0, unresolved=5 | - |
| signal_generator | success | fallback/fallback | test_verified_signal_generator_basic:success/no_failure | exact=0, guarded=0, unresolved=5 | - |
| square_wave | success | fallback/fallback | test_square_wave_basic:success/no_failure, test_square_wave_edge:success/no_failure | exact=0, guarded=0, unresolved=6 | - |
| sub_64bit | success | fallback/fallback | test_sub_64bit_basic:success/no_failure, test_sub_64bit_edge:success/no_failure | exact=0, guarded=0, unresolved=2 | - |
| synchronizer | success | fallback/fallback | test_verified_synchronizer_basic:success/no_failure, test_verified_synchronizer_edge:success/no_failure | exact=1, guarded=0, unresolved=4 | - |
| traffic_light | success | fallback/fallback | test_verified_traffic_light_basic:success/no_failure, test_verified_traffic_light_edge:success/no_failure | exact=0, guarded=0, unresolved=20 | - |
| up_down_counter | success | fallback/fallback | test_up_down_counter_basic:success/no_failure | exact=0, guarded=0, unresolved=5 | - |
| width_8to16 | success | fallback/fallback | test_verified_width_8to16_basic:success/no_failure, test_verified_width_8to16_edge:success/no_failure | exact=1, guarded=0, unresolved=4 | - |
