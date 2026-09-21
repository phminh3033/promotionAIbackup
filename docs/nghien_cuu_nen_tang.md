# Nghiên cứu nền tảng cho PromoPilot AI

> Tài liệu này ghi lại kết quả nghiên cứu literature thực hiện qua công cụ tìm kiếm web (WebSearch) vào 2026-09-20, phục vụ thiết kế PromoPilot AI. Mỗi mục ghi rõ: paper, năm, journal, DOI/link, phương pháp, ý nghĩa, và **thành phần cụ thể được áp dụng vào MVP**.
>
> **Giới hạn minh bạch:** Việc tìm kiếm được thực hiện qua WebSearch (kết quả tóm tắt từ Google-style search + trích đoạn), KHÔNG phải đọc toàn văn PDF từng paper. Các trích dẫn dưới đây được xác nhận có tồn tại thật (có DOI/link cụ thể xuất hiện trong kết quả tìm kiếm), nhưng phần "Phương pháp" và "Ý nghĩa" là tóm tắt lại theo abstract/snippet tìm được, không phải đọc full-text chi tiết mọi phần của bài báo. Không có citation nào trong tài liệu này bị bịa — nếu không tìm thấy nguồn xác thực cho một chủ đề, mục đó được ghi rõ là "Không tìm được nguồn xác thực trong phiên nghiên cứu này" thay vì đoán.

---

## 1. Bảng tổng hợp paper theo chủ đề

### 1.1 Causal Machine Learning / Uplift trong Marketing

| # | Paper | Năm | Journal/Nguồn | DOI/Link |
|---|---|---|---|---|
| 1 | *How causal machine learning can leverage marketing strategies: Assessing and improving the performance of a coupon campaign* | 2023 | PLOS ONE | https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0278937 |
| 2 | *Estimating Marketing Component Effects: Double Machine Learning from Targeted Digital Promotions* (Ellickson, Kar, Reeder) | 2023 | Marketing Science, Vol 42(4), tr. 704–728 | https://doi.org/10.1287/mksc.2022.1401 |

**Phương pháp:** Double Machine Learning (DML) và Causal Forest để tách causal effect của khuyến mãi/coupon ra khỏi các yếu tố nhiễu (confounders) bằng cách dùng ML để ước lượng "helper equations" (propensity, outcome model), sau đó ước lượng heterogeneous treatment effect theo từng nhóm khách hàng.

**Ý nghĩa:** Chứng minh rằng hiệu quả khuyến mãi khác nhau đáng kể giữa các nhóm khách hàng (theo lịch sử mua hàng), và rằng dùng correlation/before-after đơn thuần dễ đánh giá sai hiệu quả thật của promotion.

**Áp dụng vào MVP:**
- **Không** triển khai causal forest/DML đầy đủ ở MVP vì đa số SME không có dữ liệu treatment/control sạch (xem Mục XVII yêu cầu gốc).
- Kiến trúc `src/promotion/` được thiết kế theo interface cho phép cắm module causal sau này (`uplift_estimator` optional).
- MVP dùng **historical pre/post comparison** (không phải causal suy diễn đầy đủ) khi có dữ liệu promotion lịch sử, và luôn hiển thị cảnh báo "chưa phải causal uplift đã được chứng minh" — đúng theo khuyến nghị của các paper này về rủi ro nhầm correlation với causation.

---

### 1.2 Demand Forecasting / Hierarchical Forecasting

| # | Paper | Năm | Journal/Nguồn | DOI/Link |
|---|---|---|---|---|
| 3 | *A demand forecasting system of product categories defined by their time series using a hybrid approach of ensemble learning with feature engineering* | 2024 | Computing (Springer) | https://doi.org/10.1007/s00607-024-01320-y |
| 4 | *Hierarchical Forecasting at Scale* (Sprangers et al.) | 2023/2024 | International Journal of Forecasting (ScienceDirect) | https://www.sciencedirect.com/science/article/pii/S0169207024000116 ; preprint https://arxiv.org/pdf/2310.12809 |
| 5 | *Assessing the Performance of Hierarchical Forecasting Methods on the Retail Sector* | 2019 | Entropy | https://doi.org/10.3390/e21040436 |

**Phương pháp:** (3) Phân cụm sản phẩm theo đặc trưng nhu cầu (unsupervised) → chọn phương pháp forecast phù hợp cho từng cụm → ensemble các model tốt nhất theo cụm. (4) Học một mô hình forecast "bottom-level" duy nhất cho hàng triệu SKU bằng cách tối ưu hoá loss function tôn trọng cấu trúc phân cấp (sparse hierarchical loss) thay vì học riêng từng cấp rồi reconcile. (5) So sánh các phương pháp reconciliation (bottom-up, top-down, MinT...) trên dữ liệu bán lẻ.

