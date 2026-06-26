"""科室模块业务逻辑层"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.department.schemas import DeptCreate, DeptUpdate, DeptResponse, DeptListResponse
from app.department import repository as repo
from app.hospital.models import HospitalModel
from app.exception.base import NotFoundException
from app.shared.database import register_es_hook
from app.search.sync.hooks import sync_department_create, sync_department_update, sync_department_delete
import logging

logger = logging.getLogger(__name__)


async def _get_hospital_name(session: AsyncSession, hospital_id: int) -> str:
    result = await session.execute(
        select(HospitalModel.hospital_name).where(HospitalModel.id == hospital_id)
    )
    name = result.scalar_one_or_none()
    if not name:
        logger.warning("ES 同步: hospital_id=%d 不存在，hospital_name 将为空", hospital_id)
    return name or ""


def _to_response(d) -> DeptResponse:
    return DeptResponse(id=d.id, hospital_id=d.hospital_id, dept_name=d.dept_name)


async def list_by_hospital(session: AsyncSession, hospital_id: int) -> list[DeptResponse]:
    depts = await repo.list_by_hospital(session, hospital_id)
    return [_to_response(d) for d in depts]


async def list_all(session: AsyncSession) -> list[DeptListResponse]:
    rows = await repo.list_all_with_hospital(session)
    return [DeptListResponse(**r) for r in rows]


async def create_dept(session: AsyncSession, req: DeptCreate) -> DeptResponse:
    d = await repo.create(session, hospital_id=req.hospital_id, dept_name=req.dept_name)
    hn = await _get_hospital_name(session, req.hospital_id)
    register_es_hook(session, lambda: sync_department_create(d, hn))
    return _to_response(d)


async def update_dept(session: AsyncSession, dept_id: int, req: DeptUpdate) -> DeptResponse:
    d = await repo.get_by_id(session, dept_id)
    if not d:
        raise NotFoundException("科室不存在")
    d = await repo.update(session, d, dept_name=req.dept_name)
    hn = await _get_hospital_name(session, d.hospital_id)
    register_es_hook(session, lambda: sync_department_update(d, hn))
    return _to_response(d)


async def delete_dept(session: AsyncSession, dept_id: int):
    d = await repo.get_by_id(session, dept_id)
    if not d:
        raise NotFoundException("科室不存在")
    await repo.soft_delete(session, d)
    register_es_hook(session, lambda: sync_department_delete(dept_id))
