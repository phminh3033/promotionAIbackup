# Nhật ký nâng cấp PromoPilot AI

File này ghi lại lịch sử từng đợt nâng cấp (do người dùng yêu cầu trực tiếp, hoặc do Skill
`nang-cap-promopilot` tự động thực hiện định kỳ). Mục đích: bất kỳ ai (người hoặc AI session sau)
đọc lại có thể hiểu **đã thử gì, kết quả ra sao, và nên làm gì tiếp theo** — tránh lặp lại công
sức hoặc đưa ra quyết định mâu thuẫn với các đợt trước.

Mỗi mục cần có: Ngày, Người/Agent thực hiện, Mục tiêu, Thay đổi, Kết quả kiểm thử, Bài học/Đề xuất tiếp theo.

---

## 2026-09-21 (buổi tối) — Mở rộng thành PromotionPilot AI (đợt nâng cấp #2)

**Thực hiện bởi:** Phiên làm việc trực tiếp với người dùng (yêu cầu mở rộng lớn, không phải Skill tự động).

**Mục tiêu:** Người dùng đưa ra spec mở rộng toàn diện (~53 mục) đổi tên sản phẩm thành
"PromotionPilot AI", thêm Local Context, Execution Plan, Campaign Monitor, Alert Engine, AI Action
(Continue/Adjust/Stop/Scale), Campaign Learning Loop, External Signals/Integrations stub, mục tiêu
BRANDING, demo dataset Pharmacity-style, deploy-ready cho cloud.

**Thay đổi chính:**
- **Module mới (logic thật, có test)**: `src/context/local_context.py`, `src/execution/plan.py`,
  `src/monitoring/campaign_monitor.py`, `src/alerts/engine.py`, `src/learning/campaign_log.py`.
- **Module stub kiến trúc-sẵn-sàng (đúng yêu cầu spec, không fake data)**:
  `src/external_signals/{social_listener,weather,competitor,google_trends,events}.py`,
  `src/integrations/{pos_api,webhook,event_stream,inventory_sync,customer_sync}.py`.
- Thêm mục tiêu kinh doanh thứ 5: **BRANDING** (`src/optimization/objective.py`).
- Mở rộng `BusinessProfile`: `min_roi_pct`, `max_campaign_duration_days`, `mask_customer_id`.
- Thêm `config/business_rules.yaml` + `BusinessProfile.with_yaml_defaults()`.
- Mở rộng `src/data/loader.py` hỗ trợ Excel đa sheet (`list_excel_sheets`, `sheet_name` param).
- Mở rộng `src/data/mapper.py`: tách camelCase (`TransactionID` -> `Transaction ID`) để nhận diện
  tên cột tiếng Anh kiểu POS/ERP quốc tế.
- Thêm `src/utils/privacy.py` (hash CustomerID khi hiển thị/export).
- Dataset demo mới: `scripts/generate_pharmacity_demo.py` → `data/pharmacity_demo.csv` (~360.000
  dòng, 6 tháng, 43 SKU, 30% thiếu CustomerID, AOV ~500K, 3.4 items/txn) +
  `data/mau_du_lieu_promotionpilot.xlsx` (file mẫu 3 sheet).
- 6 trang UI mới: Local Context, Execution Plan (gộp campaign content generator cũ), Campaign
  Monitor, Alerts, Export Report; rebrand trang chủ + toàn bộ navigation (16 trang).
- Cập nhật README.md toàn diện (deploy Streamlit Cloud/Render/Railway, integration roadmap Level 1-4).

**Bug thật phát hiện và sửa trong lúc test qua browser (không phải lý thuyết):**
1. `BusinessProfile.with_yaml_defaults()` đọc YAML suy luận int cho `service_capacity_per_staff_per_hour: 8`
   (thay vì float) → `StreamlitMixedNumericTypesError` khi mở trang Mục tiêu kinh doanh. Sửa: ép
   kiểu tường minh trong loader + defensive cast tại nơi dùng widget.
2. **Bug logic quan trọng**: kịch bản "tốt nhất" ở trang Kịch bản Promotion được chọn ĐỘC LẬP với
   kết quả Business Rules — có thể đề xuất một mechanic mà chính Business Rules đã đánh giá
   "rejected" (vd hết hàng). Sửa: tính Business Rules TRƯỚC khi mô phỏng, gắn cờ `bi_tu_choi` vào
   bảng kịch bản, loại các mechanic bị reject khỏi lựa chọn "tốt nhất" (áp dụng cả ở trang Kịch bản
   Promotion và trang AI Recommendation).
3. Dataset demo ban đầu: SKU bán chạy nhất (Pareto-distributed popularity) luôn cạn hàng phi thực
   tế vì tồn kho ban đầu không tỷ lệ với tốc độ bán. Sửa: tồn kho/mục tiêu tái nhập tỷ lệ theo
   popularity SKU + rút ngắn chu kỳ kiểm tra tái nhập (18→10 ngày, ngưỡng 25%→40%). Kết quả: % SKU
   có <5 ngày tồn kho giảm từ 30% xuống 11.6%.
4. AI Action reasons có thể nói "ROI vẫn đạt mục tiêu" ngay cả khi ROI thực tế là N/A (thiếu dữ
   liệu GP) — sửa câu chữ cho chính xác với trường hợp thiếu dữ liệu.

**Kết quả kiểm thử:**
- `pytest`: 61/61 pass (thêm `tests/test_alerts.py`, `test_execution_plan.py`,
  `test_campaign_monitor.py`, `test_business_profile.py`).
- Test qua browser thật (Claude Browser): toàn bộ luồng UNDERSTAND → FORECAST → PREPARE → SIMULATE
  → DECIDE → EXECUTE → MONITOR & LEARN chạy được với dữ liệu Pharmacity demo, dùng đúng use case
  chính của spec (Local Context "Đối thủ mở cửa hàng gần đây" → gợi ý TRAFFIC → BOGO/Bundle →
  Execution Plan → Campaign Monitor (+113% doanh thu thực tế nhập tay, khớp toán học) → Alerts
  (SCALE recommendation).
- Forecast: Holt-Winters, WAPE 9.9%, độ tin cậy Cao trên dataset mới.
- Không có Uncaught exception mới nào trong log server sau khi sửa các bug trên.

**Bài học / Đề xuất cho đợt nâng cấp tiếp theo:**
1. Vẫn cần cơ chế theo dõi độ chính xác dự báo theo thời gian (Nhóm A #1 trong backlog) — chưa làm.
2. Tối ưu tốc độ Market Basket Analysis (30-50s trên >100K giao dịch) — cân nhắc sample transaction
   hoặc giới hạn min_support thông minh hơn khi dataset lớn.
3. Baseline theo ngày trong Campaign Monitor đang chia đều (uniform) — nên học pattern theo
   weekday/seasonality từ forecast thay vì chia đều đơn giản.
4. Chưa test kỹ giao diện `st.data_editor` (Campaign Monitor nhập actual data) qua nhiều dòng liên
   tiếp — chỉ test 1 dòng qua browser tự động do giới hạn tương tác canvas-grid; nên có người dùng
   thật test thêm.
5. README/docs đã ghi rõ quyết định giảm demo dataset từ 24 tháng xuống 6 tháng — nếu người dùng
   muốn dữ liệu đầy đủ 24 tháng cho pitch thật, có thể chỉnh `N_DAYS` trong
   `scripts/generate_pharmacity_demo.py` (đã tham số hoá sẵn), chấp nhận thời gian sinh/tải lâu hơn.

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
