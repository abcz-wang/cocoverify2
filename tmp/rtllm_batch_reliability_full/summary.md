# RTLLM Batch Summary

- Benchmark root: `/workspace/I/qimeng6/wangchuanhao/QiMeng-Agent/VerilogBenchmark/Benchmarks/RTLLM_for_ivl`
- Output dir: `/workspace/I/qimeng6/wangchuanhao/cocoverify2/tmp/rtllm_batch_reliability_full`
- Pipeline: `contract -> plan(hybrid) -> oracle(hybrid) -> render -> run -> triage`
- Experimental fill used: `False`
- LLM runtime policy: `provider=openai, model=oss, trust_env=False, disable_proxies=True`
- Batch execution policy: `jobs=2, resume=True`

## Aggregate Metrics

- Discovered tasks: 50
- Valid contract: 50
- Valid plan: 50
- Valid oracle: 50
- Valid render: 50
- Tasks with >=1 successful run: 50
- Tasks with all rendered modules successful: 50
- False positive count on verified RTL: 0
- Tasks with guarded/unresolved policies: 45
- LLM plan attempted/succeeded/fallback: 50/32/18
- LLM oracle attempted/succeeded/fallback: 50/50/0
- Resumed tasks: 0

## Histograms

- Triage: `{"no_failure": 102}`
- Assertion strength: `{"exact": 142, "guarded": 61, "unresolved": 471}`
- LLM plan status: `{"fallback": 18, "merged": 32}`
- LLM oracle status: `{"merged": 50}`

## Per-Task Rollup

