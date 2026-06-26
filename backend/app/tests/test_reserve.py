"""挂号预约模块单元测试 — 下单 / 状态流转 / 号源原子扣减 / 取消回滚"""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.reserve import service


# ── helpers ──────────────────────────────────────────────

def _mock_schedule():
    s = MagicMock()
    s.id = 1
    s.doctor_id = 10
    s.work_date = "2026-07-01"
    s.time_period = "1"          # string type per model
    s.normal_num = 20
    s.elder_priority_num = 5
    return s


def _mock_reserve(schedule_id=1, user_id=100, elder_bind_id=None, source_type="normal",
                  order_status=1, pay_status=1, queue_code="NK202607010001"):
    r = MagicMock()
    r.id = 1
    r.user_id = user_id
    r.schedule_id = schedule_id
    r.elder_bind_id = elder_bind_id
    r.source_type = source_type
    r.order_status = order_status
    r.pay_status = pay_status
    r.queue_status = 1
    r.queue_code = queue_code
    return r


# ═══════════════════════════════════════════
# 1. 预约下单
# ═══════════════════════════════════════════

class TestCreateReserve:
    async def test_create_reserve_success(self, mock_session):
        from app.reserve.schemas import ReserveCreateRequest

        sched = _mock_schedule()
        reserve = _mock_reserve()
        none_result = MagicMock(scalar_one_or_none=MagicMock(return_value=None))

        # Step 1: schedule lookup returns schedule
        # Step 2+: _build_response does doctor/dept/hospital/elder lookups
        mock_session.execute = AsyncMock(return_value=none_result)

        with patch("app.reserve.repository.create", AsyncMock(return_value=reserve)):
            with patch("app.reserve.repository.update_status", AsyncMock(return_value=reserve)):
                with patch("app.reserve.service.decrease_source_redis", AsyncMock(return_value=True)):
                    with patch("app.reserve.service.get_schedule", AsyncMock(return_value=sched)):
                        req = ReserveCreateRequest(schedule_id=1, source_type="normal")
                        result = await service.create_reserve(mock_session, user_id=100, req=req)

                        assert result.id == 1
                        assert result.queue_code == "NK202607010001"

    async def test_create_reserve_schedule_not_found(self, mock_session):
        from app.reserve.schemas import ReserveCreateRequest
        from app.exception.base import NotFoundException

        with patch("app.reserve.service.get_schedule", AsyncMock(return_value=None)):
            req = ReserveCreateRequest(schedule_id=9999, source_type="normal")
            with pytest.raises(NotFoundException):
                await service.create_reserve(mock_session, user_id=100, req=req)

    async def test_create_reserve_no_source_left(self, mock_session):
        from app.reserve.schemas import ReserveCreateRequest
        from app.exception.base import ConflictException

        with patch("app.reserve.service.get_schedule", AsyncMock(return_value=_mock_schedule())):
            with patch("app.reserve.service.decrease_source_redis", AsyncMock(return_value=False)):
                req = ReserveCreateRequest(schedule_id=1, source_type="normal")
                with pytest.raises(ConflictException):
                    await service.create_reserve(mock_session, user_id=100, req=req)

    async def test_create_reserve_rollback_on_db_failure(self, mock_session):
        from app.reserve.schemas import ReserveCreateRequest

        rollback_called = [False]

        async def mock_rollback(*args):
            rollback_called[0] = True

        with patch("app.reserve.service.get_schedule", AsyncMock(return_value=_mock_schedule())):
            with patch("app.reserve.service.decrease_source_redis", AsyncMock(return_value=True)):
                with patch("app.reserve.service.rollback_source_redis", AsyncMock(side_effect=mock_rollback)):
                    with patch("app.reserve.repository.create", AsyncMock(side_effect=Exception("DB crash"))):
                        req = ReserveCreateRequest(schedule_id=1, source_type="elder")
                        with pytest.raises(Exception):
                            await service.create_reserve(mock_session, user_id=100, req=req)
                        assert rollback_called[0] is True


# ═══════════════════════════════════════════
# 2. 支付
# ═══════════════════════════════════════════

class TestPayReserve:
    async def test_pay_success(self, mock_session):
        reserve = _mock_reserve(pay_status=1, order_status=1)
        updated = _mock_reserve(pay_status=2, order_status=2)
        none_result = MagicMock(scalar_one_or_none=MagicMock(return_value=None))

        mock_session.execute = AsyncMock(return_value=none_result)

        with patch("app.reserve.repository.get_by_id", AsyncMock(return_value=reserve)):
            with patch("app.reserve.repository.update_status", AsyncMock(return_value=updated)):
                result = await service.pay_reserve(mock_session, reserve_id=1, user_id=100)
                assert result.pay_status == 2
                assert result.order_status == 2

    async def test_pay_wrong_user(self, mock_session):
        from app.exception.base import NotFoundException

        reserve = _mock_reserve(user_id=100)
        with patch("app.reserve.repository.get_by_id", AsyncMock(return_value=reserve)):
            with pytest.raises(NotFoundException, match="不存在"):
                await service.pay_reserve(mock_session, reserve_id=1, user_id=999)

    async def test_pay_already_paid(self, mock_session):
        from app.exception.base import BadRequestException

        reserve = _mock_reserve(pay_status=2)
        with patch("app.reserve.repository.get_by_id", AsyncMock(return_value=reserve)):
            with pytest.raises(BadRequestException, match="不允许支付"):
                await service.pay_reserve(mock_session, reserve_id=1, user_id=100)


