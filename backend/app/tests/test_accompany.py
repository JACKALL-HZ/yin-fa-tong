"""陪诊模块单元测试 — 志愿者评分 / 订单 5 态流转 / 评价"""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.accompany.order import service as order_service
from app.accompany.volunteer import service as vol_service
from decimal import Decimal


# ── helpers: 属性必须为真实类型，否则 Pydantic 校验失败 ──

def _mock_volunteer(id_=1, status=1, score=Decimal("4.5"), count=10):
    v = MagicMock()
    v.id = id_
    v.vol_name = f"志愿者{id_}"
    v.vol_phone = "13800000000"
    v.service_dept = "心血管内科"
    v.avatar = "https://example.com/avatar.jpg"
    v.service_score = score
    v.service_count = count
    v.status = status
    v.service_desc = "热心陪诊"
    v.is_deleted = 0
    v.create_time = "2026-01-01"
    v.update_time = "2026-01-01"
    return v


def _mock_order(id_=1, user_id=100, elder_bind_id=1, volunteer_id=1,
                order_status=1, service_score=None, service_comment=None):
    o = MagicMock()
    o.id = id_
    o.user_id = user_id
    o.elder_bind_id = elder_bind_id
    o.volunteer_id = volunteer_id
    o.accompany_date = "2026-07-15"
    o.order_status = order_status
    o.service_score = service_score
    o.service_comment = service_comment
    o.create_time = "2026-01-01"
    o.update_time = "2026-01-01"
    return o


# ═══════════════════════════════════════════
# 1. 志愿者服务测试
# ═══════════════════════════════════════════

class TestVolunteer:
    async def test_list_available(self, mock_session):
        v = _mock_volunteer()
        mock_session.execute = AsyncMock(return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[v])))))

        result = await vol_service.list_available(mock_session)
        assert len(result) == 1
        assert result[0].vol_name == "志愿者1"

    async def test_get_detail(self, mock_session):
        v = _mock_volunteer()
        mock_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=v)))

        result = await vol_service.get_detail(mock_session, 1)
        assert result.vol_name == "志愿者1"
        assert result.service_score == Decimal("4.5")

    async def test_get_detail_not_found(self, mock_session):
        from app.exception.base import NotFoundException
        mock_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)))
        with pytest.raises(NotFoundException):
            await vol_service.get_detail(mock_session, 9999)

    async def test_update_score_weighted_average(self, mock_session):
        from app.accompany.volunteer.repository import update_score

        vol = _mock_volunteer(score=Decimal("4.0"), count=5)
        # old_total = 4.0 * 5 = 20; new = 5; count = 6
        # expected = (20 + 5) / 6 = 25/6 ≈ 4.1667
        expected = (Decimal("4.0") * 5 + Decimal("5")) / 6

        with patch.object(mock_session, "flush", AsyncMock()):
            await update_score(mock_session, vol, 5)
            assert vol.service_score == expected
            assert vol.service_count == 6


# ═══════════════════════════════════════════
# 2. 陪诊订单 — 创建
# ═══════════════════════════════════════════

class TestCreateAccompanyOrder:
    async def test_create_success(self, mock_session):
        from app.accompany.order.schemas import AccompanyOrderCreate

        vol = _mock_volunteer(status=1)
        order_obj = _mock_order()
        elder_mock = MagicMock()
        elder_mock.elder_name = "张大爷"

        mock_session.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=vol)),    # get_volunteer
            MagicMock(scalar_one_or_none=MagicMock(return_value=elder_mock)),  # elder lookup
            MagicMock(scalar_one_or_none=MagicMock(return_value=vol)),    # vol lookup in _to_response
        ])

        with patch("app.accompany.order.repository.create", AsyncMock(return_value=order_obj)):
            req = AccompanyOrderCreate(volunteer_id=1, elder_bind_id=1, accompany_date="2026-07-15")
            result = await order_service.create_order(mock_session, user_id=100, req=req)

            assert result.id == 1
            assert result.order_status == 1
            assert result.status_text == "待审核"

    async def test_create_volunteer_unavailable(self, mock_session):
        from app.accompany.order.schemas import AccompanyOrderCreate
        from app.exception.base import BadRequestException

        vol = _mock_volunteer(status=2)
        mock_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=vol)))

        req = AccompanyOrderCreate(volunteer_id=1, elder_bind_id=1, accompany_date="2026-07-15")
        with pytest.raises(BadRequestException, match="不可预约"):
            await order_service.create_order(mock_session, user_id=100, req=req)

    async def test_create_volunteer_not_found(self, mock_session):
        from app.accompany.order.schemas import AccompanyOrderCreate
        from app.exception.base import BadRequestException

        mock_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)))

        req = AccompanyOrderCreate(volunteer_id=999, elder_bind_id=1, accompany_date="2026-07-15")
        with pytest.raises(BadRequestException, match="不可预约"):
            await order_service.create_order(mock_session, user_id=100, req=req)


# ═══════════════════════════════════════════
# 3. 订单 5 态流转
# ═══════════════════════════════════════════

