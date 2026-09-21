# Nhật ký nâng cấp PromoPilot AI

File này ghi lại lịch sử từng đợt nâng cấp (do người dùng yêu cầu trực tiếp, hoặc do Skill
`nang-cap-promopilot` tự động thực hiện định kỳ). Mục đích: bất kỳ ai (người hoặc AI session sau)
đọc lại có thể hiểu **đã thử gì, kết quả ra sao, và nên làm gì tiếp theo** — tránh lặp lại công
sức hoặc đưa ra quyết định mâu thuẫn với các đợt trước.

Mỗi mục cần có: Ngày, Người/Agent thực hiện, Mục tiêu, Thay đổi, Kết quả kiểm thử, Bài học/Đề xuất tiếp theo.

---

## 2026-09-21 — Mở rộng bộ model dự báo (đợt nâng cấp #1)

**Thực hiện bởi:** Phiên làm việc trực tiếp với người dùng (chưa phải Skill tự động).

**Mục tiêu:** Theo yêu cầu người dùng — "mô hình dự báo nên học hỏi và phát triển liên tục để đảm
bảo dữ liệu dự báo chính xác", ưu tiên đã chọn: **thêm nhiều thuật toán dự báo mới**.

**Thay đổi:**
- Thêm 4 model ứng viên mới vào `src/forecasting/models.py`: `LightGBMModel`, `CatBoostModel`
  (cả hai theo pattern optional-import giống `XGBoostModel` đã có), và `EnsembleStatMLModel`
  (trung bình cộng Holt-Winters + Random Forest).
- Bật `XGBoostModel` thật sự lần đầu (trước đó có code nhưng chưa cài `xgboost` nên luôn bị bỏ qua).
- Cập nhật `requirements.txt` thêm `xgboost`, `lightgbm`, `catboost` (optional nhưng khuyến nghị).
- Cập nhật `src/forecasting/selector.py` phần giải thích lựa chọn model để bao quát tên model mới.
- Cập nhật `README.md` và `docs/nghien_cuu_nen_tang.md` mục 3.5.

**Kết quả kiểm thử:**
- `pytest`: 41/41 pass (không có test mới riêng cho từng model boosting cụ thể — TODO cho đợt sau).
- `scripts/smoke_test_pipeline.py`: chạy thành công, forecast công ty vẫn chọn Random Forest
  (WAPE 20.06%, không đổi so với trước khi thêm model — không model mới nào thắng trên dataset demo).
- Thời gian chạy smoke test tăng từ ~21s lên ~45s (do backtest nhiều model hơn).

**Bài học / Đề xuất cho đợt nâng cấp tiếp theo:**
1. **Chưa làm**: chưa thêm test riêng (`tests/test_forecasting.py`) xác nhận LightGBM/CatBoost/
   Ensemble hoạt động đúng khi được cài — nên bổ sung.
2. **Rủi ro hiệu năng**: nếu tiếp tục thêm model, cân nhắc: (a) giảm `max_folds` xuống 2 cho các
   model chậm, (b) cache kết quả backtest theo hash(dữ liệu + tham số) để tránh chạy lại khi user
   bấm "Chạy dự báo" nhiều lần với cùng dữ liệu, (c) chạy backtest song song (multiprocessing) —
   chưa làm vì MVP ưu tiên đơn giản.
3. **Chưa làm — cơ chế theo dõi độ chính xác theo thời gian** (accuracy tracking): người dùng đã
   được hỏi và chọn ưu tiên "thêm thuật toán" thay vì "theo dõi độ chính xác" ở đợt này — nhưng đây
   vẫn là hạng mục giá trị cao cho các đợt sau (log dự báo → đối chiếu thực tế → biểu đồ WAPE theo
   thời gian). Nên đề xuất lại trong đợt nâng cấp kế tiếp.
4. **Máy dev ban đầu thiếu Git và GitHub CLI** — đã cài Git qua `winget install --id Git.Git`.
   Nếu môi trường CI/cloud khác cũng thiếu, cân nhắc kiểm tra trước khi chạy các lệnh git.
5. Nên thử nghiệm model mới trên **nhiều dataset khác nhau** (không chỉù demo), vì kết quả "Random
   Forest vẫn thắng" có thể chỉ đúng với đặc điểm riêng của dữ liệu demo (69 SKU, seasonality vừa
   phải) — dataset khác (nhiều SKU hơn, seasonality phức tạp hơn) có thể cho kết quả khác.
