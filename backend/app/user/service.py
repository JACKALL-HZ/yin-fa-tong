"""用户中心业务逻辑层"""

from datetime import date, datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.user.schemas import ElderBindCreate, ElderBindUpdate, ElderBindResponse, ElderReminderResponse, TodoItem, AlertItem, HealthReminderItem, ProfileUpdate, ProfileResponse
from app.user.models import ElderBindModel
from app.auth.models import UserModel
from app.user import repository as repo
from app.reserve import repository as reserve_repo
from app.reserve.models import ReserveModel
from app.schedule.models import ScheduleModel
from app.doctor.models import DoctorModel
from app.department.models import DepartmentModel
from app.hospital.models import HospitalModel
from app.reminder.models import ReminderModel
from app.exception.base import NotFoundException, BadRequestException


def _to_profile_response(user: UserModel) -> ProfileResponse:
    profile_complete = all([user.real_name, user.gender, user.id_card, user.birthday])
    return ProfileResponse(
        id=user.id,
        username=user.username,
        nickname=user.nickname,
        user_type=user.user_type,
        real_name=user.real_name,
        gender=user.gender,
        id_card=user.id_card,
        birthday=user.birthday,
        phone=user.phone,
        profile_complete=profile_complete,
    )


async def update_profile(session: AsyncSession, user: UserModel, req: ProfileUpdate) -> ProfileResponse:
    """更新用户个人信息"""
    user.real_name = req.real_name
    user.gender = req.gender
    user.id_card = req.id_card
    user.birthday = req.birthday
    user.phone = req.phone
    await session.commit()
    return _to_profile_response(user)


def _calc_age(birthday: date | None) -> int | None:
    """根据出生日期计算实足年龄"""
    if not birthday:
        return None
    today = date.today()
    return today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))


def _to_response(elder: ElderBindModel) -> ElderBindResponse:
    age = _calc_age(elder.birthday)
    return ElderBindResponse(
        id=elder.id,
        child_uid=elder.child_uid,
        elder_name=elder.elder_name,
        elder_id_card=elder.elder_id_card,
        elder_phone=elder.elder_phone,
        gender=elder.gender,
        birthday=elder.birthday,
        age=age,
        medical_card=elder.medical_card,
        is_elder=age is not None and age >= 60,
    )


async def list_elders(session: AsyncSession, child_uid: int) -> list[ElderBindResponse]:
    elders = await repo.list_by_child(session, child_uid)
    return [_to_response(e) for e in elders]


async def create_elder(session: AsyncSession, child_uid: int, req: ElderBindCreate) -> ElderBindResponse:
    # 每人最多绑定 5 位长辈
    count = await repo.count_by_child(session, child_uid)
    if count >= 5:
        raise BadRequestException("最多绑定5位长辈")

    elder = await repo.create(
        session, child_uid,
        elder_name=req.elder_name,
        elder_id_card=req.elder_id_card,
        elder_phone=req.elder_phone,
        gender=req.gender,
        birthday=req.birthday,
        medical_card=req.medical_card,
    )
    return _to_response(elder)


async def update_elder(session: AsyncSession, bind_id: int, child_uid: int, req: ElderBindUpdate) -> ElderBindResponse:
    elder = await repo.get_by_id(session, bind_id, child_uid)
    if not elder:
        raise NotFoundException("长辈信息不存在")
    elder = await repo.update(
        session, elder,
        elder_name=req.elder_name,
        elder_id_card=req.elder_id_card,
        elder_phone=req.elder_phone,
        gender=req.gender,
        birthday=req.birthday,
        medical_card=req.medical_card,
    )
    return _to_response(elder)


async def delete_elder(session: AsyncSession, bind_id: int, child_uid: int):
    elder = await repo.get_by_id(session, bind_id, child_uid)
    if not elder:
        raise NotFoundException("长辈信息不存在")
    await repo.soft_delete(session, elder)


def _format_time_period(period: str) -> str:
    """排班时段转中文"""
    return {"AM": "上午", "PM": "下午", "ALL": "全天"}.get(period, period)


def _relative_time(dt: datetime) -> str:
    """生成相对时间描述"""
    diff = datetime.now() - dt
    minutes = int(diff.total_seconds() / 60)
    if minutes < 1:
        return "刚刚"
    if minutes < 60:
        return f"{minutes} 分钟前"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} 小时前"
    days = hours // 24
    return f"{days} 天前"


def _format_date(work_date: date) -> str:
    """格式化日期为中文"""
    today = date.today()
    delta = (work_date - today).days
    if delta == 0:
        return "今天"
    if delta == 1:
        return "明天"
    if delta == 2:
        return "后天"
    return f"{work_date.month}月{work_date.day}日"


