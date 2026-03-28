`timescale 1ns / 1ps

module verified_alu(
    input [31:0] a,
    input [31:0] b,
    input [5:0] aluc,
    output [31:0] r,
    output zero,
    output carry,
    output negative,
    output overflow,
    output flag
);
    assign r = 32'h00000000;
    assign zero = 1'b1;
    assign carry = 1'b0;
    assign negative = 1'b0;
    assign overflow = 1'b0;
    assign flag = 1'b0;
endmodule
