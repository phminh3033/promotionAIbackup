# Hướng dẫn Pilot PromoPilot AI cho Doanh nghiệp SME

Tài liệu này hướng dẫn quy trình 5 ngày để một doanh nghiệp SME thử nghiệm (pilot) PromoPilot AI
với dữ liệu thật, và cách đo lường kết quả sau khi chạy campaign đầu tiên.

---

## Trước khi bắt đầu — Điều kiện cần có

- File dữ liệu bán hàng xuất từ POS/phần mềm bán hàng (Excel hoặc CSV), tối thiểu **60-90 ngày**
  gần nhất (càng dài càng tốt, lý tưởng ≥ 12 tháng để thấy mùa vụ).
- Một máy tính cài được Python 3.10+ (xem README.md mục 3-5).
- Người phụ trách: chủ doanh nghiệp, Marketing Manager, hoặc Sales/Operations Manager — không cần
  biết lập trình hay Data Science.

---

## Ngày 1: Thu thập dữ liệu

**Mục tiêu:** Có được file dữ liệu sạch nhất có thể từ hệ thống bán hàng hiện tại.

1. Xuất dữ liệu giao dịch từ POS/phần mềm bán hàng ra Excel/CSV.
2. Đảm bảo có tối thiểu 4 cột: Ngày, Mã sản phẩm, Số lượng, Doanh thu.
3. Nếu có thể, xuất thêm: Mã hoá đơn/giao dịch, Mã khách hàng, Giá vốn, Tồn kho, Lịch sử khuyến mãi.
4. Không cần làm sạch dữ liệu thủ công trước — PromoPilot AI có bước Data Quality Check riêng.
5. Đặt tên file rõ ràng (vd: `banhang_thang1_thang6_2026.csv`).

**Kết quả cần có cuối ngày:** 1 file dữ liệu sẵn sàng để upload.

---

## Ngày 2: Data Mapping & Kiểm tra chất lượng

**Mục tiêu:** Đưa dữ liệu vào hệ thống và hiểu được độ tin cậy có thể kỳ vọng.

1. Chạy `streamlit run app.py`, vào trang **1. Tải dữ liệu**, upload file.
2. Xác nhận/chỉnh Data Mapping Wizard (hệ thống tự gợi ý, bạn chỉ cần kiểm tra lại).
3. Sang trang **2. Chất lượng dữ liệu**, đọc kỹ:
   - Điểm chất lượng dữ liệu (0-100) và ý nghĩa.
   - Cảnh báo (dữ liệu trùng, thiếu ngày, giá trị âm...).
   - Module nào đang bật/tắt dựa theo dữ liệu hiện có.
4. Nếu điểm quá thấp (<50), quay lại nguồn dữ liệu để bổ sung/làm sạch trước khi tiếp tục.
5. Vào trang **7. Mục tiêu kinh doanh**, điền Hồ sơ Doanh nghiệp (ngành hàng, margin, lead time,
   safety stock, ngân sách khuyến mãi...) — đây là bước quan trọng vì toàn bộ đề xuất sau này phụ
   thuộc vào các con số này.

**Kết quả cần có cuối ngày:** Dữ liệu đã mapping xong, điểm chất lượng ≥ 60, hồ sơ doanh nghiệp đã lưu.

---

## Ngày 3: Train model & Xem dự báo

**Mục tiêu:** Có dự báo nhu cầu/doanh thu và đề xuất tồn kho đầu tiên.

1. Vào trang **3. Dự báo**, chạy dự báo cho:
   - Doanh thu toàn công ty (7/14/30 ngày).
   - 3-5 sản phẩm bán chạy nhất (theo SKU).
2. Đọc phần giải thích "Hệ thống chọn mô hình X vì..." — không cần hiểu sâu kỹ thuật, chỉ cần biết
   **độ tin cậy** (Cao/Trung bình/Thấp).
3. Vào trang **6. Tồn kho**, nhập Lead Time và Safety Stock theo thực tế doanh nghiệp, xem danh
   sách sản phẩm cần đặt hàng và rủi ro hết hàng/tồn dư.