| Task | Status | LLM(plan/oracle) | Modules | Assertion Strengths | Failure Summary |
| --- | --- | --- | --- | --- | --- |
| JC_counter | success | merged/merged | test_verified_JC_counter_basic:success/no_failure, test_verified_JC_counter_edge:success/no_failure | exact=5, guarded=0, unresolved=4 | - |
| LFSR | success | merged/merged | test_LFSR_basic:success/no_failure, test_LFSR_edge:success/no_failure | exact=0, guarded=0, unresolved=9 | - |
| LIFObuffer | success | fallback/merged | test_LIFObuffer_basic:success/no_failure, test_LIFObuffer_edge:success/no_failure | exact=8, guarded=0, unresolved=22 | - |
| RAM | success | merged/merged | test_verified_RAM_basic:success/no_failure, test_verified_RAM_edge:success/no_failure | exact=2, guarded=0, unresolved=5 | - |
| ROM | success | merged/merged | test_ROM_basic:success/no_failure, test_ROM_edge:success/no_failure | exact=0, guarded=0, unresolved=6 | - |
| accu | success | merged/merged | test_accu_basic:success/no_failure, test_accu_edge:success/no_failure | exact=9, guarded=0, unresolved=9 | - |
| adder_16bit | success | merged/merged | test_verified_adder_16bit_basic:success/no_failure, test_verified_adder_16bit_edge:success/no_failure | exact=0, guarded=1, unresolved=15 | - |
| adder_32bit | success | merged/merged | test_verified_adder_32bit_basic:success/no_failure, test_verified_adder_32bit_edge:success/no_failure | exact=0, guarded=1, unresolved=15 | - |
| adder_8bit | success | merged/merged | test_verified_adder_8bit_basic:success/no_failure, test_verified_adder_8bit_edge:success/no_failure | exact=0, guarded=1, unresolved=13 | - |
| adder_bcd | success | merged/merged | test_adder_bcd_basic:success/no_failure, test_adder_bcd_edge:success/no_failure | exact=0, guarded=0, unresolved=14 | - |
| adder_pipe_64bit | success | merged/merged | test_verified_adder_64bit_basic:success/no_failure, test_verified_adder_64bit_edge:success/no_failure | exact=0, guarded=0, unresolved=25 | - |
| alu | success | fallback/merged | test_verified_alu_basic:success/no_failure, test_verified_alu_edge:success/no_failure | exact=0, guarded=12, unresolved=17 | - |
| asyn_fifo | success | fallback/merged | test_dual_port_RAM_basic:success/no_failure, test_dual_port_RAM_edge:success/no_failure | exact=0, guarded=0, unresolved=5 | - |
| barrel_shifter | success | fallback/merged | test_barrel_shifter_basic:success/no_failure | exact=0, guarded=0, unresolved=2 | - |
| calendar | success | fallback/merged | test_verified_calendar_basic:success/no_failure | exact=0, guarded=0, unresolved=18 | - |
| clkgenerator | success | merged/merged | test_clkgenerator_basic:success/no_failure, test_clkgenerator_edge:success/no_failure | exact=0, guarded=0, unresolved=2 | - |
| comparator_3bit | success | merged/merged | test_comparator_3bit_basic:success/no_failure, test_comparator_3bit_edge:success/no_failure | exact=21, guarded=0, unresolved=0 | - |
| comparator_4bit | success | merged/merged | test_comparator_4bit_basic:success/no_failure, test_comparator_4bit_edge:success/no_failure | exact=0, guarded=0, unresolved=21 | - |
| counter_12 | success | merged/merged | test_verified_counter_12_basic:success/no_failure, test_verified_counter_12_edge:success/no_failure | exact=0, guarded=0, unresolved=12 | - |
| div_16bit | success | merged/merged | test_verified_div_16bit_basic:success/no_failure, test_verified_div_16bit_edge:success/no_failure | exact=0, guarded=2, unresolved=14 | - |
| edge_detect | success | merged/merged | test_verified_edge_detect_basic:success/no_failure, test_verified_edge_detect_edge:success/no_failure | exact=10, guarded=0, unresolved=13 | - |
| fixed_point_adder | success | merged/merged | test_fixed_point_adder_basic:success/no_failure, test_fixed_point_adder_edge:success/no_failure | exact=0, guarded=0, unresolved=7 | - |
| fixed_point_subtractor | success | merged/merged | test_fixed_point_subtractor_basic:success/no_failure, test_fixed_point_subtractor_edge:success/no_failure | exact=0, guarded=0, unresolved=7 | - |
| float_multi | success | merged/merged | test_float_multi_basic:success/no_failure, test_float_multi_edge:success/no_failure | exact=0, guarded=2, unresolved=11 | - |
| freq_div | success | merged/merged | test_freq_div_basic:success/no_failure, test_freq_div_edge:success/no_failure | exact=0, guarded=0, unresolved=0 | - |
| freq_divbyeven | success | merged/merged | test_freq_divbyeven_basic:success/no_failure, test_freq_divbyeven_edge:success/no_failure | exact=0, guarded=0, unresolved=9 | - |
| freq_divbyfrac | success | merged/merged | test_freq_divbyfrac_basic:success/no_failure, test_freq_divbyfrac_edge:success/no_failure | exact=0, guarded=0, unresolved=9 | - |
| freq_divbyodd | success | merged/merged | test_freq_divbyodd_basic:success/no_failure, test_freq_divbyodd_edge:success/no_failure | exact=0, guarded=0, unresolved=9 | - |
| fsm | success | fallback/merged | test_verified_fsm_basic:success/no_failure, test_verified_fsm_edge:success/no_failure | exact=10, guarded=0, unresolved=0 | - |
| instr_reg | success | merged/merged | test_instr_reg_basic:success/no_failure, test_instr_reg_edge:success/no_failure | exact=0, guarded=6, unresolved=30 | - |
| multi_16bit | success | merged/merged | test_verified_multi_16bit_basic:success/no_failure, test_verified_multi_16bit_protocol:success/no_failure, test_verified_multi_16bit_edge:success/no_failure | exact=8, guarded=12, unresolved=7 | - |
| multi_8bit | success | fallback/merged | test_multi_8bit_basic:success/no_failure, test_multi_8bit_edge:success/no_failure | exact=1, guarded=0, unresolved=2 | - |
| multi_booth_8bit | success | fallback/merged | test_verified_multi_booth_8bit_basic:success/no_failure, test_verified_multi_booth_8bit_edge:success/no_failure | exact=10, guarded=2, unresolved=8 | - |
| multi_pipe_4bit | success | fallback/merged | test_verified_multi_pipe_basic:success/no_failure, test_verified_multi_pipe_edge:success/no_failure | exact=11, guarded=0, unresolved=0 | - |
| multi_pipe_8bit | success | fallback/merged | test_verified_multi_pipe_8bit_basic:success/no_failure, test_verified_multi_pipe_8bit_edge:success/no_failure | exact=10, guarded=0, unresolved=10 | - |
| parallel2serial | success | fallback/merged | test_verified_parallel2serial_basic:success/no_failure, test_verified_parallel2serial_edge:success/no_failure | exact=0, guarded=0, unresolved=0 | - |
| pe | success | fallback/merged | test_verified_pe_basic:success/no_failure, test_verified_pe_edge:success/no_failure | exact=6, guarded=0, unresolved=5 | - |
| pulse_detect | success | fallback/merged | test_verified_pulse_detect_basic:success/no_failure, test_verified_pulse_detect_edge:success/no_failure | exact=0, guarded=0, unresolved=11 | - |
| radix2_div | success | fallback/merged | test_verified_radix2_div_basic:success/no_failure, test_verified_radix2_div_protocol:success/no_failure, test_verified_radix2_div_edge:success/no_failure | exact=0, guarded=20, unresolved=16 | - |
| right_shifter | success | fallback/merged | test_verified_right_shifter_basic:success/no_failure, test_verified_right_shifter_edge:success/no_failure | exact=0, guarded=2, unresolved=6 | - |
| ring_counter | success | merged/merged | test_ring_counter_basic:success/no_failure, test_ring_counter_edge:success/no_failure | exact=0, guarded=0, unresolved=9 | - |
| sequence_detector | success | merged/merged | test_sequence_detector_basic:success/no_failure, test_sequence_detector_edge:success/no_failure | exact=11, guarded=0, unresolved=1 | - |
| serial2parallel | success | merged/merged | test_verified_serial2parallel_basic:success/no_failure, test_verified_serial2parallel_protocol:success/no_failure, test_verified_serial2parallel_edge:success/no_failure | exact=9, guarded=0, unresolved=11 | - |
| signal_generator | success | merged/merged | test_verified_signal_generator_basic:success/no_failure, test_verified_signal_generator_edge:success/no_failure | exact=0, guarded=0, unresolved=9 | - |
| square_wave | success | merged/merged | test_square_wave_basic:success/no_failure, test_square_wave_edge:success/no_failure | exact=0, guarded=0, unresolved=8 | - |
| sub_64bit | success | fallback/merged | test_sub_64bit_basic:success/no_failure, test_sub_64bit_edge:success/no_failure | exact=0, guarded=0, unresolved=3 | - |
| synchronizer | success | fallback/merged | test_verified_synchronizer_basic:success/no_failure, test_verified_synchronizer_edge:success/no_failure | exact=1, guarded=0, unresolved=4 | - |
| traffic_light | success | fallback/merged | test_verified_traffic_light_basic:success/no_failure, test_verified_traffic_light_edge:success/no_failure | exact=0, guarded=0, unresolved=20 | - |
| up_down_counter | success | merged/merged | test_up_down_counter_basic:success/no_failure, test_up_down_counter_edge:success/no_failure | exact=0, guarded=0, unresolved=9 | - |
| width_8to16 | success | merged/merged | test_verified_width_8to16_basic:success/no_failure, test_verified_width_8to16_protocol:success/no_failure, test_verified_width_8to16_edge:success/no_failure | exact=10, guarded=0, unresolved=9 | - |
