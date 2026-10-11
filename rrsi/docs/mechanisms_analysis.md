```mermaid
flowchart TD
    subgraph S1 ["1. Khởi tạo vòng t"]
        Ht["Incumbent Harness H_t"]
        History["Lịch sử L_t & Báo cáo Lỗi F_t"]
    end

    subgraph S2 ["2. Proposer Module"]
        BudgetCalc["Tính ngân sách b_t"]
        StallCheck{"Hệ thống bị Stall? (sigma_t == 1)"}
        StallCheck -- Có --> ForceExplore["Ép chọn Component chưa từng thử"]
        StallCheck -- Không --> FreeExplore["Đề xuất bình thường"]
    end

    BudgetCalc --> GenCode["Agent sinh code diff H'"]
    ForceExplore --> GenCode
    FreeExplore --> GenCode
    PruneSet["Danh sách cần cắt tỉa B_t"] --> GenCode

    S1 --> S2

    subgraph S3 ["3. Critic Gatekeeper"]
        RegexCheck{"Chứa Task ID / Key?"}
        LLMCritic{"Critic LLM: Phát hiện Leakage / Gaming?"}
    end

    GenCode --> RegexCheck
    RegexCheck -- Không vi phạm --> LLMCritic
    RegexCheck -- Vi phạm --> Reject["Loại bỏ & Yêu cầu sửa"]
    LLMCritic -- Vi phạm --> Reject

    subgraph S4 ["4. Thực thi & Đo lường"]
        LLMCritic -- Chấp nhận --> RunEval["Chạy Harness trên D_evolve"]
        RunEval --> CalcMetrics["Tính Accuracy S' và Token Cost C'"]
    end

    subgraph S5 ["5. Selector Module"]
        FloorCheck{"S' >= S* - delta? (Không tụt dốc)"}
        FloorCheck -- Không đạt --> Drop["Loại bỏ ứng viên"]
        FloorCheck -- Đạt --> CostCheck{"Delta S > delta? (Tăng điểm rõ rệt)"}
        CostCheck -- Đúng --> TokenBudget{"Delta C <= beta0 + beta1 * Delta S?"}
        CostCheck -- Sai --> ShapedScore{"w_s*dS - w_c*dC + w_n*nu > 0?"}
    end

    TokenBudget -- Đạt --> Valid["Đủ điều kiện Admissible"]
    TokenBudget -- Vượt trần --> Drop
    ShapedScore -- Đạt --> Valid
    ShapedScore -- Không --> Drop

    CalcMetrics --> FloorCheck

    subgraph S6 ["6. Cập nhật vòng t+1"]
        Valid --> Argmax["Chọn ứng viên Max S'"]
        Argmax --> Update["Cập nhật H_{t+1} = H'"]
        Drop --> Retain["Giữ nguyên H_{t+1} = H_t"]
    end