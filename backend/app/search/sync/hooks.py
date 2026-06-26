"""ES 增量同步钩子

在 hospital/department/doctor 模块的 CUD 操作后调用。
ES 故障不影响主流程（try/except + log warning），漏同步由下次全量同步补齐。
"""

import logging
from elasticsearch import ConnectionError as ESConnectionError, TransportError
from app.shared.elasticsearch import get_es, INDEX_HOSPITAL, INDEX_DEPARTMENT, INDEX_DOCTOR
from app.search.repository import index_document, delete_document

logger = logging.getLogger(__name__)

# 只捕获 ES 基础设施异常，编程错误（AttributeError 等）不吞掉
_ES_ERRORS = (ESConnectionError, TransportError)


# ═══════════════════════════════════════════════════════════════
#  医院
# ═══════════════════════════════════════════════════════════════

async def sync_hospital_create(hospital):
    """医院新增 → ES 索引"""
    try:
        es = await get_es()
        await index_document(es, INDEX_HOSPITAL, hospital.id, {
            "id": hospital.id,
            "hospital_name": hospital.hospital_name,
            "hospital_level": hospital.hospital_level,
            "address": hospital.address,
        })
    except _ES_ERRORS:
        logger.warning("ES 同步医院 create(%d) 失败", hospital.id, exc_info=True)


async def sync_hospital_update(hospital):
    """医院更新 → ES 覆盖（index 同 ID 即更新）"""
    await sync_hospital_create(hospital)


async def sync_hospital_delete(hospital_id: int):
    """医院删除 → ES 移除"""
    try:
        es = await get_es()
        await delete_document(es, INDEX_HOSPITAL, hospital_id)
    except _ES_ERRORS:
        logger.warning("ES 同步医院 delete(%d) 失败", hospital_id, exc_info=True)


# ═══════════════════════════════════════════════════════════════
#  科室
# ═══════════════════════════════════════════════════════════════

async def sync_department_create(dept, hospital_name: str):
    """科室新增 → ES 索引"""
    try:
        es = await get_es()
        await index_document(es, INDEX_DEPARTMENT, dept.id, {
            "id": dept.id,
            "hospital_id": dept.hospital_id,
            "hospital_name": hospital_name,
            "dept_name": dept.dept_name,
        })
    except _ES_ERRORS:
        logger.warning("ES 同步科室 create(%d) 失败", dept.id, exc_info=True)


async def sync_department_update(dept, hospital_name: str):
    """科室更新 → ES 覆盖"""
    await sync_department_create(dept, hospital_name)


async def sync_department_delete(dept_id: int):
    """科室删除 → ES 移除"""
    try:
        es = await get_es()
        await delete_document(es, INDEX_DEPARTMENT, dept_id)
    except _ES_ERRORS:
        logger.warning("ES 同步科室 delete(%d) 失败", dept_id, exc_info=True)


# ═══════════════════════════════════════════════════════════════
#  医生
# ═══════════════════════════════════════════════════════════════

async def sync_doctor_create(doctor, dept_name: str, hospital_id: int, hospital_name: str):
    """医生新增 → ES 索引"""
    try:
        es = await get_es()
        await index_document(es, INDEX_DOCTOR, doctor.id, {
            "id": doctor.id,
            "dept_id": doctor.dept_id,
            "hospital_id": hospital_id,
            "doctor_name": doctor.doctor_name,
            "doctor_title": doctor.doctor_title,
            "specialty": doctor.specialty,
            "register_fee": float(doctor.register_fee) if doctor.register_fee else 0,
            "doctor_avatar": doctor.doctor_avatar,
            "dept_name": dept_name,
            "hospital_name": hospital_name,
        })
    except _ES_ERRORS:
        logger.warning("ES 同步医生 create(%d) 失败", doctor.id, exc_info=True)


async def sync_doctor_update(doctor, dept_name: str, hospital_id: int, hospital_name: str):
    """医生更新 → ES 覆盖"""
    await sync_doctor_create(doctor, dept_name, hospital_id, hospital_name)


async def sync_doctor_delete(doctor_id: int):
    """医生删除 → ES 移除"""
    try:
        es = await get_es()
        await delete_document(es, INDEX_DOCTOR, doctor_id)
    except _ES_ERRORS:
        logger.warning("ES 同步医生 delete(%d) 失败", doctor_id, exc_info=True)
