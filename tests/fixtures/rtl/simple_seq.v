module simple_seq #(
    parameter WIDTH = 8
) (
    input clk,
    input rst_n,
    input [WIDTH-1:0] d,
    output logic [WIDTH-1:0] q,
    output reg done
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            q <= '0;
            done <= 1'b0;
        end else begin
            q <= d;
            done <= 1'b1;
        end
    end
endmodule
