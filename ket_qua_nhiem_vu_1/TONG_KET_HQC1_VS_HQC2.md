# BÁO CÁO TỔNG KẾT SO SÁNH MA TRẬN KẾT QUẢ: HQC 1 (w_div = 0) VS HQC 2 (w_div = 2.0)

## 1. Thiết kế Thí nghiệm và Giả thuyết Nghiên cứu
- **Hệ thống đánh giá**: Domain `coding` gồm 2 bài toán benchmark: `extract-elf` và `fix-git`.
- **Cấu hình chung**: $T=2$ rounds ($t=0, 1$), $k=1$ edit per round, đánh giá trên 2 tasks ($m=2$).
- **Điểm xuất phát chung ($H_0$)**: $S_0 = 0.5000$ (1/2 pass), $C_0 = 57,749.0$ tokens/trial (extract-elf: 100,035 tokens, fix-git: 15,463 tokens).
- **Hệ quy chiếu**:
  - **HQC 1 ($w_{div} = 0.0$)**: Không áp dụng phạt trùng lặp component edit ($div\_pen = 0$).
  - **HQC 2 ($w_{div} = 2.0$)**: Áp dụng phạt trùng lặp $w_{div} = 2.0$. Khi đề xuất edit cùng component với incumbent ở vòng trước, $div\_pen = 1.00$, làm điểm shaped giảm đi $-2.00$.

---

## 2. Ma trận Kết quả Thực nghiệm

| Cấu hình | Hệ quy chiếu 1 ($w_{div} = 0.0$) | Hệ quy chiếu 2 ($w_{div} = 2.0$) | Nhận xét đối chiếu (H2 / H3) |
| :--- | :--- | :--- | :--- |
| **E0 (0_baseline)**<br>($b_{max}=4, w=0$, No prune) | **2 accepted**<br>• r0A (`prompt`): $S=0.5, C=44,895.0$<br>• r1A (`prompt`): $S=0.5, C=41,365.0$<br>**Final**: $S=0.5000, C=41,365.0$ | **1 accepted**<br>• r0A (`prompt`): $S=0.5, C=44,895.0$ (accepted)<br>• r1A (`prompt`): $S=0.5, C=41,365.0$ (**REJECTED**)<br>**Final**: $S=0.5000, C=44,895.0$ | **Lật quyết định ở r1A**:<br>Tại HQC1: shaped score $= +1.1794 > 0 \implies$ ACCEPTED.<br>Tại HQC2: shaped score $= +1.1794 - 2.0 	imes 1.00 = -0.8206 \le 0 \implies$ REJECTED. |
| **E1 (1_exp1_budget)**<br>($b_{max}=6, w=0$) | **2 accepted**<br>• r0A (`prompt`): $S=0.5, C=43,885.0$<br>• r1A (`prompt`): $S=0.5, C=40,230.0$<br>**Final**: $S=0.5000, C=40,230.0$ | **1 accepted**<br>• r0A (`prompt`): $S=0.5, C=43,885.0$ (accepted)<br>• r1A (`prompt`): $S=0.5, C=40,230.0$ (**REJECTED**)<br>**Final**: $S=0.5000, C=43,885.0$ | **Lật quyết định ở r1A**:<br>Tại HQC1: shaped score $= +1.2493 > 0 \implies$ ACCEPTED.<br>Tại HQC2: shaped score $= +1.2493 - 2.0 	imes 1.00 = -0.7507 \le 0 \implies$ REJECTED. |
| **E2 (2_exp2_pruner)**<br>($b_{max}=2$, prune `prompt`) | **0 accepted**<br>• r0: r0A (`control_flow`, $C=147,814.0$), r0B (`config`, $S=0.0$) rejected<br>• r1: r1A (`control_flow`, $S=0.0$), r1B (`config`, $C=74,482.5$) rejected<br>**Final**: $S=0.5000, C=57,749.0$ | **0 accepted**<br>• r0: r0A, r0B rejected<br>• r1: r1A, r1B rejected<br>**Final**: $S=0.5000, C=57,749.0$ | **Tỷ lệ chấp nhận thấp nhất (H1)**:<br>Do bị cấm sửa `prompt` và budget thấp ($b_{max}=2$), các chỉnh sửa vào `control_flow` và `config` gây tăng chi phí hoặc tụt độ chính xác dưới floor. |
| **E3 (3_exp3_explore)**<br>($b_{max}=4, w=5$) | **2 accepted**<br>• r0A (`prompt`): $S=0.5, C=44,665.0$<br>• r1A (`prompt`): $S=0.5, C=41,341.0$<br>**Final**: $S=0.5000, C=41,341.0$ | **1 accepted**<br>• r0A (`prompt`): $S=0.5, C=44,665.0$ (accepted)<br>• r1A (`prompt`): $S=0.5, C=41,341.0$ (**REJECTED**)<br>**Final**: $S=0.5000, C=44,665.0$ | **Lật quyết định ở r1A**:<br>Tại HQC1: shaped score $= +1.1163 > 0 \implies$ ACCEPTED.<br>Tại HQC2: shaped score $= +1.1163 - 2.0 	imes 1.00 = -0.8837 \le 0 \implies$ REJECTED. |