class TestOrderStateFlow:
    async def test_approve_success(self, mock_session):
        order = _mock_order(order_status=1)
        updated = _mock_order(order_status=2)

        mock_session.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=order)),   # get_by_id
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),    # elder lookup
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),    # vol lookup
        ])

        with patch("app.accompany.order.repository.update_status", AsyncMock(return_value=updated)):
            result = await order_service.approve_order(mock_session, order_id=1)
            assert result.order_status == 2
            assert result.status_text == "待服务"

    async def test_approve_wrong_status(self, mock_session):
        from app.exception.base import BadRequestException
        order = _mock_order(order_status=3)
        mock_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=order)))
        with pytest.raises(BadRequestException, match="不允许审核"):
            await order_service.approve_order(mock_session, order_id=1)

    async def test_reject_success(self, mock_session):
        order = _mock_order(order_status=1)
        mock_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=order)))
        with patch("app.accompany.order.repository.update_status", AsyncMock()):
            result = await order_service.reject_order(mock_session, order_id=1)
            assert result is None

    async def test_start_service_success(self, mock_session):
        order = _mock_order(order_status=2)
        updated = _mock_order(order_status=3)

        mock_session.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=order)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
        ])

        with patch("app.accompany.order.repository.update_status", AsyncMock(return_value=updated)):
            result = await order_service.start_service(mock_session, order_id=1)
            assert result.order_status == 3
            assert result.status_text == "服务中"

    async def test_start_service_wrong_status(self, mock_session):
        from app.exception.base import BadRequestException
        order = _mock_order(order_status=1)
        mock_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=order)))
        with pytest.raises(BadRequestException, match="不允许开始服务"):
            await order_service.start_service(mock_session, order_id=1)

    async def test_submit_review_success(self, mock_session):
        from app.accompany.order.schemas import ReviewCreate

        order = _mock_order(order_status=3, service_score=None)
        reviewed = _mock_order(order_status=4, service_score=5, service_comment="很好")
        vol = _mock_volunteer()

        mock_session.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=order)),    # get_by_id
            MagicMock(scalar_one_or_none=MagicMock(return_value=vol)),      # get_volunteer for update_score
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),     # elder in _to_response
            MagicMock(scalar_one_or_none=MagicMock(return_value=vol)),      # vol in _to_response
        ])

        with patch("app.accompany.order.repository.submit_review", AsyncMock(return_value=reviewed)):
            with patch("app.accompany.volunteer.repository.update_score", AsyncMock()):
                req = ReviewCreate(service_score=5, service_comment="很好")
                result = await order_service.submit_review(mock_session, order_id=1, user_id=100, req=req)
                assert result.order_status == 4
                assert result.service_score == 5

    async def test_submit_review_double_review(self, mock_session):
        from app.accompany.order.schemas import ReviewCreate
        from app.exception.base import BadRequestException

        order = _mock_order(order_status=4, service_score=5)
        mock_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=order)))

        req = ReviewCreate(service_score=4, service_comment="再评一次")
        with pytest.raises(BadRequestException):
            await order_service.submit_review(mock_session, order_id=1, user_id=100, req=req)

    async def test_submit_review_wrong_user(self, mock_session):
        from app.accompany.order.schemas import ReviewCreate
        from app.exception.base import NotFoundException

        order = _mock_order(order_status=3, user_id=100)
        mock_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=order)))

        req = ReviewCreate(service_score=3)
        with pytest.raises(NotFoundException, match="不存在"):
            await order_service.submit_review(mock_session, order_id=1, user_id=999, req=req)


# ═══════════════════════════════════════════
# 4. 完整 5 态流程
# ═══════════════════════════════════════════

class TestFullFiveStateFlow:
    async def test_full_flow(self, mock_session):
        from app.accompany.order.schemas import AccompanyOrderCreate, ReviewCreate

        vol = _mock_volunteer(status=1)
        elder = MagicMock()
        elder.elder_name = "张大爷"

        order_1 = _mock_order(order_status=1, service_score=None)
        order_2 = _mock_order(order_status=2, service_score=None)
        order_3 = _mock_order(order_status=3, service_score=None)
        order_4 = _mock_order(order_status=4, service_score=5)

        # Need to carefully orchestrate execute returns per step
        # Step 1: create -> check vol(status=1) then elder+vol for _to_response
        mock_session.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=vol)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=elder)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=vol)),
        ])

        with patch("app.accompany.order.repository.create", AsyncMock(return_value=order_1)):
            req = AccompanyOrderCreate(volunteer_id=1, elder_bind_id=1, accompany_date="2026-07-15")
            created = await order_service.create_order(mock_session, user_id=100, req=req)
            assert created.order_status == 1

        # Step 2: approve
        mock_session.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=order_1)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=elder)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=vol)),
        ])
        with patch("app.accompany.order.repository.update_status", AsyncMock(return_value=order_2)):
            approved = await order_service.approve_order(mock_session, order_id=1)
            assert approved.order_status == 2

        # Step 3: start
        mock_session.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=order_2)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=elder)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=vol)),
        ])
        with patch("app.accompany.order.repository.update_status", AsyncMock(return_value=order_3)):
            started = await order_service.start_service(mock_session, order_id=1)
            assert started.order_status == 3

        # Step 4: review
        mock_session.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=order_3)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=vol)),  # for update_score
            MagicMock(scalar_one_or_none=MagicMock(return_value=elder)),  # elder
            MagicMock(scalar_one_or_none=MagicMock(return_value=vol)),  # vol
        ])
        with patch("app.accompany.order.repository.submit_review", AsyncMock(return_value=order_4)):
            with patch("app.accompany.volunteer.repository.update_score", AsyncMock()):
                review_req = ReviewCreate(service_score=5, service_comment="非常满意")
                reviewed = await order_service.submit_review(mock_session, order_id=1, user_id=100, req=review_req)
                assert reviewed.order_status == 4
                assert reviewed.service_score == 5
