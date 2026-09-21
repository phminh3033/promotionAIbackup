# PromoPilot AI

**AI Marketing & Demand Planning Copilot dành cho Doanh nghiệp vừa và nhỏ (SME)**

## 1. PromoPilot AI là gì?

PromoPilot AI là một ứng dụng web chạy local (không cần Cloud) giúp doanh nghiệp vừa và nhỏ tại
Việt Nam dùng dữ liệu bán hàng sẵn có (Excel/CSV xuất từ POS) để:

- Hiểu tình hình kinh doanh hiện tại (chất lượng dữ liệu, sản phẩm bán chạy, khách hàng).
- Dự báo nhu cầu, doanh thu, số giao dịch/khách hàng, nhu cầu tồn kho.
- Đề xuất số lượng hàng cần nhập (Inventory Planning).
- Mô phỏng nhiều kịch bản khuyến mãi (Discount, BOGO, Bundle, Gift...) và so sánh ROI.
- Đề xuất chương trình khuyến mãi phù hợp nhất với **mục tiêu kinh doanh** doanh nghiệp chọn
  (Kéo traffic / Tăng doanh thu / Tăng lợi nhuận / Giải phóng tồn kho).
- Sinh kế hoạch campaign cơ bản (nội dung Facebook/Zalo/SMS) — hoàn toàn rule-based, không cần API key.

Toàn bộ hệ thống được thiết kế theo nguyên tắc:

```
CORE AI ENGINE + BUSINESS CONFIGURATION + COMPANY DATA + BUSINESS CONSTRAINTS
= COMPANY-SPECIFIC RECOMMENDATION
```

Nghĩa là **không có một mô hình/đề xuất cố định** áp dụng giống nhau cho mọi doanh nghiệp — mọi
kết quả đều phụ thuộc vào dữ liệu, hồ sơ, và mục tiêu của chính doanh nghiệp bạn.

## 2. Use case

- Chủ cửa hàng/chuỗi bán lẻ nhỏ muốn biết "tuần sau nên nhập bao nhiêu hàng?"
- Marketing Manager muốn biết "nên giảm giá bao nhiêu % hay làm combo để có lợi nhất?"
- Sales/Operations Manager muốn biết "cần bao nhiêu nhân viên trực trong đợt khuyến mãi sắp tới?"
- Doanh nghiệp muốn thử nghiệm ý tưởng khuyến mãi trước khi triển khai thật, tránh giảm giá sâu
  làm lỗ mà không biết.

## 3. Cách cài Python

Cần **Python 3.10 trở lên** (đã kiểm thử với Python 3.14). Kiểm tra đã cài chưa:

```bash
python --version
```

Nếu chưa có, tải tại [python.org/downloads](https://www.python.org/downloads/) (khi cài, nhớ tick
"Add Python to PATH").

## 4. Tạo virtual environment

Từ thư mục gốc dự án (`promopilot-ai/`):

```bash
python -m venv .venv
```

Kích hoạt:

- Windows (PowerShell): `.venv\Scripts\Activate.ps1`
- Windows (cmd): `.venv\Scripts\activate.bat`
- macOS/Linux: `source .venv/bin/activate`

## 5. Cài đặt thư viện (pip install)

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 6. Cách chạy ứng dụng

Sinh dữ liệu demo (chỉ cần chạy 1 lần, hoặc bỏ qua nếu đã có `data/demo_sme_sales.csv`):

```bash
python scripts/generate_demo_data.py
```

Chạy ứng dụng:

```bash
streamlit run app.py
```

Trình duyệt sẽ tự mở tại `http://localhost:8501`. Bấm **"Dùng dữ liệu demo"** ở trang Tổng quan để
trải nghiệm nhanh toàn bộ tính năng, hoặc vào trang **1. Tải dữ liệu** để upload file thật.

## 7. Định dạng dữ liệu (Data Format)

Chấp nhận file **CSV** hoặc **Excel (.xlsx/.xls)**. Không yêu cầu tên cột cụ thể — hệ thống có
**Data Mapping Wizard** để bạn ánh xạ cột. Các trường dữ liệu:

**Bắt buộc tối thiểu:**

| Trường | Ý nghĩa |
|---|---|
| Ngày giao dịch (Date) | Ngày phát sinh đơn hàng |
| Mã sản phẩm (Product_ID) | Định danh SKU |
| Số lượng (Quantity) | Số lượng bán |
| Doanh thu (Revenue) | Thành tiền |

**Tuỳ chọn (càng nhiều càng mở thêm tính năng):** Mã giao dịch, Mã khách hàng, Mã cửa hàng, Danh
mục, Đơn giá, Giá vốn, Lợi nhuận gộp, Tồn kho, Mã/Loại khuyến mãi, Giảm giá, Ngày bắt đầu/kết thúc
khuyến mãi.

Hệ thống **không crash** nếu thiếu trường tuỳ chọn — module liên quan sẽ tự tắt và giải thích rõ lý do.

## 8. Data Mapping (ánh xạ cột)

Ở trang **1. Tải dữ liệu**, hệ thống tự động gợi ý cột nào tương ứng với trường nào (dựa trên tên
cột, hỗ trợ cả tiếng Việt có dấu và tiếng Anh). Bạn xác nhận hoặc chỉnh sửa lại trước khi áp dụng.

## 9. Các mô hình được sử dụng