async def get_elder_reminders(session: AsyncSession, child_uid: int) -> ElderReminderResponse:
    """根据长辈的真实挂号记录生成代办任务和智能提醒"""
    # 1. 获取当前用户绑定的所有长辈
    elders = await repo.list_by_child(session, child_uid)
    elder_map = {e.id: e for e in elders}

    if not elder_map:
        return ElderReminderResponse(todos=[], alerts=[])

    # 2. 查询这些长辈的所有挂号记录
    reserves = await reserve_repo.list_by_elder_binds(session, list(elder_map.keys()))

    # 3. 批量查询关联的排班 + 医生 + 科室 + 医院信息
    schedule_ids = list({r.schedule_id for r in reserves})
    schedule_map: dict[int, dict] = {}
    if schedule_ids:
        stmt = (
            select(
                ScheduleModel, DoctorModel.doctor_name, DoctorModel.register_fee,
                DepartmentModel.dept_name, HospitalModel.hospital_name,
            )
            .join(DoctorModel, ScheduleModel.doctor_id == DoctorModel.id)
            .join(DepartmentModel, DoctorModel.dept_id == DepartmentModel.id)
            .join(HospitalModel, DepartmentModel.hospital_id == HospitalModel.id)
            .where(ScheduleModel.id.in_(schedule_ids), ScheduleModel.is_deleted == 0)
        )
        result = await session.execute(stmt)
        for s, doc_name, fee, dept_name, hosp_name in result.all():
            schedule_map[s.id] = {
                "work_date": s.work_date,
                "time_period": s.time_period,
                "doctor_name": doc_name,
                "register_fee": fee,
                "dept_name": dept_name,
                "hospital_name": hosp_name,
            }

    # 4. 根据挂号记录生成代办任务和智能提醒
    today = date.today()
    now = datetime.now()
    todos: list[TodoItem] = []
    alerts: list[AlertItem] = []

    for r in reserves:
        elder = elder_map.get(r.elder_bind_id)
        if not elder:
            continue
        sched = schedule_map.get(r.schedule_id)
        if not sched:
            continue

        elder_name = elder.elder_name
        work_date = sched["work_date"]
        time_period = _format_time_period(sched["time_period"])
        dept_name = sched["dept_name"] or "未知科室"
        hospital_name = sched["hospital_name"] or "未知医院"
        doctor_name = sched["doctor_name"] or ""
        date_str = _format_date(work_date)
        delta_days = (work_date - today).days

        # ---- 代办任务生成规则 ----

        # 待支付订单 → 催促支付
        if r.pay_status == 1 and r.order_status == 1:
            todos.append(TodoItem(
                icon="💰",
                text=f"为{elder_name}支付{dept_name}挂号费",
                time=f"{date_str} {time_period} · {hospital_name}",
                urgent=True,
            ))

        # 已支付 + 未来 3 天内的预约 → 提醒就诊
        elif r.order_status == 2 and 0 <= delta_days <= 3:
            todos.append(TodoItem(
                icon="🩺",
                text=f"带{elder_name}去{dept_name}{doctor_name}医生处就诊",
                time=f"{date_str} {time_period} · {hospital_name}",
                urgent=delta_days <= 1,
            ))

        # ---- 智能提醒生成规则 ----

        # 待支付且创建超过 10 分钟 → 支付超时预警
        if r.pay_status == 1 and r.order_status == 1:
            created = r.create_time
            if isinstance(created, datetime) and (now - created).total_seconds() > 600:
                alerts.append(AlertItem(
                    icon="⏰",
                    title="待支付提醒",
                    desc=f"{elder_name}的{dept_name}挂号订单还未支付，15分钟后将自动取消",
                    time=_relative_time(created),
                ))

        # 已支付 + 就诊日是今天 → 当日就诊提醒
        if r.order_status == 2 and delta_days == 0:
            alerts.append(AlertItem(
                icon="📅",
                title="今日就诊提醒",
                desc=f"{elder_name}今天{time_period}在{hospital_name}{dept_name}就诊",
                time="今天",
            ))

        # 已支付 + 就诊日是明天 → 提前提醒
        if r.order_status == 2 and delta_days == 1:
            alerts.append(AlertItem(
                icon="🩺",
                title="明日就诊提醒",
                desc=f"{elder_name}明天{time_period}在{hospital_name}{dept_name}{doctor_name}医生处就诊",
                time="明天",
            ))

        # 候诊中 → 排队状态提醒
        if r.order_status == 2 and r.queue_status == 1 and r.queue_code:
            alerts.append(AlertItem(
                icon="🏥",
                title="候诊排队中",
                desc=f"{elder_name}在{hospital_name}{dept_name}候诊，排队号 {r.queue_code}",
                time="进行中",
            ))

        # 已就诊 → 就诊完成提醒
        if r.order_status == 3:
            alerts.append(AlertItem(
                icon="✅",
                title="就诊已完成",
                desc=f"{elder_name}已在{hospital_name}{dept_name}完成就诊",
                time=_relative_time(r.create_time) if isinstance(r.create_time, datetime) else "近期",
            ))

    # 代办任务排序：紧急优先
    todos.sort(key=lambda t: (not t.urgent, t.time))
    # 智能提醒排序：按时间倒序（最新的在前）
    alerts.sort(key=lambda a: a.time, reverse=True)

    # 5. 查询用户的健康提醒（用药/复诊/体检）
    type_icon_map = {"medicine": "💊", "revisit": "🩺", "checkup": "📋"}
    type_title_map = {"medicine": "用药提醒", "revisit": "复诊提醒", "checkup": "体检提醒"}
    type_action_map = {"medicine": "去续方", "revisit": "查看", "checkup": "预约"}

    reminder_result = await session.execute(
        select(ReminderModel).where(
            ReminderModel.user_id == child_uid,
            ReminderModel.is_deleted == 0,
            ReminderModel.is_active == 1,
        )
    )
    health_reminders: list[HealthReminderItem] = []
    for rm in reminder_result.scalars().all():
        rtype = rm.remind_type
        # 如果关联了长辈，拼接长辈姓名
        elder_label = ""
        if rm.elder_bind_id and rm.elder_bind_id in elder_map:
            elder_label = f"{elder_map[rm.elder_bind_id].elder_name}的"
        health_reminders.append(HealthReminderItem(
            icon=type_icon_map.get(rtype, "🔔"),
            title=type_title_map.get(rtype, "健康提醒"),
            desc=f"{elder_label}{rm.remind_content} · 每日 {rm.remind_time}",
            action=type_action_map.get(rtype, "查看"),
        ))

    return ElderReminderResponse(todos=todos, alerts=alerts, health_reminders=health_reminders)
