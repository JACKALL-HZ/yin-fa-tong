"""医院模块业务逻辑层"""

from sqlalchemy.ext.asyncio import AsyncSession
from app.hospital.schemas import HospitalCreate, HospitalUpdate, HospitalResponse
from app.hospital import repository as repo
from app.exception.base import NotFoundException
from app.shared.database import register_es_hook
from app.search.sync.hooks import sync_hospital_create, sync_hospital_update, sync_hospital_delete
import logging

logger = logging.getLogger(__name__)


def _to_response(h) -> HospitalResponse:
    return HospitalResponse(id=h.id, hospital_name=h.hospital_name, hospital_level=h.hospital_level, address=h.address)


async def list_hospitals(session: AsyncSession) -> list[HospitalResponse]:
    hospitals = await repo.list_all(session)
    return [_to_response(h) for h in hospitals]


async def create_hospital(session: AsyncSession, req: HospitalCreate) -> HospitalResponse:
    h = await repo.create(session, hospital_name=req.hospital_name, hospital_level=req.hospital_level, address=req.address)
    register_es_hook(session, lambda: sync_hospital_create(h))
    return _to_response(h)


async def update_hospital(session: AsyncSession, hospital_id: int, req: HospitalUpdate) -> HospitalResponse:
    h = await repo.get_by_id(session, hospital_id)
    if not h:
        raise NotFoundException("医院不存在")
    h = await repo.update(session, h, hospital_name=req.hospital_name, hospital_level=req.hospital_level, address=req.address)
    register_es_hook(session, lambda: sync_hospital_update(h))
    return _to_response(h)


async def delete_hospital(session: AsyncSession, hospital_id: int):
    h = await repo.get_by_id(session, hospital_id)
    if not h:
        raise NotFoundException("医院不存在")
    await repo.soft_delete(session, h)
    register_es_hook(session, lambda: sync_hospital_delete(hospital_id))
