"""体检报告数据访问层"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.report.models import PhysicalReportModel


async def get_by_id(session: AsyncSession, report_id: int) -> PhysicalReportModel | None:
    result = await session.execute(
        select(PhysicalReportModel).where(PhysicalReportModel.id == report_id, PhysicalReportModel.is_deleted == 0)
    )
    return result.scalar_one_or_none()


async def list_by_elder(session: AsyncSession, elder_bind_id: int) -> list[PhysicalReportModel]:
    result = await session.execute(
        select(PhysicalReportModel).where(
            PhysicalReportModel.elder_bind_id == elder_bind_id,
            PhysicalReportModel.is_deleted == 0,
        ).order_by(PhysicalReportModel.create_time.desc())
    )
    return list(result.scalars().all())


async def list_by_user_elders(session: AsyncSession, elder_bind_ids: list[int]) -> list[PhysicalReportModel]:
    if not elder_bind_ids:
        return []
    result = await session.execute(
        select(PhysicalReportModel).where(
            PhysicalReportModel.elder_bind_id.in_(elder_bind_ids),
            PhysicalReportModel.is_deleted == 0,
        ).order_by(PhysicalReportModel.create_time.desc())
    )
    return list(result.scalars().all())


async def create(
    session: AsyncSession,
    elder_bind_id: int,
    report_url: str,
    ocr_result: str | None = None,
    interpretation: str | None = None,
) -> PhysicalReportModel:
    report = PhysicalReportModel(
        elder_bind_id=elder_bind_id,
        report_url=report_url,
        ocr_result=ocr_result,
        interpretation=interpretation,
    )
    session.add(report)
    await session.flush()
    await session.refresh(report)
    return report


async def soft_delete(session: AsyncSession, report: PhysicalReportModel):
    report.is_deleted = 1
    await session.flush()
