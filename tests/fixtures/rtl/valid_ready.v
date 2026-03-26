module valid_ready #(
    parameter WIDTH = 8
) (
    input aclk,
    input aresetn,
    input in_valid,
    output in_ready,
    input [WIDTH-1:0] in_data,
    output out_valid,
    input out_ready,
    output [WIDTH-1:0] out_data,
    input start,
    output done
);
    assign in_ready = out_ready;
    assign out_valid = in_valid;
    assign out_data = in_data;
    assign done = start & in_valid & out_ready;
endmodule