**Dự báo (Auto Model Selection):** Naive, Seasonal Naive, Moving Average, Exponential Smoothing,
Holt-Winters, Random Forest, Gradient Boosting, XGBoost, LightGBM, CatBoost, và Ensemble
(Holt-Winters + Random Forest). Các model boosting (XGBoost/LightGBM/CatBoost) tự bỏ qua nếu chưa
cài thư viện tương ứng — không crash. Hệ thống tự backtest (time-series rolling-origin split) và
chọn mô hình có WAPE thấp nhất — xem chi tiết ở trang **11. Model & Độ tin cậy** và
`docs/nghien_cuu_nen_tang.md`.

> **Lưu ý hiệu năng:** càng nhiều model ứng viên, thời gian backtest càng lâu (~2 lần so với bộ 7
> model ban đầu, đo trên dữ liệu demo ~45s cho 1 lượt dự báo công ty). Đây là đánh đổi có chủ đích
> để tối đa độ chính xác; UI có hiển thị trạng thái xử lý (`st.status`) để người dùng không cảm
> thấy app bị treo. Xem `docs/nhat_ky_nang_cap.md` để biết định hướng tối ưu tốc độ trong tương lai.

**Khách hàng:** RFM + K-Means (tự chọn số cụm qua silhouette score).

**Giỏ hàng:** FP-Growth + Association Rules (thư viện `mlxtend`).

**Khuyến mãi:** Hybrid Rule-based Engine (business rules) + giả định elasticity theo cơ chế
(assumption, có gắn nhãn rõ ràng) + uplift từ lịch sử thật (nếu dataset có lịch sử khuyến mãi đủ dữ
liệu) — **không dùng LLM để quyết định khuyến mãi**.

## 10. Input tối thiểu vs. Input tốt nhất

| | Input tối thiểu | Input tốt nhất |
|---|---|---|
| Bắt buộc có | Ngày, Mã SP, Số lượng, Doanh thu | + Mã giao dịch, Mã khách hàng, Giá vốn, Tồn kho, Lịch sử khuyến mãi |
| Modules hoạt động | Dự báo cơ bản, Xếp hạng sản phẩm | Toàn bộ 11 module (RFM, Basket, Inventory, Historical uplift...) |
| Độ tin cậy | Thấp–Trung bình (đặc biệt nếu <60 ngày dữ liệu) | Cao hơn với ≥1 năm dữ liệu |

## 11. Limitations (Giới hạn của MVP)

- **Không phải causal inference thật**: uplift khuyến mãi dựa trên giả định elasticity hoặc so
  sánh lịch sử đơn giản (pre/post theo weekday), KHÔNG kiểm soát confounder — không dùng để ra
  quyết định tài chính lớn mà không thẩm định thêm.
- **Không có Contextual Bandit / Reinforcement Learning** để tối ưu khuyến mãi theo thời gian thực
  (Priority 3 — chưa triển khai trong MVP).
- **Không tích hợp dữ liệu bên ngoài** (thời tiết, đối thủ real-time) — chỉ nhập thủ công sự kiện.
- **Chưa có hierarchical forecasting reconciliation** chính thức (MinT...) giữa các cấp SKU/Category/Company.
- **Ngày lễ Việt Nam** trong feature engineering là danh sách rút gọn, chưa tính Tết Âm lịch biến động theo năm.
- **Dữ liệu quá ít (<14 ngày)** sẽ chỉ dùng model Naive và cảnh báo độ tin cậy Thấp.

## 12. Cách Pilot cho doanh nghiệp

Xem chi tiết quy trình 5 ngày tại [`docs/huong_dan_pilot.md`](docs/huong_dan_pilot.md).

## 13. Data Privacy

- Toàn bộ ứng dụng chạy **local** trên máy bạn — không có bước upload dữ liệu lên server bên ngoài.
- Nếu bật tích hợp LLM (tuỳ chọn, cấu hình trong `.env`, mặc định **tắt**), hệ thống **chỉ gửi số
  liệu tổng hợp** (aggregated summary) để sinh nội dung marketing — **không bao giờ gửi dữ liệu
  giao dịch chi tiết (transaction-level)** cho bất kỳ API bên ngoài nào.
- Không hard-code API key trong mã nguồn; cấu hình qua `.env` (xem `.env.example`).

## Cấu trúc thư mục

```
promopilot-ai/
  app.py                  # Điểm khởi chạy, định nghĩa navigation
  pages/                  # Các trang Streamlit (0-11)
  src/
    data/                 # loader, mapper, quality, schema
    features/             # feature engineering cho time series
    forecasting/          # models, backtest, auto model selection
    segmentation/         # RFM, K-Means
    basket/                # market basket analysis
    inventory/             # inventory planning
    promotion/             # mechanics, business rules, simulator
    optimization/          # objective functions (Traffic/Revenue/Profit/Clearance)
    roi/                   # ROI calculator
    recommendation/        # recommendation engine, timing, campaign generator
    explainability/        # giải thích bằng ngôn ngữ kinh doanh
    business/              # business profile onboarding
    utils/                 # session state helpers
  config/                  # business profiles đã lưu (tự tạo khi chạy)
  data/                    # demo_sme_sales.csv
  scripts/                 # generate_demo_data.py, smoke_test_pipeline.py
  tests/                   # pytest
  docs/                    # nghien_cuu_nen_tang.md, huong_dan_pilot.md
```

## Chạy test

```bash
pytest
```

## Giấy phép / Liên hệ

Dự án MVP nội bộ — vui lòng liên hệ nhóm phát triển để biết thêm chi tiết triển khai thực tế.
