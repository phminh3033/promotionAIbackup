---
name: nang-cap-promopilot
description: Quy trình nâng cấp định kỳ, có hệ thống cho ứng dụng PromoPilot AI (Streamlit app dự báo nhu cầu/doanh thu + đề xuất khuyến mãi cho SME, nằm trong project này). Dùng skill này bất cứ khi nào người dùng yêu cầu "nâng cấp", "cải thiện", "phát triển thêm", "làm cho chính xác hơn" PromoPilot AI hoặc mô hình dự báo của nó — kể cả khi họ không gọi thẳng tên skill. Cũng là skill được một cloud routine gọi tự động hàng tuần để tự nghiên cứu và nâng cấp app mà không cần giám sát trực tiếp — vì vậy PHẢI tuân thủ nghiêm ngặt các giới hạn an toàn trong phần "Ranh giới quan trọng" bên dưới.
---

# Nâng cấp PromoPilot AI

PromoPilot AI là app dự báo cổ điển (Random Forest, Holt-Winters, XGBoost...), không phải mô hình
online-learning tự học thật sự. "Nâng cấp liên tục để đảm bảo dự báo chính xác" ở đây nghĩa là một
vòng lặp MLOps trung thực: mỗi lần chạy skill này, chọn **một** hạng mục cải tiến có phạm vi vừa
đủ, làm trọn vẹn (code + test + docs), rồi dừng lại — không cố làm nhiều việc nửa vời trong 1 lượt.

Vì sao làm từng bước nhỏ: skill này có thể chạy không giám sát (cloud routine hàng tuần). Một thay
đổi nhỏ, có test, dễ review/rollback luôn an toàn hơn một đợt tái cấu trúc lớn không ai kiểm tra kịp.

## Quy trình (làm tuần tự, đừng bỏ bước)

### 1. Đọc bối cảnh trước khi làm gì cả

- Đọc `docs/backlog_tinh_nang.md` — danh sách hạng mục ưu tiên, chia Nhóm A (mô hình dự báo) và
  Nhóm B (tính năng App). Chọn **đúng 1 hạng mục** chưa nằm trong mục "Đã hoàn thành", ưu tiên
  hạng mục xếp trước trong danh sách trừ khi có lý do rõ ràng để chọn khác (giải thích lý do đó).
- Đọc `docs/nhat_ky_nang_cap.md` — lịch sử các đợt nâng cấp trước. Đừng lặp lại việc đã làm, đừng
  đi ngược lại quyết định trước đó mà không có lý do mới. Chú ý phần "Bài học / Đề xuất tiếp theo"
  của đợt gần nhất — thường đã gợi ý sẵn việc nên làm kế tiếp.
- Đọc `docs/nghien_cuu_nen_tang.md` để hiểu quy ước LITERATURE / ASSUMPTION / BUSINESS RULE đang
  dùng xuyên suốt codebase — mọi thay đổi logic nghiệp vụ mới đều phải gắn nhãn rõ theo quy ước này.

### 2. Research nếu cần (chỉ khi hạng mục đòi hỏi kiến thức mới)

Nếu hạng mục liên quan tới thêm thuật toán/kỹ thuật forecasting mới, dùng WebSearch tìm paper/tài
liệu kỹ thuật đáng tin cậy (ưu tiên 1-2 năm gần đây). Không bịa citation — nếu không tìm được nguồn
xác thực, ghi rõ đó là suy luận/assumption của bạn, không phải kết luận từ paper. Cập nhật
`docs/nghien_cuu_nen_tang.md` với format sẵn có trong file (Paper/Năm/Journal/DOI/Phương pháp/Ý
nghĩa/Áp dụng vào MVP).

### 3. Implement — theo đúng convention hiện có

Đọc qua 1-2 file tương tự trong `src/` (vd `src/forecasting/models.py` cho model mới,
`src/promotion/` cho business rule mới) trước khi viết code mới, để bám đúng style. Các nguyên tắc
bất di bất dịch của toàn bộ codebase này (xem thêm README.md và các file src/ hiện có):

- Toàn bộ text hiển thị cho người dùng bằng **tiếng Việt**.
- Không hard-code recommendation/kết quả — mọi output phải tính từ dữ liệu đầu vào thực tế.
- Không dùng LLM để quyết định logic nghiệp vụ (promotion, forecast...) — LLM chỉ sinh nội dung
  marketing/giải thích (xem `src/recommendation/campaign.py`).
- Không crash khi dữ liệu thiếu field optional — luôn có fallback + thông báo rõ ràng bằng tiếng Việt
  (xem cách `src/data/schema.py::DatasetCapabilities` bật/tắt module theo dữ liệu).
- Thêm model dự báo mới: theo pattern optional-import + `_MLRecursiveModel` trong
  `src/forecasting/models.py` (xem cách `LightGBMModel`/`CatBoostModel` đã làm — import trong
  try/except, không làm cả app lỗi nếu thư viện chưa cài).