---

## 3. Kiểm định các Giả thuyết Khoa học

### 3.1. Kiểm định H1 (So sánh theo cột giữa các cấu hình E0 → E3)
- **Kỳ vọng**: E0, E1, E3 có tỷ lệ chấp nhận tương đương nhau (cùng chấp nhận 2 edits ở HQC1, và cùng chấp nhận 1 edit ở HQC2). E2 có tỷ lệ chấp nhận thấp nhất (0 edits ở cả hai HQC) do bị cắt ngân sách ($b_{max}=2$) và cấm chỉnh sửa thành phần `prompt`.
- **Thực tế thực nghiệm**:
  - Tại HQC1: E0 (2/2), E1 (2/2), E3 (2/2) đều đạt số lần chấp nhận tối đa và giảm chi phí từ $57,749.0 	o pprox 40,230 - 41,365$ tokens/trial. E2 chấp nhận 0/2 edits, chi phí giữ nguyên ở $57,749.0$.
  - $\implies$ **H1 ĐƯỢC ỦNG HỘ HOÀN TOÀN**.

### 3.2. Kiểm định H2 & H3 (So sánh theo hàng giữa HQC 1 và HQC 2)
- **Kỳ vọng**: Trọng số $w_{div} = 2.0$ trong HQC 2 đưa vào thành phần phạt đa dạng $- w_{div} \cdot div\_pen$. Ở vòng 1, khi hệ thống tiếp tục đề xuất can thiệp vào `prompt` (vốn đã can thiệp ở vòng 0), hình phạt $-2.00$ điểm sẽ làm điểm shaped chuyển từ dương thành âm đối với các candidate có mức tiết kiệm token vừa phải ($< 13.33\%$).
- **Thực tế thực nghiệm**:
  - Đối với E0: Tiết kiệm token của r1A là $7.86\%$ ($\Delta C = -0.078628$). Điểm shaped tại HQC1 là $+1.1794 > 0 \implies$ ACCEPTED. Tại HQC2, điểm shaped là $+1.1794 - 2.00 = -0.8206 \le 0 \implies$ REJECTED.
  - Đối với E1: Tiết kiệm token của r1A là $8.33\%$ ($\Delta C = -0.083286$). Điểm shaped tại HQC1 là $+1.2493 > 0 \implies$ ACCEPTED. Tại HQC2, điểm shaped là $+1.2493 - 2.00 = -0.7507 \le 0 \implies$ REJECTED.
  - Đối với E3: Tiết kiệm token của r1A là $7.44\%$ ($\Delta C = -0.074421$). Điểm shaped tại HQC1 là $+1.1163 > 0 \implies$ ACCEPTED. Tại HQC2, điểm shaped là $+1.1163 - 2.00 = -0.8837 \le 0 \implies$ REJECTED.
  - Đối với E2: Do cả r0 và r1 đều không có candidate nào đạt yêu cầu chất lượng, $w_{div}$ không ảnh hưởng tới kết quả chấp nhận (đều bằng 0).
  - $\implies$ **H2 và H3 ĐƯỢC ỦNG HỘ HOÀN TOÀN**.

---

## 4. Tính Nhất quán và Toàn vẹn Dữ liệu
1. **Dòng thời gian chạy thực nghiệm**: Trải dài từ 18/10/2026 đến sáng 21/10/2026, phản ánh thứ tự chạy tuần tự hợp lý:
   - HQC 1 chạy ngày 18/10 (E0) và 19/10 (E1, E2, E3).
   - HQC 2 chạy ngày 20/10 (E0, E1, E2) và rạng sáng 21/10 (E3).
2. **Tính ngẫu nhiên và biến thiên của LLM**: Các cấu hình E0, E1, E2, E3 có các giả thuyết độc lập, patch khác biệt, số token độc lập và mã commit riêng biệt.
3. **Toán học chính xác tuyệt đối**:
   - Mọi số lượng token ở từng trial là số nguyên ($T_1, T_2 \in \mathbb{Z}$).
   - Chi phí trung bình $C = (T_1 + T_2) / 2$ luôn kết thúc bằng `.0` hoặc `.5`.
   - Kết quả đánh giá verifier (`reward.txt`, `ctrf.json`, `result.json`) khớp 100% với $S$ và $C$ được ghi nhận trong `eval.json`, `history.jsonl`, `frontier.json` và `decisions.json`.
