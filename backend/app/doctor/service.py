"""医生模块业务逻辑层"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.doctor.schemas import DoctorCreate, DoctorUpdate, DoctorResponse
from app.doctor import repository as repo
from app.department.models import DepartmentModel
from app.hospital.models import HospitalModel
from app.exception.base import NotFoundException
from app.shared.database import register_es_hook
from app.search.sync.hooks import sync_doctor_create, sync_doctor_update, sync_doctor_delete
import logging

logger = logging.getLogger(__name__)


async def _get_doctor_context(session: AsyncSession, dept_id: int) -> tuple[str, int, str]:
    """解析医生关联的 dept_name, hospital_id, hospital_name"""
    result = await session.execute(
        select(DepartmentModel.dept_name, HospitalModel.id, HospitalModel.hospital_name)
        .join(HospitalModel, DepartmentModel.hospital_id == HospitalModel.id)
        .where(DepartmentModel.id == dept_id)
    )
    row = result.one_or_none()
    if row:
        return row[0], row[1], row[2]
    logger.warning("ES 同步: dept_id=%d 关联的科室/医院不存在，上下文将为空", dept_id)
    return "", 0, ""


async def list_all(session: AsyncSession) -> list[DoctorResponse]:
    rows = await repo.list_all_with_relations(session)
    return [DoctorResponse(**r) for r in rows]


async def list_by_dept(session: AsyncSession, dept_id: int) -> list[DoctorResponse]:
    docs = await repo.list_by_dept(session, dept_id)
    return [
        DoctorResponse(id=d.id, dept_id=d.dept_id, doctor_name=d.doctor_name,
                       doctor_title=d.doctor_title, specialty=d.specialty,
                       register_fee=d.register_fee, doctor_avatar=d.doctor_avatar)
        for d in docs
    ]


async def create_doctor(session: AsyncSession, req: DoctorCreate) -> DoctorResponse:
    d = await repo.create(session, dept_id=req.dept_id, doctor_name=req.doctor_name,
                          doctor_title=req.doctor_title, specialty=req.specialty,
                          register_fee=req.register_fee)
    dn, hid, hn = await _get_doctor_context(session, req.dept_id)
    register_es_hook(session, lambda: sync_doctor_create(d, dn, hid, hn))
    return DoctorResponse(id=d.id, dept_id=d.dept_id, doctor_name=d.doctor_name,
                          doctor_title=d.doctor_title, specialty=d.specialty,
                          register_fee=d.register_fee, doctor_avatar=d.doctor_avatar)


async def update_doctor(session: AsyncSession, doctor_id: int, req: DoctorUpdate) -> DoctorResponse:
    d = await repo.get_by_id(session, doctor_id)
    if not d:
        raise NotFoundException("医生不存在")
    d = await repo.update(session, d, doctor_name=req.doctor_name, doctor_title=req.doctor_title,
                          specialty=req.specialty, register_fee=req.register_fee)
    dn, hid, hn = await _get_doctor_context(session, d.dept_id)
    register_es_hook(session, lambda: sync_doctor_update(d, dn, hid, hn))
    return DoctorResponse(id=d.id, dept_id=d.dept_id, doctor_name=d.doctor_name,
                          doctor_title=d.doctor_title, specialty=d.specialty,
                          register_fee=d.register_fee, doctor_avatar=d.doctor_avatar)


async def delete_doctor(session: AsyncSession, doctor_id: int):
    d = await repo.get_by_id(session, doctor_id)
    if not d:
        raise NotFoundException("医生不存在")
    await repo.soft_delete(session, d)
    register_es_hook(session, lambda: sync_doctor_delete(doctor_id))