- Mọi ngưỡng/quy tắc tự đặt (không có cơ sở khoa học trực tiếp) phải ghi chú `[BUSINESS RULE]` hoặc
  `[ASSUMPTION cho MVP]` ngay trong docstring/comment, giải thích lý do chọn.

### 4. Kiểm thử — bắt buộc trước khi coi là xong

```bash
pytest -q
python scripts/smoke_test_pipeline.py
```

Cả hai phải chạy không lỗi. Nếu thêm model/logic mới, thêm test tương ứng trong `tests/` (xem
`tests/test_forecasting.py`, `tests/test_roi.py` làm ví dụ — test phải xác nhận công thức/kết quả
bằng số cụ thể, không chỉ "chạy không crash").

Nếu pytest fail và không sửa được trong phiên này: **revert thay đổi** (`git checkout -- <file>`
hoặc `git restore`) thay vì để lại trạng thái lỗi, rồi ghi lại trong nhật ký nâng cấp là đã thử và
tại sao chưa thành công — để đợt sau biết mà tránh hoặc tiếp tục từ đó.

### 5. Ghi lại — để đợt sau không phải đoán mò

- Cập nhật `docs/backlog_tinh_nang.md`: chuyển hạng mục vừa hoàn thành sang mục "Đã hoàn thành"
  kèm ngày. Nếu phát hiện hạng mục mới đáng làm trong lúc thực hiện, thêm vào backlog (đừng làm
  luôn nếu nó vượt phạm vi đợt này).
- Thêm 1 mục mới vào `docs/nhat_ky_nang_cap.md` theo đúng format đã có: **Ngày, Người/Agent thực
  hiện, Mục tiêu, Thay đổi, Kết quả kiểm thử, Bài học/Đề xuất tiếp theo**. Phần "Kết quả kiểm thử"
  phải nêu con số cụ thể (bao nhiêu test pass, thời gian chạy, model nào thắng...), không viết
  chung chung kiểu "đã test xong".

### 6. Commit (chỉ local — xem ranh giới ở dưới)

```bash
git add -A
git commit -m "Nâng cấp: <mô tả ngắn hạng mục đã làm>"
```

Chỉ commit sau khi bước 4 (kiểm thử) đã pass. Message commit ngắn gọn, mô tả đúng hạng mục đã làm
(vd "Nâng cấp: thêm cơ chế theo dõi độ chính xác dự báo theo thời gian").

### 7. Tóm tắt kết thúc

Kết thúc bằng một đoạn tóm tắt ngắn: đã chọn hạng mục nào và vì sao, đã thay đổi gì, kết quả test,
và 1-2 gợi ý cho đợt tiếp theo (đã ghi trong nhật ký thì nhắc lại ngắn gọn ở đây cho người đọc
transcript không cần mở file).

## Ranh giới quan trọng — đọc kỹ nếu đang chạy không giám sát (cloud routine)

- **Không bao giờ push lên GitHub nếu đây là phiên chạy local trên máy người dùng.** Chỉ cloud
  routine (chạy trong môi trường CCR clone riêng từ GitHub) mới được `git push`. Nếu không chắc
  đang chạy ở đâu, mặc định coi là local và KHÔNG push — chỉ commit cục bộ, để người dùng tự đẩy
  lên khi họ đã xem qua thay đổi (`git log`, `git diff`).
- **Không tự quyết định thay đổi kiến trúc lớn** mà backlog/người dùng chưa yêu cầu rõ: đổi
  database (SQLite → thứ khác), đổi framework UI (Streamlit → thứ khác), thêm phụ thuộc bắt buộc
  vào dịch vụ cloud trả phí, đổi cấu trúc thư mục `src/`. Những việc này cần con người quyết định
  trước, không phải việc để tự động hoá.
- **Chỉ làm 1 hạng mục mỗi lần chạy.** Đừng cố nhồi nhiều thay đổi không liên quan vào cùng 1 commit
  — mỗi lần chạy skill là một đơn vị công việc độc lập, dễ review, dễ rollback riêng lẻ.
- **Không tắt/bỏ qua test để "cho xong việc".** Nếu một thay đổi không thể làm cho pytest pass
  trong phạm vi hợp lý của 1 phiên, thà revert và ghi lại bài học còn hơn để lại code lỗi.
- **Không âm thầm đổi các con số/ngưỡng đã có** (min_margin, safety_stock_days, ngưỡng Data Quality
  Score...) trừ khi hạng mục đang làm chính là về ngưỡng đó — các con số này ảnh hưởng trực tiếp
  đến quyết định kinh doanh thật của doanh nghiệp dùng app.
- **Không claim causal uplift hay độ chính xác mà chưa được backtest chứng minh** — giữ nguyên tinh
  thần "LITERATURE vs ASSUMPTION vs BUSINESS RULE" đã có trong toàn bộ codebase.
