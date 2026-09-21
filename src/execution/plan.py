"""Execution Plan Generator (mục XXVII, XXVIII spec PromotionPilot AI).

Sinh kế hoạch triển khai theo mốc D-7 .. D+7 kèm phân công theo phòng ban (team), dựa trên
RecommendationCard đã chọn. [BUSINESS RULE]: cấu trúc timeline và nội dung task là mẫu chuẩn tự
thiết kế cho MVP (không phải quy trình nội bộ thật của một doanh nghiệp cụ thể) — doanh nghiệp cần
tự điều chỉnh owner/deadline theo tổ chức thật của họ.

MVP không kết nối hệ thống ticket thật (Jira/Monday/Asana/Teams/Email) — chỉ tạo bảng Task nội bộ.
Kiến trúc sẵn sàng: mỗi ExecutionTask có đủ field (team, task, owner, due_date, status, priority)
để tương lai map 1-1 sang API của các hệ thống đó.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

TEAMS = [
    "Demand Planning",
    "Marketing",
    "ERP / IT",
    "Supply Chain",
    "Retail / Store",
    "HR",
    "PSD / Trading",
]

PRIORITY_LEVELS = ["Cao", "Trung bình", "Thấp"]
STATUS_LEVELS = ["Chưa bắt đầu", "Đang thực hiện", "Hoàn thành", "Trễ hạn"]


@dataclass
class ExecutionTask:
    day_offset: int  # vd -7, -5, 0, 3, 7 (so với ngày khởi chạy campaign)
    team: str
    task: str
    owner: str
    due_date: pd.Timestamp
    status: str = "Chưa bắt đầu"
    priority: str = "Trung bình"

    def day_label(self) -> str:
        if self.day_offset == 0:
            return "D0 (Ngày khởi chạy)"
        sign = "+" if self.day_offset > 0 else ""
        return f"D{sign}{self.day_offset}"


def generate_execution_plan(
    campaign_start: pd.Timestamp,
    product_focus: str,
    promotion_label: str,
    recommended_stock: float,
    objective_vi: str,
) -> list[ExecutionTask]:
    """Sinh danh sách task theo mốc D-7..D+7, nội dung có tham chiếu tới scenario đã chọn.

    [BUSINESS RULE]: template timeline chuẩn cho 1 chương trình khuyến mãi bán lẻ vừa/nhỏ — có thể
    không phù hợp 100% với mọi loại hình doanh nghiệp, cần điều chỉnh thủ công khi áp dụng thật.
    """
    campaign_start = pd.Timestamp(campaign_start)

    template = [
        (-7, "Demand Planning", f"Chốt dự báo nhu cầu & xác nhận tồn kho mục tiêu {recommended_stock:.0f} sản phẩm cho {product_focus}", "Cao"),
        (-6, "Supply Chain", f"Đặt hàng bổ sung / lên lịch nhập kho cho {product_focus} nếu tồn kho hiện tại chưa đủ", "Cao"),
        (-5, "Marketing", f"Chuẩn bị nội dung & vật phẩm quảng cáo (POSM) cho chương trình '{promotion_label}'", "Trung bình"),
        (-4, "PSD / Trading", "Xác nhận giá bán, điều kiện áp dụng và ngân sách khuyến mãi với các bên liên quan", "Trung bình"),
        (-3, "ERP / IT", f"Cấu hình chương trình khuyến mãi '{promotion_label}' trong hệ thống bán hàng/ERP", "Cao"),
        (-2, "Supply Chain", f"Hoàn tất giao hàng {recommended_stock:.0f} sản phẩm {product_focus} đến cửa hàng/kho", "Cao"),
        (-1, "Retail / Store", "Đào tạo nhân viên bán hàng về chương trình, cách tư vấn và xử lý tình huống", "Trung bình"),
        (-1, "HR", "Rà soát lịch làm việc, tăng cường nhân sự nếu dự kiến traffic tăng cao", "Trung bình"),
        (0, "Retail / Store", f"Khởi chạy chương trình '{promotion_label}' — mục tiêu: {objective_vi}", "Cao"),
        (3, "Demand Planning", "Thu thập dữ liệu bán hàng thực tế 3 ngày đầu, đối chiếu với dự báo (xem trang Campaign Monitor)", "Cao"),
        (7, "Marketing", "Tổng kết kết quả tuần đầu, đánh giá phản hồi khách hàng", "Trung bình"),
        (7, "PSD / Trading", "Review cuối: quyết định Tiếp tục / Điều chỉnh / Dừng / Mở rộng (xem trang Alerts)", "Cao"),
    ]

    tasks = []
    for day_offset, team, task_desc, priority in template:
        due_date = campaign_start + pd.Timedelta(days=day_offset)
        tasks.append(
            ExecutionTask(
                day_offset=day_offset,
                team=team,
                task=task_desc,
                owner=f"Phụ trách {team}",
                due_date=due_date,
                status="Chưa bắt đầu",
                priority=priority,
            )
        )
    return sorted(tasks, key=lambda t: t.day_offset)


def tasks_to_dataframe(tasks: list[ExecutionTask]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Mốc": t.day_label(),
                "Ngày": t.due_date.date(),
                "Phòng ban": t.team,
                "Công việc": t.task,
                "Phụ trách": t.owner,
                "Mức độ ưu tiên": t.priority,
                "Trạng thái": t.status,
            }
            for t in tasks
        ]
    )
