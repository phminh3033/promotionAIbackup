"""Định nghĩa schema chuẩn hoá (canonical schema) mà toàn bộ hệ thống PromoPilot AI sử dụng.

Doanh nghiệp có thể đặt tên cột khác nhau trong file gốc (POS export, Excel tự làm...).
Sau bước Data Mapping Wizard, dữ liệu được đổi tên về các cột chuẩn dưới đây để mọi
module phía sau (forecasting, inventory, promotion...) chỉ cần làm việc với MỘT schema duy nhất.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Các trường bắt buộc tối thiểu để hệ thống chạy được (theo yêu cầu mục V)
REQUIRED_FIELDS = ["date", "product_id", "quantity", "revenue"]

# Các trường tùy chọn: nếu có sẽ mở thêm module, nếu thiếu thì module liên quan tự tắt
OPTIONAL_FIELDS = [
    "transaction_id",
    "customer_id",
    "store_id",
    "category",
    "selling_price",
    "cost",
    "gross_profit",
    "inventory",
    "promotion_id",
    "promotion_type",
    "discount",
    "promotion_start",
    "promotion_end",
]

ALL_CANONICAL_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS

# Nhãn tiếng Việt hiển thị cho người dùng trong Mapping Wizard
FIELD_LABELS_VI = {
    "date": "Ngày giao dịch",
    "product_id": "Mã sản phẩm",
    "quantity": "Số lượng",
    "revenue": "Doanh thu",
    "transaction_id": "Mã giao dịch / hóa đơn",
    "customer_id": "Mã khách hàng",
    "store_id": "Mã cửa hàng / chi nhánh",
    "category": "Danh mục sản phẩm",
    "selling_price": "Đơn giá bán",
    "cost": "Giá vốn",
    "gross_profit": "Lợi nhuận gộp",
    "inventory": "Tồn kho",
    "promotion_id": "Mã chương trình khuyến mãi",
    "promotion_type": "Loại khuyến mãi",
    "discount": "Mức giảm giá",
    "promotion_start": "Ngày bắt đầu khuyến mãi",
    "promotion_end": "Ngày kết thúc khuyến mãi",
}

FIELD_HINTS_VI = {
    "date": "Cột chứa ngày (hoặc ngày giờ) phát sinh giao dịch bán hàng.",
    "product_id": "Mã hoặc tên định danh duy nhất của sản phẩm/SKU.",
    "quantity": "Số lượng sản phẩm bán ra trong dòng dữ liệu.",
    "revenue": "Doanh thu (thành tiền) của dòng dữ liệu, đã bao gồm số lượng.",
    "transaction_id": "Mã hóa đơn/giao dịch — cần thiết cho phân tích giỏ hàng.",
    "customer_id": "Mã khách hàng — cần thiết cho phân tích khách hàng (RFM).",
    "store_id": "Mã cửa hàng — dùng khi doanh nghiệp có nhiều chi nhánh.",
    "category": "Nhóm/danh mục sản phẩm.",
    "selling_price": "Giá bán một đơn vị sản phẩm.",
    "cost": "Giá vốn một đơn vị sản phẩm — cần thiết để tính lợi nhuận gộp.",
    "gross_profit": "Lợi nhuận gộp có sẵn (nếu doanh nghiệp đã tính sẵn).",
    "inventory": "Tồn kho hiện tại của sản phẩm — cần thiết cho module Tồn kho.",
    "promotion_id": "Mã chương trình khuyến mãi đã áp dụng (nếu có).",
    "promotion_type": "Loại cơ chế khuyến mãi (giảm giá %, BOGO, bundle...).",
    "discount": "Giá trị hoặc phần trăm giảm giá đã áp dụng.",
    "promotion_start": "Ngày bắt đầu chương trình khuyến mãi.",
    "promotion_end": "Ngày kết thúc chương trình khuyến mãi.",
}


@dataclass
class DatasetCapabilities:
    """Đánh giá dữ liệu công ty có đủ trường nào để bật/tắt từng module.

    Nguyên tắc (mục V yêu cầu gốc): KHÔNG được crash nếu thiếu Customer_ID / Inventory...
    Thay vào đó module liên quan tự tắt và hệ thống giải thích lý do bằng tiếng Việt.
    """

    has_transaction: bool = False
    has_customer: bool = False
    has_store: bool = False
    has_category: bool = False
    has_price: bool = False
    has_cost: bool = False
    has_gross_profit: bool = False
    has_inventory: bool = False
    has_promotion: bool = False
    has_intraday_time: bool = False
    missing_optional: list[str] = field(default_factory=list)

    def module_status(self) -> dict[str, tuple[bool, str]]:
        """Trả về {tên module: (bật/tắt, lý do tiếng Việt)}."""
        return {
            "Phân tích khách hàng (RFM)": (
                self.has_customer,
                "Cần cột Mã khách hàng." if not self.has_customer else "Sẵn sàng.",
            ),
            "Phân tích giỏ hàng (Market Basket)": (
                self.has_transaction,
                "Cần cột Mã giao dịch/hóa đơn để nhóm sản phẩm mua cùng lúc."
                if not self.has_transaction
                else "Sẵn sàng.",
            ),
            "Lợi nhuận gộp / Margin": (
                self.has_cost or self.has_gross_profit,
                "Cần cột Giá vốn hoặc Lợi nhuận gộp để tính margin chính xác; nếu thiếu, hệ thống dùng margin giả định từ Business Profile."
                if not (self.has_cost or self.has_gross_profit)
                else "Sẵn sàng.",
            ),
            "Tồn kho & Đề xuất nhập hàng": (
                self.has_inventory,
                "Cần cột Tồn kho hiện tại. Thiếu thì hệ thống chỉ dự báo nhu cầu, không tính được số lượng cần nhập."
                if not self.has_inventory
                else "Sẵn sàng.",
            ),
            "Lịch sử phản hồi khuyến mãi": (
                self.has_promotion,
                "Cần cột Mã/Loại khuyến mãi. Thiếu thì mô phỏng dùng giả định elasticity mặc định thay vì dữ liệu lịch sử thật."
                if not self.has_promotion
                else "Sẵn sàng.",
            ),
            "Dự báo theo giờ / heatmap traffic": (
                self.has_intraday_time,
                "Cần cột ngày có kèm giờ (timestamp chi tiết)." if not self.has_intraday_time else "Sẵn sàng.",
            ),
            "Phân tích theo cửa hàng": (
                self.has_store,
                "Cần cột Mã cửa hàng." if not self.has_store else "Sẵn sàng.",
            ),
        }