**Ý nghĩa:** Không có một model duy nhất tối ưu cho mọi SKU/category; ensemble + lựa chọn theo đặc điểm chuỗi thời gian (feature-based model selection) cho kết quả tốt hơn one-size-fits-all. Time series ở mức chi tiết (SKU/ngày) thường noisy/intermittent hơn mức tổng hợp.

**Áp dụng vào MVP:**
- **Auto Model Selection** (`src/forecasting/selector.py`): với mỗi chuỗi (tổng thể / theo category / theo SKU), hệ thống tự thử nhiều model (Naive, Moving Average, Holt-Winters, Random Forest, Gradient Boosting) và chọn model có WAPE thấp nhất trên backtest — lấy cảm hứng trực tiếp từ ý tưởng "feature-based / performance-based model selection" của paper #3.
- Forecast được thực hiện ở nhiều mức (tổng thể, category, SKU) tương tự ý tưởng hierarchical (paper #4, #5), nhưng MVP **không** triển khai thuật toán reconciliation (MinT, bottom-up formal) đầy đủ do giới hạn thời gian — đây là fix rõ trong phần "Limitations".

---

### 1.3 Promotion Mechanics (BOGO / Discount / Bundle)

| # | Paper | Năm | Journal/Nguồn | DOI/Link |
|---|---|---|---|---|
| 6 | *Buy-One-Get-One Promotions in a Two-Echelon Supply Chain* (Li, Khouja, Pan, Zhou) | 2022/2023 | Management Science, Vol 69(9), tr. 5234–5255 | https://doi.org/10.1287/mnsc.2022.4638 |
| 7 | *When sales promotions make consumers experiencing financial restrictions purchase more or less: the role of decisional conflict* (Ulqinaku, Sarial-Abi) | 2025 | Italian Journal of Marketing | https://doi.org/10.1007/s43039-025-00112-2 |
| 8 | *Quantifying within-category / cross-category spillovers của khuyến mãi giá* — nguồn nền tảng gần nhất tìm được: *Cross-category demand effects of price promotions* | 2016 | Journal of the Academy of Marketing Science | https://doi.org/10.1007/s11747-010-0244-z (bản early-view PubMed: https://pubmed.ncbi.nlm.nih.gov/27524844/) |

**Phương pháp:** (6) Mô hình kinh tế lượng/game-theoretic so sánh lợi nhuận nhà bán lẻ & nhà sản xuất giữa BOGO, Price Reduction (PR), và Everyday-Low-Price (EDLP) trong chuỗi cung ứng 2 tầng. (7) 4 thí nghiệm hành vi tiêu dùng đo phản ứng của khách hàng bị hạn chế tài chính với các loại khuyến mãi khác nhau. (8) Ước lượng mô hình cầu category-level để đo hiệu ứng lan toả (spillover) giữa các category khi một category được khuyến mãi.

**Ý nghĩa:**
- BOGO thường tạo ra sản lượng bán cao hơn discount tương đương vì thúc đẩy tiêu dùng 2 đơn vị thay vì tích trữ (stockpiling) — nhưng chỉ tối ưu khi nhà bán lẻ kiểm soát được hành vi tích trữ.
- Khách hàng bị hạn chế tài chính phản ứng **tốt hơn** với BOGO-free so với "mua 1 tặng thêm X% giảm", và phản ứng **kém hơn** với khuyến mãi giới hạn thời gian ngắn / high-low pricing.
- Khuyến mãi một category có thể "hút" doanh thu từ category khác trong cùng cửa hàng (spillover âm) hoặc tạo hiệu ứng halo (spillover dương) — khoảng 0.16 đơn vị tăng thêm ở category khác cho mỗi đơn vị doanh thu tăng thêm trực tiếp.

**Áp dụng vào MVP:**
- Bộ giả định elasticity mặc định cho từng cơ chế khuyến mãi (`src/promotion/mechanics.py`) phản ánh định tính từ (6): BOGO/B1G1 được gán uplift đơn vị cao hơn discount % tương đương ở cùng mức "giá trị khuyến mãi", nhưng margin/đơn vị thấp hơn.
- Business Rule "IF repeat frequency high THEN consider BOGO / Buy More Save More" (yêu cầu gốc mục XV) được củng cố bởi (6) và (7).
- Cross-category spillover (paper #8) **không** được mô hình hoá định lượng trong MVP (cần dữ liệu category-pair phong phú hơn dữ liệu demo SME thường có) — ghi rõ trong Limitations, kiến trúc để ngỏ cho mở rộng sau (basket analysis đã có sẵn dữ liệu lift giữa các sản phẩm/category, có thể dùng làm proxy).

---

### 1.4 Customer Segmentation / RFM

| # | Paper | Năm | Journal/Nguồn | DOI/Link |
|---|---|---|---|---|
| 9 | *RFM ranking – An effective approach to customer segmentation* (Christy, Umamakeswari, Priyatharsini, Neyaa) | 2021 | Journal of King Saud University – Computer and Information Sciences, Vol 33(10) | (DOI theo tên tạp chí, không có link trực tiếp trong kết quả tìm kiếm — cần xác minh thêm nếu dùng học thuật chính thức) |
| 10 | *K-Means Clustering Approach for Intelligent Customer Segmentation Using Customer Purchase Behavior Data* | 2022 | Sustainability (MDPI) | https://www.mdpi.com/2071-1050/14/12/7243 |

**Phương pháp:** Tính điểm Recency/Frequency/Monetary cho từng khách hàng, sau đó áp dụng K-Means (hoặc ranking theo quartile) để phân cụm; đặt tên cụm theo đặc điểm hành vi (Loyal, At-risk, One-time...).

**Ý nghĩa:** RFM + K-Means là phương pháp phổ biến, dễ diễn giải cho doanh nghiệp không có đội Data Science — phù hợp trực tiếp với đối tượng SME của PromoPilot AI.

**Áp dụng vào MVP:**
- `src/segmentation/rfm.py` + `clustering.py`: tính RFM chuẩn, chuẩn hoá, K-Means với **k được chọn tự động qua silhouette score** (k=2..6), đặt tên cụm theo rank R/F/M (Khách giá trị cao, Khách mua thường xuyên, Khách mới, Khách có nguy cơ rời bỏ, Khách ít mua) — đúng theo yêu cầu gốc mục XII và định hướng của paper #9, #10.
- Module tự tắt nếu số khách hàng duy nhất quá ít (< 30) để tránh cluster vô nghĩa — đây là **business rule tự thiết kế cho MVP**, không phải kết luận trực tiếp từ paper.

---

### 1.5 Market Basket Analysis

| # | Paper | Năm | Journal/Nguồn | DOI/Link |
|---|---|---|---|---|
| 11 | *A Comparative Analysis of Apriori and FP-Growth Algorithms for Market Basket Analysis Using Multi-level Association Rule Mining* | 2024 | Springer (Conference/Book chapter) | https://www.springerprofessional.de/en/a-comparative-analysis-of-apriori-and-fp-growth-algorithms-for-m/23995276 |
| 12 | *Market basket analysis with association rules* | 2021 | Communications in Statistics – Theory and Methods, Vol 50(7) | https://doi.org/10.1080/03610926.2020.1716255 |

**Phương pháp:** So sánh Apriori (breadth-first, sinh candidate itemsets) và FP-Growth (depth-first, dùng FP-tree, không sinh candidate) để tìm frequent itemsets, sau đó sinh association rules với support/confidence/lift.

**Ý nghĩa:** FP-Growth nhanh hơn Apriori đáng kể trên dataset lớn nhưng Apriori dễ hiểu/diễn giải hơn cho candidate itemsets nhỏ — với quy mô SME (vài chục nghìn giao dịch), cả hai đều khả thi.

**Áp dụng vào MVP:**
- `src/basket/market_basket.py` dùng `mlxtend` (apriori hoặc fpgrowth tuỳ cờ cấu hình, mặc định fpgrowth vì nhanh hơn theo paper #11), sinh rule với support/confidence/lift, lọc theo ngưỡng lift > 1 và confidence ≥ 0.3 (ngưỡng này là **business rule tự thiết kế**, không phải từ paper).

---

### 1.6 Multi-Armed Bandit / Contextual Bandit trong Marketing

| # | Paper | Năm | Journal/Nguồn | DOI/Link |
|---|---|---|---|---|
| 13 | *Multi-armed bandits for performance marketing* | 2023/2024 | International Journal of Data Science and Analytics (Springer) | https://doi.org/10.1007/s41060-023-00493-7 |

**Phương pháp:** Dùng thuật toán multi-armed bandit (thay vì A/B test tĩnh) để phân bổ ngân sách/traffic động giữa các biến thể khuyến mãi/quảng cáo dựa trên hiệu suất theo thời gian thực.

**Ý nghĩa:** Hiệu quả đặc biệt khi số lượng dữ liệu ít, ngân sách nhỏ, thị trường thay đổi nhanh — đúng bối cảnh SME.

**Áp dụng vào MVP:** **Không** triển khai bandit engine trong MVP (Priority 3 theo yêu cầu gốc) vì cần vòng lặp thử nghiệm liên tục nhiều campaign mà một MVP one-shot demo không mô phỏng được trung thực. Kiến trúc `src/optimization/` để lại interface `BanditAllocator` (chưa implement, có docstring ghi rõ TODO) cho giai đoạn sau.

---

### 1.7 Retail Store Location (tham khảo, không áp dụng trực tiếp)

| # | Paper | Năm | Journal | DOI/Link |
|---|---|---|---|---|
| 14 | *Retail store location screening: A machine learning-based approach* | 2024 | Journal of Retailing and Consumer Services, Vol 77 | https://doi.org/10.1016/j.jretconser.2023.103715 (link ScienceDirect: S0969698923003715) |

**Ý nghĩa:** Minh hoạ cách ensemble ML (sequential ensemble học residual của model chính) có thể vượt industry benchmark trong bài toán retail. **Không liên quan trực tiếp** đến scope MVP (không có bài toán chọn địa điểm), nhưng ý tưởng "ensemble học residual" được ghi nhận là điểm tham khảo kỹ thuật chung cho `src/forecasting/`.

---

### 1.8 WAPE / Forecast Accuracy Metrics cho Intermittent Demand

Nguồn: Rob J. Hyndman – *WAPE: Weighted Absolute Percentage Error* (blog kỹ thuật của tác giả `forecast`/`fable` package trong R, chuyên gia hàng đầu về forecasting, thường được trích dẫn học thuật) — https://robjhyndman.com/hyndsight/wape.html; và tổng hợp so sánh MAPE/WAPE/WMAPE tại Baeldung CS (nguồn kỹ thuật, không phải peer-reviewed journal, dùng để tham khảo định nghĩa công thức).

**Ý nghĩa:** MAPE không xác định được khi actual = 0 và bị méo bởi các SKU bán chậm; WAPE (tổng |error| / tổng |actual|) ổn định hơn cho demand bán lẻ có nhiều ngày/SKU có sales = 0 hoặc rất thấp (intermittent demand).

**Áp dụng vào MVP:** `src/forecasting/backtest.py` dùng **WAPE làm metric chính** để so sánh và chọn model; chỉ hiển thị MAPE khi giá trị actual trung bình đủ lớn (> ngưỡng cấu hình) — đúng yêu cầu gốc mục IX ("Không nên dùng MAPE khi actual gần 0").

---

## 2. Phân tách rõ ràng: Literature vs. Assumption vs. Business Rule

Để tuân thủ nguyên tắc "không bịa causal uplift", toàn bộ logic ra quyết định của PromoPilot AI được gắn nhãn theo 3 loại nguồn:

| Loại | Ý nghĩa | Ví dụ trong MVP |
|---|---|---|
| **[LITERATURE]** | Có cơ sở trực tiếp từ paper liệt kê ở trên | Dùng WAPE thay MAPE khi actual thấp; BOGO có uplift đơn vị cao hơn discount tương đương; RFM+K-Means cho segmentation |
| **[ASSUMPTION]** | Giả định kỹ thuật cần thiết để MVP chạy được khi thiếu dữ liệu causal, có ghi chú rõ trong UI | Bảng elasticity mặc định theo cơ chế khuyến mãi khi dataset không có lịch sử promotion; hệ số uplift bundle giả định +15% units nếu không có dữ liệu lịch sử |
| **[BUSINESS RULE]** | Ngưỡng/luật tự thiết kế theo kinh nghiệm vận hành SME, không tuyên bố có cơ sở khoa học | Ngưỡng Data Quality Score; ngưỡng lift>1 & confidence≥30% để đề xuất bundle; ngưỡng phân loại rủi ro tồn kho LOW/MEDIUM/HIGH; công thức Safety Stock = avg_daily_demand × safety_stock_days |

Mọi màn hình hiển thị recommendation trong app đều gắn nhãn ngắn gọn (💡 giả định / 📊 dữ liệu / 📐 quy tắc) để người dùng SME phân biệt được đâu là con số "chắc chắn từ dữ liệu của họ" và đâu là "giả định cần họ tự đánh giá".

## 3. Chủ đề không tìm được nguồn xác thực trong phiên nghiên cứu này

- "AutoML cho SME" — kết quả tìm kiếm chủ yếu là bài blog thương mại, không có journal Q1/Q2 cụ thể được xác nhận trong phiên này. Không trích dẫn.
- "Cold-start problem" trong forecasting bán lẻ — chưa tìm kiếm riêng do giới hạn số lượt search trong phiên; MVP xử lý cold-start bằng business rule đơn giản (dùng category-level average khi SKU mới chưa đủ lịch sử), không tuyên bố có cơ sở paper cụ thể.
- Google Scholar/Scopus/Web of Science trực tiếp không truy cập được (không có quyền truy cập cơ sở dữ liệu học thuật có phí trong phiên làm việc này); toàn bộ nguồn trên lấy từ kết quả WebSearch công khai (ScienceDirect, Springer, PLOS, PubMed, Management Science/Marketing Science qua INFORMS, arXiv, MDPI, ResearchGate).

## 3.5. Cập nhật 2026-09-21: mở rộng bộ model dự báo (LightGBM, CatBoost, Ensemble)

Theo yêu cầu nâng cấp liên tục của người dùng, bộ candidate model trong `src/forecasting/models.py`
được mở rộng từ 7 lên 11 model:

- **XGBoost, LightGBM, CatBoost**: cả ba đều là gradient boosting trên cây quyết định, cùng họ
  thuật toán với Gradient Boosting/Random Forest đã có, khác nhau ở cách tối ưu tốc độ/độ chính
  xác (LightGBM dùng histogram-based split + leaf-wise growth; CatBoost xử lý tốt categorical
  features và ordered boosting để giảm overfitting). [LITERATURE định tính]: các thư viện này là
  chuẩn công nghiệp phổ biến trong demand forecasting hiện đại (được nhắc tới như lựa chọn ensemble
  ML trong nhiều paper đã khảo sát ở mục 1.2, vd "XGBoost" trong "Adaptive demand forecasting
  framework..."). Không có thư viện nào trong 3 thư viện này được cài đặt sẵn khi máy chưa có
  Internet — hệ thống tự bỏ qua nếu import lỗi (đã test: không crash).
- **Ensemble (Holt-Winters + Random Forest)**: [LITERATURE]: trung bình cộng dự báo từ nhiều model
  khác họ (1 model thống kê + 1 model học máy) thường cho kết quả ổn định hơn dùng riêng lẻ — đúng
  tinh thần hybrid ensemble learning (mục 1.2, Computing 2024). [ASSUMPTION cho MVP]: dùng trọng số
  bằng nhau (simple average) thay vì học trọng số tối ưu (stacking/weighted ensemble) vì MVP chưa
  có đủ dữ liệu backtest để tránh overfit khi học trọng số.

**Kết quả thực nghiệm trên dữ liệu demo** (`data/demo_sme_sales.csv`, dự báo doanh thu công ty):
Random Forest vẫn thắng (WAPE 20.06%) — không có model mới nào vượt trội hơn trên bộ dữ liệu này.
Đây là kết quả trung thực, không phải mọi thuật toán mới đều tự động cải thiện độ chính xác; giá
trị của việc mở rộng bộ candidate là tăng khả năng tìm được model tốt nhất cho **từng dataset cụ
thể** của từng doanh nghiệp (một số dataset khác có thể phù hợp hơn với LightGBM/CatBoost).

**Đánh đổi hiệu năng đã ghi nhận**: thời gian backtest tăng ~2 lần (21s → 45s cho 1 lượt dự báo
trên dữ liệu demo, 3 fold backtest x 11 model ứng viên). Xem `docs/nhat_ky_nang_cap.md` để biết
định hướng tối ưu (vd giảm số fold cho model chậm, cache kết quả, chạy song song).

## 4. Kết luận cho thiết kế MVP

1. Không có "one model fits all" — cần Auto Model Selection theo backtest (paper #3, #4).
2. Không claim causal uplift nếu không có treatment/control sạch (paper #1, #2) → luôn gắn disclaimer trong Promotion Simulator.
3. BOGO/Bundle có định tính rõ ràng khác Discount về hành vi khách hàng (paper #6, #7) → bảng elasticity theo cơ chế phải khác nhau, không dùng chung 1 hệ số.
4. RFM + K-Means là lựa chọn hợp lý, dễ diễn giải cho SME (paper #9, #10).
5. WAPE là metric chính cho forecast retail có nhiều ngày sales thấp/bằng 0 (Hyndman).
6. FP-Growth ưu tiên hơn Apriori về tốc độ ở dataset vừa (paper #11).