# ═══════════════════════════════════════════
# 3. 取消订单
# ═══════════════════════════════════════════

class TestCancelReserve:
    async def test_cancel_success(self, mock_session):
        reserve = _mock_reserve(order_status=1)

        with patch("app.reserve.repository.get_by_id", AsyncMock(return_value=reserve)):
            with patch("app.reserve.service.rollback_source_redis", AsyncMock()):
                with patch("app.reserve.repository.update_status", AsyncMock()):
                    result = await service.cancel_reserve(mock_session, reserve_id=1, user_id=100)
                    assert result is None

    async def test_cancel_already_cancelled(self, mock_session):
        from app.exception.base import BadRequestException

        reserve = _mock_reserve(order_status=4)
        with patch("app.reserve.repository.get_by_id", AsyncMock(return_value=reserve)):
            with pytest.raises(BadRequestException, match="已取消"):
                await service.cancel_reserve(mock_session, reserve_id=1, user_id=100)

    async def test_cancel_wrong_user(self, mock_session):
        from app.exception.base import NotFoundException

        reserve = _mock_reserve(user_id=100)
        with patch("app.reserve.repository.get_by_id", AsyncMock(return_value=reserve)):
            with pytest.raises(NotFoundException):
                await service.cancel_reserve(mock_session, reserve_id=1, user_id=999)


# ═══════════════════════════════════════════
# 4. 列表 / 详情
# ═══════════════════════════════════════════

class TestListAndDetail:
    async def test_list_my_reserves(self, mock_session):
        reserve = _mock_reserve()
        none_result = MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        mock_session.execute = AsyncMock(return_value=none_result)

        with patch("app.reserve.repository.list_by_user", AsyncMock(return_value=[reserve])):
            result = await service.list_my_reserves(mock_session, user_id=100)
            assert isinstance(result, list)
            assert len(result) == 1

    async def test_get_detail_not_found(self, mock_session):
        from app.exception.base import NotFoundException
        with patch("app.reserve.repository.get_by_id", AsyncMock(return_value=None)):
            with pytest.raises(NotFoundException):
                await service.get_reserve_detail(mock_session, reserve_id=999, user_id=100)


# ═══════════════════════════════════════════
# 5. 候诊编号生成
# ═══════════════════════════════════════════

class TestQueueCode:
    def test_format(self):
        from app.reserve.service import _generate_queue_code
        code = _generate_queue_code(42)
        assert code.startswith("NK")
        assert code.endswith("0042")
        assert len(code) > 10

    def test_uniqueness_same_day(self):
        from app.reserve.service import _generate_queue_code
        c1 = _generate_queue_code(1)
        c2 = _generate_queue_code(2)
        assert c1 != c2
        assert c1[:-4] == c2[:-4]


# ═══════════════════════════════════════════
# 6. 订单状态流转完整性
# ═══════════════════════════════════════════

class TestStateTransitions:
    async def test_full_flow_normal(self, mock_session):
        from app.reserve.schemas import ReserveCreateRequest

        schedule = _mock_schedule()
        reserve = _mock_reserve(pay_status=1, order_status=1)
        reserve_paid = _mock_reserve(pay_status=2, order_status=2)
        none_result = MagicMock(scalar_one_or_none=MagicMock(return_value=None))

        mock_session.execute = AsyncMock(return_value=none_result)

        # Step 1
        with patch("app.reserve.service.get_schedule", AsyncMock(return_value=schedule)):
            with patch("app.reserve.repository.create", AsyncMock(return_value=reserve)):
                with patch("app.reserve.repository.update_status", AsyncMock(return_value=reserve)):
                    with patch("app.reserve.service.decrease_source_redis", AsyncMock(return_value=True)):
                        req = ReserveCreateRequest(schedule_id=1, source_type="normal")
                        created = await service.create_reserve(mock_session, user_id=100, req=req)
                        assert created.order_status == 1

        # Step 2
        with patch("app.reserve.repository.get_by_id", AsyncMock(return_value=reserve)):
            with patch("app.reserve.repository.update_status", AsyncMock(return_value=reserve_paid)):
                paid = await service.pay_reserve(mock_session, reserve_id=1, user_id=100)
                assert paid.pay_status == 2
                assert paid.order_status == 2
