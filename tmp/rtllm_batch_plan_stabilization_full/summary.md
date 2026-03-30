# RTLLM Batch Summary

- Benchmark root: `/workspace/I/qimeng6/wangchuanhao/QiMeng-Agent/VerilogBenchmark/Benchmarks/RTLLM_for_ivl`
- Output dir: `/workspace/I/qimeng6/wangchuanhao/cocoverify2/tmp/rtllm_batch_plan_stabilization_full`
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
- Tasks with guarded/unresolved policies: 44
- LLM plan attempted/succeeded/fallback: 50/47/3
- LLM oracle attempted/succeeded/fallback: 50/50/0
- Resumed tasks: 0

## Histograms

- Triage: `{"no_failure": 88}`
- Assertion strength: `{"exact": 145, "guarded": 64, "unresolved": 407}`
- LLM plan status: `{"fallback": 3, "merged": 47}`
- LLM plan fallback reasons: `{"json_parse": 1, "timeout": 2}`
- LLM oracle status: `{"merged": 50}`
- LLM oracle fallback reasons: `{}`

## Per-Task Rollup

| Task | Status | LLM(plan/oracle) | Modules | Assertion Strengths | Failure Summary |
| --- | --- | --- | --- | --- | --- |
| JC_counter | success | merged/merged | test_verified_JC_counter_basic:success/no_failure | exact=4, guarded=0, unresolved=2 | - |
| LFSR | success | merged/merged | test_LFSR_basic:success/no_failure | exact=0, guarded=0, unresolved=7 | - |
| LIFObuffer | success | merged/merged | test_LIFObuffer_basic:success/no_failure, test_LIFObuffer_edge:success/no_failure | exact=8, guarded=0, unresolved=25 | - |
| RAM | success | merged/merged | test_verified_RAM_basic:success/no_failure, test_verified_RAM_edge:success/no_failure | exact=2, guarded=0, unresolved=4 | - |
| ROM | success | merged/merged | test_ROM_basic:success/no_failure, test_ROM_edge:success/no_failure | exact=0, guarded=0, unresolved=3 | - |
| accu | success | merged/merged | test_accu_basic:success/no_failure, test_accu_edge:success/no_failure | exact=12, guarded=0, unresolved=5 | - |
| adder_16bit | success | merged/merged | test_verified_adder_16bit_basic:success/no_failure, test_verified_adder_16bit_edge:success/no_failure | exact=0, guarded=1, unresolved=9 | - |
| adder_32bit | success | merged/merged | test_verified_adder_32bit_basic:success/no_failure | exact=0, guarded=0, unresolved=6 | - |
| adder_8bit | success | merged/merged | test_verified_adder_8bit_basic:success/no_failure, test_verified_adder_8bit_edge:success/no_failure | exact=0, guarded=1, unresolved=11 | - |
| adder_bcd | success | merged/merged | test_adder_bcd_basic:success/no_failure, test_adder_bcd_edge:success/no_failure | exact=0, guarded=1, unresolved=11 | - |
| adder_pipe_64bit | success | merged/merged | test_verified_adder_64bit_basic:success/no_failure, test_verified_adder_64bit_edge:success/no_failure | exact=0, guarded=0, unresolved=22 | - |
| alu | success | merged/merged | test_verified_alu_basic:success/no_failure, test_verified_alu_edge:success/no_failure | exact=0, guarded=12, unresolved=20 | - |
| asyn_fifo | success | fallback/merged | test_dual_port_RAM_basic:success/no_failure, test_dual_port_RAM_edge:success/no_failure | exact=0, guarded=0, unresolved=6 | - |
| barrel_shifter | success | merged/merged | test_barrel_shifter_basic:success/no_failure | exact=0, guarded=0, unresolved=2 | - |
| calendar | success | merged/merged | test_verified_calendar_basic:success/no_failure | exact=0, guarded=0, unresolved=15 | - |
| clkgenerator | success | merged/merged | test_clkgenerator_basic:success/no_failure | exact=0, guarded=0, unresolved=3 | - |
| comparator_3bit | success | merged/merged | test_comparator_3bit_basic:success/no_failure, test_comparator_3bit_edge:success/no_failure | exact=18, guarded=0, unresolved=0 | - |
| comparator_4bit | success | merged/merged | test_comparator_4bit_basic:success/no_failure, test_comparator_4bit_edge:success/no_failure | exact=0, guarded=0, unresolved=18 | - |
| counter_12 | success | fallback/merged | test_verified_counter_12_basic:success/no_failure, test_verified_counter_12_edge:success/no_failure | exact=0, guarded=0, unresolved=11 | - |
| div_16bit | success | merged/merged | test_verified_div_16bit_basic:success/no_failure, test_verified_div_16bit_edge:success/no_failure | exact=0, guarded=2, unresolved=10 | - |
| edge_detect | success | merged/merged | test_verified_edge_detect_basic:success/no_failure, test_verified_edge_detect_edge:success/no_failure | exact=8, guarded=0, unresolved=11 | - |
| fixed_point_adder | success | merged/merged | test_fixed_point_adder_basic:success/no_failure, test_fixed_point_adder_edge:success/no_failure | exact=0, guarded=0, unresolved=7 | - |
| fixed_point_subtractor | success | merged/merged | test_fixed_point_subtractor_basic:success/no_failure, test_fixed_point_subtractor_edge:success/no_failure | exact=0, guarded=0, unresolved=6 | - |
| float_multi | success | merged/merged | test_float_multi_basic:success/no_failure, test_float_multi_edge:success/no_failure | exact=0, guarded=2, unresolved=9 | - |
| freq_div | success | merged/merged | test_freq_div_basic:success/no_failure | exact=0, guarded=0, unresolved=0 | - |
| freq_divbyeven | success | merged/merged | test_freq_divbyeven_basic:success/no_failure | exact=0, guarded=0, unresolved=7 | - |
| freq_divbyfrac | success | merged/merged | test_freq_divbyfrac_basic:success/no_failure | exact=0, guarded=0, unresolved=3 | - |
| freq_divbyodd | success | merged/merged | test_freq_divbyodd_basic:success/no_failure | exact=0, guarded=0, unresolved=6 | - |
| fsm | success | fallback/merged | test_verified_fsm_basic:success/no_failure, test_verified_fsm_edge:success/no_failure | exact=11, guarded=0, unresolved=0 | - |
| instr_reg | success | merged/merged | test_instr_reg_basic:success/no_failure, test_instr_reg_edge:success/no_failure | exact=0, guarded=6, unresolved=21 | - |
| multi_16bit | success | merged/merged | test_verified_multi_16bit_basic:success/no_failure, test_verified_multi_16bit_protocol:success/no_failure, test_verified_multi_16bit_edge:success/no_failure | exact=8, guarded=11, unresolved=6 | - |
| multi_8bit | success | merged/merged | test_multi_8bit_basic:success/no_failure, test_multi_8bit_edge:success/no_failure | exact=1, guarded=0, unresolved=3 | - |
| multi_booth_8bit | success | merged/merged | test_verified_multi_booth_8bit_basic:success/no_failure, test_verified_multi_booth_8bit_edge:success/no_failure | exact=11, guarded=2, unresolved=8 | - |
| multi_pipe_4bit | success | merged/merged | test_verified_multi_pipe_basic:success/no_failure, test_verified_multi_pipe_edge:success/no_failure | exact=11, guarded=0, unresolved=0 | - |
| multi_pipe_8bit | success | merged/merged | test_verified_multi_pipe_8bit_basic:success/no_failure, test_verified_multi_pipe_8bit_edge:success/no_failure | exact=11, guarded=0, unresolved=11 | - |
| parallel2serial | success | merged/merged | test_verified_parallel2serial_basic:success/no_failure, test_verified_parallel2serial_edge:success/no_failure | exact=16, guarded=0, unresolved=0 | - |
| pe | success | merged/merged | test_verified_pe_basic:success/no_failure, test_verified_pe_edge:success/no_failure | exact=6, guarded=0, unresolved=5 | - |
| pulse_detect | success | merged/merged | test_verified_pulse_detect_basic:success/no_failure, test_verified_pulse_detect_edge:success/no_failure | exact=0, guarded=0, unresolved=12 | - |
| radix2_div | success | merged/merged | test_verified_radix2_div_basic:success/no_failure, test_verified_radix2_div_protocol:success/no_failure, test_verified_radix2_div_edge:success/no_failure | exact=0, guarded=22, unresolved=16 | - |
| right_shifter | success | merged/merged | test_verified_right_shifter_basic:success/no_failure, test_verified_right_shifter_edge:success/no_failure | exact=0, guarded=2, unresolved=6 | - |
| ring_counter | success | merged/merged | test_ring_counter_basic:success/no_failure | exact=0, guarded=0, unresolved=7 | - |
| sequence_detector | success | merged/merged | test_sequence_detector_basic:success/no_failure | exact=7, guarded=0, unresolved=0 | - |
| serial2parallel | success | merged/merged | test_verified_serial2parallel_basic:success/no_failure, test_verified_serial2parallel_edge:success/no_failure | exact=0, guarded=0, unresolved=5 | - |
| signal_generator | success | merged/merged | test_verified_signal_generator_basic:success/no_failure | exact=0, guarded=0, unresolved=9 | - |
| square_wave | success | merged/merged | test_square_wave_basic:success/no_failure, test_square_wave_edge:success/no_failure | exact=0, guarded=0, unresolved=8 | - |
| sub_64bit | success | merged/merged | test_sub_64bit_basic:success/no_failure, test_sub_64bit_edge:success/no_failure | exact=0, guarded=0, unresolved=3 | - |
| synchronizer | success | merged/merged | test_verified_synchronizer_basic:success/no_failure, test_verified_synchronizer_edge:success/no_failure | exact=1, guarded=0, unresolved=4 | - |
| traffic_light | success | merged/merged | test_verified_traffic_light_basic:success/no_failure, test_verified_traffic_light_edge:success/no_failure | exact=0, guarded=2, unresolved=34 | - |
| up_down_counter | success | merged/merged | test_up_down_counter_basic:success/no_failure | exact=0, guarded=0, unresolved=6 | - |
| width_8to16 | success | merged/merged | test_verified_width_8to16_basic:success/no_failure, test_verified_width_8to16_edge:success/no_failure | exact=10, guarded=0, unresolved=4 | - |
