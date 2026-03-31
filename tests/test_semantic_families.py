"""Semantic family inference tests."""

from __future__ import annotations

from cocoverify2.core.models import DUTContract, PortSpec, TimingSpec
from cocoverify2.core.types import PortDirection, SequentialKind
from cocoverify2.utils.semantic_families import (
    infer_fifo_readback_family,
    infer_grouped_valid_accumulator_family,
    infer_pipelined_multiply_family,
    infer_sequence_detect_family,
    infer_serial_to_parallel_family,
)


def test_grouped_valid_accumulator_family_detects_noncanonical_roles() -> None:
    contract = DUTContract(
        module_name="stream_accumulator",
        ports=[
            PortSpec(name="clk_i", direction=PortDirection.INPUT, width=1),
            PortSpec(name="rst_ni", direction=PortDirection.INPUT, width=1),
            PortSpec(name="sample_bus", direction=PortDirection.INPUT, width=8),
            PortSpec(name="accept_i", direction=PortDirection.INPUT, width=1),
            PortSpec(name="sum_total", direction=PortDirection.OUTPUT, width=10),
            PortSpec(name="sum_done", direction=PortDirection.OUTPUT, width=1),
        ],
        observable_outputs=["sum_total", "sum_done"],
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.8),
    )

    family = infer_grouped_valid_accumulator_family(
        contract,
        task_description="Accumulate every four accepted samples and emit one grouped sum output.",
        spec_text="After four valid input samples, assert a completion pulse and present the accumulated sum.",
    )

    assert family is not None
    assert family["input_data_signal"] == "sample_bus"
    assert family["input_gate_signal"] == "accept_i"
    assert family["output_data_signal"] == "sum_total"
    assert family["output_gate_signal"] == "sum_done"
    assert family["group_size"] == 4


def test_grouped_valid_accumulator_family_does_not_match_multiplier_like_start_done_interface() -> None:
    contract = DUTContract(
        module_name="iterative_multiplier",
        ports=[
            PortSpec(name="clk", direction=PortDirection.INPUT, width=1),
            PortSpec(name="rst_n", direction=PortDirection.INPUT, width=1),
            PortSpec(name="start", direction=PortDirection.INPUT, width=1),
            PortSpec(name="ain", direction=PortDirection.INPUT, width=16),
            PortSpec(name="bin", direction=PortDirection.INPUT, width=16),
            PortSpec(name="done", direction=PortDirection.OUTPUT, width=1),
            PortSpec(name="yout", direction=PortDirection.OUTPUT, width=32),
        ],
        observable_outputs=["done", "yout"],
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.8),
    )

    family = infer_grouped_valid_accumulator_family(
        contract,
        task_description="Start a 16-bit multiplication and assert done when the product is available.",
        spec_text="After start, multiply ain by bin and present the product on yout when done is asserted.",
    )

    assert family is None


def test_serial_to_parallel_family_detects_alias_roles() -> None:
    contract = DUTContract(
        module_name="stream_deserializer",
        ports=[
            PortSpec(name="clk_i", direction=PortDirection.INPUT, width=1),
            PortSpec(name="rst_ni", direction=PortDirection.INPUT, width=1),
            PortSpec(name="bit_i", direction=PortDirection.INPUT, width=1),
            PortSpec(name="sample_gate", direction=PortDirection.INPUT, width=1),
            PortSpec(name="byte_out", direction=PortDirection.OUTPUT, width=8),
            PortSpec(name="byte_ready", direction=PortDirection.OUTPUT, width=1),
        ],
        observable_outputs=["byte_out", "byte_ready"],
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.8),
    )

    family = infer_serial_to_parallel_family(
        contract,
        task_description="Convert a serial bit stream into one parallel byte after eight valid bits.",
        spec_text="A completion pulse indicates the byte is ready after one full serial transfer.",
    )

    assert family is not None
    assert family["serial_input_signal"] == "bit_i"
    assert family["input_gate_signal"] == "sample_gate"
    assert family["parallel_output_signal"] == "byte_out"
    assert family["output_gate_signal"] == "byte_ready"
    assert family["bit_count"] == 8


def test_fifo_family_detects_write_read_roles_without_exact_names() -> None:
    contract = DUTContract(
        module_name="queue_buffer",
        ports=[
            PortSpec(name="wr_clk", direction=PortDirection.INPUT, width=1),
            PortSpec(name="rd_clk", direction=PortDirection.INPUT, width=1),
            PortSpec(name="push_req", direction=PortDirection.INPUT, width=1),
            PortSpec(name="push_payload", direction=PortDirection.INPUT, width=8),
            PortSpec(name="pop_req", direction=PortDirection.INPUT, width=1),
            PortSpec(name="pop_payload", direction=PortDirection.OUTPUT, width=8),
            PortSpec(name="empty_o", direction=PortDirection.OUTPUT, width=1),
            PortSpec(name="full_o", direction=PortDirection.OUTPUT, width=1),
        ],
        observable_outputs=["pop_payload", "empty_o", "full_o"],
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.8),
    )

    family = infer_fifo_readback_family(
        contract,
        task_description="FIFO queue with one pushed byte later read back from the output.",
        spec_text="Write then readback while checking empty and full flags.",
    )

    assert family is not None
    assert family["write_enable_signal"] == "push_req"
    assert family["read_enable_signal"] == "pop_req"
    assert family["write_data_signal"] == "push_payload"
    assert family["read_data_signal"] == "pop_payload"
    assert family["empty_signal"] == "empty_o"
    assert family["full_signal"] == "full_o"


def test_sequence_detect_family_uses_pattern_text_instead_of_exact_names() -> None:
    contract = DUTContract(
        module_name="pattern_matcher",
        ports=[
            PortSpec(name="clk_i", direction=PortDirection.INPUT, width=1),
            PortSpec(name="rst_ni", direction=PortDirection.INPUT, width=1),
            PortSpec(name="bit_stream", direction=PortDirection.INPUT, width=1),
            PortSpec(name="match_o", direction=PortDirection.OUTPUT, width=1),
        ],
        observable_outputs=["match_o"],
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.8),
    )

    family = infer_sequence_detect_family(
        contract,
        task_description="Detect the input sequence 1001 on the serial bit stream.",
        spec_text="Assert match_o when pattern 1001 is observed.",
    )

    assert family is not None
    assert family["input_signal"] == "bit_stream"
    assert family["output_signal"] == "match_o"
    assert family["bit_pattern"] == "1001"


def test_pipelined_multiply_family_marks_booth_design_as_signed_or_ambiguous() -> None:
    contract = DUTContract(
        module_name="booth_multiplier",
        ports=[
            PortSpec(name="clk", direction=PortDirection.INPUT, width=1),
            PortSpec(name="reset", direction=PortDirection.INPUT, width=1),
            PortSpec(name="a", direction=PortDirection.INPUT, width=8),
            PortSpec(name="b", direction=PortDirection.INPUT, width=8),
            PortSpec(name="p", direction=PortDirection.OUTPUT, width=16),
            PortSpec(name="rdy", direction=PortDirection.OUTPUT, width=1),
        ],
        observable_outputs=["p", "rdy"],
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.8),
    )

    family = infer_pipelined_multiply_family(
        contract,
        task_description="Implement an 8-bit Radix-4 Booth multiplier with ready pulse.",
        spec_text="Use the Booth algorithm and sign-extended partial products before asserting rdy.",
    )

    assert family is not None
    assert family["arithmetic_domain"] == "signed_or_ambiguous"
