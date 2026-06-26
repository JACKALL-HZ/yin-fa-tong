"""模型注册中心 —— 集中导入所有 Model，供 Alembic 自动发现

Alembic 需要 import 所有模型才能生成迁移脚本。
在每个模块各自的 models.py 中定义 Model，在此统一注册。
"""

# 导入顺序按外键依赖：先主表后子表
from app.auth.models import UserModel              # noqa: F401
from app.hospital.models import HospitalModel      # noqa: F401
from app.user.models import ElderBindModel         # noqa: F401
from app.department.models import DepartmentModel  # noqa: F401
from app.doctor.models import DoctorModel          # noqa: F401
from app.schedule.models import ScheduleModel      # noqa: F401
from app.reserve.models import ReserveModel        # noqa: F401
from app.payment.models import PayRecordModel      # noqa: F401
from app.report.models import PhysicalReportModel  # noqa: F401
from app.accompany.volunteer.models import VolunteerModel        # noqa: F401
from app.accompany.order.models import AccompanyOrderModel       # noqa: F401
from app.message.models import MessageModel        # noqa: F401
from app.reminder.models import ReminderModel    # noqa: F401

__all__ = [
    "UserModel",
    "HospitalModel",
    "ElderBindModel",
    "DepartmentModel",
    "DoctorModel",
    "ScheduleModel",
    "ReserveModel",
    "PayRecordModel",
    "PhysicalReportModel",
    "VolunteerModel",
    "AccompanyOrderModel",
    "MessageModel",
    "ReminderModel",
]
