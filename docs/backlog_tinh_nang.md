# Backlog tính năng & nâng cấp PromoPilot AI

Danh sách các hạng mục nâng cấp tiếp theo, xếp theo độ ưu tiên. Skill `nang-cap-promopilot` đọc
file này mỗi lần chạy để chọn hạng mục tiếp theo. Khi hoàn thành một hạng mục, **di chuyển nó sang
phần "Đã hoàn thành"** ở cuối file kèm ngày, thay vì xoá — để giữ lịch sử.

Nguyên tắc chọn việc mỗi đợt: ưu tiên 1 hạng mục có phạm vi vừa đủ để hoàn thành trọn vẹn (code +
test + docs) trong 1 phiên, hơn là làm dở nhiều hạng mục.

---

## Nhóm A — Mô hình dự báo (độ chính xác)

0. **[Mới]** Tối ưu tốc độ Market Basket Analysis — hiện mất 30-50s trên dataset >100K giao dịch
   (`src/basket/market_basket.py`), có thể gây cảm giác treo trên hạ tầng cloud free-tier chậm hơn.
   Cân nhắc: sample transactions khi >N, hoặc điều chỉnh min_support thích ứng tốt hơn.
1. **[Ưu tiên cao]** Cơ chế theo dõi độ chính xác theo thời gian (forecast accuracy tracking):
   log mỗi lần dự báo (model, ngày, giá trị dự báo) vào `config/forecast_log/`, đối chiếu với dữ
   liệu thực tế khi có, tính lại WAPE, hiển thị biểu đồ xu hướng độ chính xác ở trang
   "11. Model & Độ tin cậy". Đây là cách "học hỏi liên tục" đúng nghĩa cho hệ thống dùng model cổ
   điển (không phải online learning thật).
2. Thêm test riêng cho LightGBM/CatBoost/Ensemble trong `tests/test_forecasting.py` (hiện chỉ test
   qua `get_candidate_models` gián tiếp).
3. Tối ưu tốc độ backtest: giảm `max_folds`, cache theo hash dữ liệu, hoặc chạy song song — xem
   `docs/nhat_ky_nang_cap.md` đợt #1 mục "Rủi ro hiệu năng".
4. Prophet như model tuỳ chọn (spec gốc có nhắc tới) — cần kiểm tra tương thích Python 3.14 trước
   khi thêm (đợt #1 chưa thử vì ưu tiên XGBoost/LightGBM/CatBoost trước).
5. Hierarchical forecasting reconciliation chính thức (MinT/bottom-up) giữa cấp Company/Category/SKU
   — hiện mỗi cấp dự báo độc lập, không đảm bảo tổng SKU khớp với dự báo Category.
6. Cơ chế phát hiện "drift" — cảnh báo khi hành vi bán hàng thay đổi bất thường so với giai đoạn
   backtest gần nhất (điểm người dùng cân nhắc nhưng chưa chọn ưu tiên ở đợt #1).

## Nhóm B — Tính năng App

1. Causal uplift modeling (causal forest/DML) khi dataset có đủ treatment/control — xem
   `docs/nghien_cuu_nen_tang.md` mục XVII. Cần dataset thật có lịch sử khuyến mãi phong phú để test.
2. Contextual Bandit để tối ưu phân bổ khuyến mãi theo thời gian thực (Priority 3 gốc).
3. PDF export cho báo cáo tổng hợp (hiện chỉ có CSV/Excel, xem trang Export Report).
4. Multi-tenant: chuyển Business Profile/Campaign Log từ JSON file sang SQLite, hỗ trợ nhiều doanh
   nghiệp dùng chung 1 instance (hiện mỗi máy cài riêng nên chưa cấp thiết, nhưng cần nếu SaaS hoá).
5. Tích hợp LLM thật (có hook sẵn ở `src/recommendation/campaign.py::is_llm_enabled`, chưa kích
   hoạt) để sinh nội dung marketing sinh động hơn — CHỈ gửi dữ liệu tổng hợp, không gửi transaction chi tiết.
6. Danh sách ngày lễ Việt Nam đầy đủ hơn (bao gồm Tết Âm lịch tính theo năm) trong
   `src/features/engineering.py::FIXED_VN_HOLIDAYS_MMDD`.
7. Cross-category spillover trong Market Basket Analysis (mục XIII gốc, hiện basket chỉ xét theo
   SKU, chưa xét ảnh hưởng chéo giữa category).
8. **[Mới]** Baseline theo ngày trong Campaign Monitor hiện chia đều (uniform) tổng dự báo cho số
   ngày — nên học pattern weekday/seasonality thật từ forecast thay vì chia đều đơn giản
   (`src/monitoring/campaign_monitor.py::build_daily_baseline`).
9. **[Mới]** Kết nối thật ít nhất 1 nguồn trong `src/external_signals/` hoặc `src/integrations/`
   (vd Google Trends — có thư viện `pytrends` miễn phí, dễ thử nghiệm nhất) để chứng minh kiến trúc
   hoạt động thật, không chỉ là stub.
10. **[Mới]** Test kỹ hơn `st.data_editor` ở Campaign Monitor với nhiều dòng dữ liệu thực tế liên
    tiếp (D+1 đến D+7) — phiên nâng cấp #2 chỉ test được 1 dòng qua browser tự động do giới hạn
    tương tác với canvas-grid.

---

## Đã hoàn thành

- **2026-09-21 (buổi tối)**: Mở rộng toàn diện thành PromotionPilot AI — Local Context, Execution
  Plan, Campaign Monitor, Alert Engine + AI Action, Campaign Learning Loop, External
  Signals/Integrations (stub kiến trúc), mục tiêu BRANDING, dataset Pharmacity demo, đa sheet Excel,
  ẩn/mã hoá CustomerID, deploy-ready. Chi tiết + bug đã sửa: `docs/nhat_ky_nang_cap.md` đợt #2.
- **2026-09-21**: [Nhóm A #hạng mục mới] Thêm LightGBM, CatBoost, XGBoost (kích hoạt thật), và
  Ensemble (Holt-Winters + Random Forest) vào bộ candidate model dự báo. Chi tiết:
  `docs/nhat_ky_nang_cap.md` đợt #1.