4. (Nếu có Mã khách hàng) Vào trang **4. Khách hàng** xem phân khúc RFM.
5. (Nếu có Mã giao dịch) Vào trang **5. Sản phẩm & Giỏ hàng** xem sản phẩm hay mua cùng nhau.

**Kết quả cần có cuối ngày:** Danh sách sản phẩm cần nhập hàng tuần tới, hiểu được nhóm khách hàng chính.

---

## Ngày 4: Review kết quả & Mô phỏng khuyến mãi

**Mục tiêu:** Thử nhiều kịch bản khuyến mãi và chọn phương án phù hợp.

1. Ở trang **7. Mục tiêu kinh doanh**, chọn 1 trong 4 mục tiêu: Traffic / Revenue / Profit / Clearance.
2. Vào trang **8. Kịch bản Promotion**, chọn sản phẩm/danh mục muốn khuyến mãi (ưu tiên sản phẩm
   tồn kho cao, hoặc sản phẩm có cặp bán kèm ở trang Giỏ hàng), chạy mô phỏng.
3. So sánh bảng kết quả: Sản lượng, Doanh thu, Lợi nhuận gộp, ROI của từng kịch bản.
4. Đọc phần "Đánh giá theo Business Rules" và "Giải thích thêm" để hiểu lý do đề xuất.
5. **Lưu ý quan trọng:** kết quả mô phỏng là ước tính dựa trên dữ liệu lịch sử/giả định, không phải
   cam kết chính xác tuyệt đối — dùng để **so sánh tương đối** giữa các phương án.

**Kết quả cần có cuối ngày:** Đã chọn được 1 kịch bản khuyến mãi để triển khai thử.

---

## Ngày 5: Chọn Campaign & Chuẩn bị triển khai

**Mục tiêu:** Có kế hoạch campaign hoàn chỉnh sẵn sàng triển khai.

1. Vào trang **9. AI Recommendation**, xem Recommendation Card tổng hợp (mục tiêu, sản phẩm, thời
   gian, khách hàng/nhu cầu/doanh thu/lợi nhuận dự kiến, rủi ro, độ tin cậy).
2. Vào trang **10. Campaign Plan**, xem kế hoạch tồn kho, nhân sự, và nội dung Facebook/Zalo/SMS.
3. Chỉnh sửa nội dung cho phù hợp giọng văn thương hiệu (nội dung sinh ra là bản nháp rule-based).
4. Xuất báo cáo (CSV/Excel) để lưu trữ và chia sẻ với đội ngũ liên quan.
5. Chuẩn bị: đặt hàng bổ sung theo đề xuất tồn kho, sắp xếp nhân sự theo đề xuất, lên lịch đăng bài.

**Kết quả cần có cuối ngày:** Campaign sẵn sàng chạy, có báo cáo lưu trữ.

---

## Sau khi chạy Campaign: Đo lường KPI

So sánh kết quả thực tế với dự báo trong Recommendation Card:

| Chỉ số | Dự báo (PromoPilot AI) | Thực tế | Chênh lệch |
|---|---|---|---|
| Số khách hàng | ... | ... | ... |
| Sản lượng bán | ... | ... | ... |
| Doanh thu | ... | ... | ... |
| Lợi nhuận gộp | ... | ... | ... |
| ROI | ... | ... | ... |

**Gợi ý:**

- Nếu chênh lệch lớn (>30%), đó là tín hiệu tốt để xem lại giả định elasticity đang dùng (trang
  Kịch bản Promotion sẽ tự động ưu tiên dữ liệu lịch sử thật một khi bạn tích luỹ đủ lịch sử
  khuyến mãi qua các đợt pilot tiếp theo).
- Mỗi đợt khuyến mãi chạy xong nên được ghi lại (loại khuyến mãi, mức giảm, thời gian) vào dữ liệu
  gốc — càng nhiều lịch sử khuyến mãi thật, độ chính xác của "historical uplift" trong hệ thống
  càng cải thiện qua các lần dùng sau.
- Lặp lại chu trình Ngày 3-5 hàng tuần/hàng tháng để liên tục tinh chỉnh chiến lược khuyến mãi.
