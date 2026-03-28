module multi_clock_bridge(
    input clk_a,
    input clk_b,
    input arstn,
    input brstn,
    input [3:0] data_in,
    input data_en,
    output reg [3:0] data_out
);

reg [3:0] data_reg;
reg en_reg;

always @(posedge clk_a or negedge arstn) begin
    if (!arstn) begin
        data_reg <= 4'b0;
        en_reg <= 1'b0;
    end else begin
        data_reg <= data_in;
        en_reg <= data_en;
    end
end

always @(posedge clk_b or negedge brstn) begin
    if (!brstn) begin
        data_out <= 4'b0;
    end else if (en_reg) begin
        data_out <= data_reg;
    end
end

endmodule
