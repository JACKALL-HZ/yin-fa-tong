"""ES 数据全量同步服务

从 DB + SYMPTOM_MAP 全量重建 4 个 ES 索引。
策略：delete + recreate 索引，保证完全一致性（数据量百级，执行 < 2s）。
"""

import hashlib
import logging

from sqlalchemy import select
from app.shared.elasticsearch import get_es, INDEX_HOSPITAL, INDEX_DEPARTMENT, INDEX_DOCTOR, INDEX_SYMPTOM
from app.shared.database import AsyncSessionLocal
from app.hospital.models import HospitalModel
from app.department.models import DepartmentModel
from app.doctor.models import DoctorModel
from app.guide.symptom_dict.mapping import SYMPTOM_MAP
from app.search.mappings import INDEX_MAPPINGS
from app.search.repository import delete_index, bulk_index
from app.search.schemas import HospitalDocument, DepartmentDocument, DoctorDocument, SymptomDocument

logger = logging.getLogger(__name__)


async def full_sync_all():
    """全量重建所有 ES 索引（delete + recreate + bulk_index）"""
    es = await get_es()
    logger.info("ES 全量同步开始...")

    # 从 DB 同步三类业务数据
    async with AsyncSessionLocal() as session:
        try:
            await _sync_hospitals(es, session)
            await _sync_departments(es, session)
            await _sync_doctors(es, session)
        finally:
            await session.close()

    # 从 SYMPTOM_MAP 同步症状词库
    await _sync_symptoms(es)

    # 确保所有分片 refresh，避免搜索立即可查不到
    await es.indices.refresh(index="yft_*")

    logger.info("ES 全量同步完成")


async def _sync_hospitals(es, session):
    result = await session.execute(
        select(HospitalModel).where(HospitalModel.is_deleted == 0)
    )
    hospitals = result.scalars().all()
    await delete_index(es, INDEX_HOSPITAL)
    await es.indices.create(index=INDEX_HOSPITAL, **INDEX_MAPPINGS[INDEX_HOSPITAL])
    docs = [
        HospitalDocument(
            id=h.id, hospital_name=h.hospital_name,
            hospital_level=h.hospital_level, address=h.address,
        ).model_dump()
        for h in hospitals
    ]
    await bulk_index(es, INDEX_HOSPITAL, docs)
    logger.info("ES 同步医院: %d 条", len(docs))


async def _sync_departments(es, session):
    result = await session.execute(
        select(DepartmentModel, HospitalModel.hospital_name)
        .join(HospitalModel, DepartmentModel.hospital_id == HospitalModel.id)
        .where(DepartmentModel.is_deleted == 0)
    )
    rows = result.all()
    await delete_index(es, INDEX_DEPARTMENT)
    await es.indices.create(index=INDEX_DEPARTMENT, **INDEX_MAPPINGS[INDEX_DEPARTMENT])
    docs = [
        DepartmentDocument(
            id=d.id, hospital_id=d.hospital_id,
            hospital_name=hn, dept_name=d.dept_name,
        ).model_dump()
        for d, hn in rows
    ]
    await bulk_index(es, INDEX_DEPARTMENT, docs)
    logger.info("ES 同步科室: %d 条", len(docs))


async def _sync_doctors(es, session):
    result = await session.execute(
        select(DoctorModel, DepartmentModel.dept_name, HospitalModel.id, HospitalModel.hospital_name)
        .join(DepartmentModel, DoctorModel.dept_id == DepartmentModel.id)
        .join(HospitalModel, DepartmentModel.hospital_id == HospitalModel.id)
        .where(DoctorModel.is_deleted == 0)
    )
    rows = result.all()
    await delete_index(es, INDEX_DOCTOR)
    await es.indices.create(index=INDEX_DOCTOR, **INDEX_MAPPINGS[INDEX_DOCTOR])
    docs = [
        DoctorDocument(
            id=d.id, dept_id=d.dept_id, hospital_id=hid,
            doctor_name=d.doctor_name, doctor_title=d.doctor_title,
            specialty=d.specialty,
            register_fee=float(d.register_fee) if d.register_fee else 0,
            doctor_avatar=d.doctor_avatar,
            dept_name=dn, hospital_name=hn,
        ).model_dump()
        for d, dn, hid, hn in rows
    ]
    await bulk_index(es, INDEX_DOCTOR, docs)
    logger.info("ES 同步医生: %d 条", len(docs))


async def _sync_symptoms(es):
    await delete_index(es, INDEX_SYMPTOM)
    await es.indices.create(index=INDEX_SYMPTOM, **INDEX_MAPPINGS[INDEX_SYMPTOM])
    docs = []
    for entry in SYMPTOM_MAP:
        doc_id = hashlib.md5(
            f"{'|'.join(entry['keywords'])}|{entry['dept_name']}".encode()
        ).hexdigest()[:16]
        docs.append(SymptomDocument(
            id=doc_id,
            keywords=entry["keywords"],
            dept_name=entry["dept_name"],
            weight=entry["weight"],
        ).model_dump())
    await bulk_index(es, INDEX_SYMPTOM, docs)
    logger.info("ES 同步症状词库: %d 条", len(docs))
