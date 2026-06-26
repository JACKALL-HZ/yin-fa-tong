"""志愿者业务逻辑层"""

from sqlalchemy.ext.asyncio import AsyncSession
from app.accompany.volunteer.schemas import VolunteerCreate, VolunteerUpdate, VolunteerResponse
from app.accompany.volunteer.models import VolunteerModel
from app.accompany.volunteer import repository as repo
from app.exception.base import NotFoundException


def _to_response(v: VolunteerModel) -> VolunteerResponse:
    return VolunteerResponse(
        id=v.id, vol_name=v.vol_name, vol_phone=v.vol_phone,
        service_dept=v.service_dept, avatar=v.avatar, service_desc=v.service_desc,
        service_score=v.service_score, service_count=v.service_count, status=v.status,
    )


async def list_available(session: AsyncSession) -> list[VolunteerResponse]:
    vols = await repo.list_available(session)
    return [_to_response(v) for v in vols]


async def list_all(session: AsyncSession) -> list[VolunteerResponse]:
    vols = await repo.list_all(session)
    return [_to_response(v) for v in vols]


async def get_detail(session: AsyncSession, vol_id: int) -> VolunteerResponse:
    v = await repo.get_by_id(session, vol_id)
    if not v:
        raise NotFoundException("志愿者不存在")
    return _to_response(v)


async def create_volunteer(session: AsyncSession, req: VolunteerCreate) -> VolunteerResponse:
    v = await repo.create(session, vol_name=req.vol_name, vol_phone=req.vol_phone,
                          service_dept=req.service_dept, service_desc=req.service_desc, avatar=req.avatar)
    return _to_response(v)


async def update_volunteer(session: AsyncSession, vol_id: int, req: VolunteerUpdate) -> VolunteerResponse:
    v = await repo.get_by_id(session, vol_id)
    if not v:
        raise NotFoundException("志愿者不存在")
    v = await repo.update(session, v, vol_name=req.vol_name, vol_phone=req.vol_phone,
                          service_dept=req.service_dept, service_desc=req.service_desc, status=req.status)
    return _to_response(v)


async def delete_volunteer(session: AsyncSession, vol_id: int):
    v = await repo.get_by_id(session, vol_id)
    if not v:
        raise NotFoundException("志愿者不存在")
    v.is_deleted = 1
    await session.flush()
