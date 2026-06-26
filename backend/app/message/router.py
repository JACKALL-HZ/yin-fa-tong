"""消息中心路由层"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.shared.database import get_db
from app.shared.response import ApiResponse
from app.auth.service import get_current_user
from app.auth.models import UserModel
from app.message.models import MessageModel

router = APIRouter(prefix="/api/messages", tags=["消息中心"])


@router.get("", response_model=ApiResponse)
async def list_messages(
    msg_type: int | None = None,
    read_status: int | None = None,
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """我的消息列表"""
    stmt = select(MessageModel).where(
        MessageModel.user_id == current_user.id,
        MessageModel.is_deleted == 0,
    )
    if msg_type is not None:
        stmt = stmt.where(MessageModel.msg_type == msg_type)
    if read_status is not None:
        stmt = stmt.where(MessageModel.read_status == read_status)

    result = await session.execute(stmt.order_by(MessageModel.create_time.desc()))
    messages = result.scalars().all()
    data = [
        {
            "id": m.id,
            "msg_type": m.msg_type,
            "msg_content": m.msg_content,
            "read_status": m.read_status,
            "create_time": m.create_time.isoformat(),
        }
        for m in messages
    ]
    return ApiResponse.ok(data)


@router.post("/{msg_id}/read", response_model=ApiResponse)
async def mark_read(
    msg_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """标记消息为已读"""
    result = await session.execute(
        select(MessageModel).where(MessageModel.id == msg_id, MessageModel.user_id == current_user.id)
    )
    msg = result.scalar_one_or_none()
    if not msg:
        return ApiResponse.fail(404, "消息不存在")
    msg.read_status = 1
    await session.flush()
    return ApiResponse.ok(message="已标记为已读")


@router.get("/unread-count", response_model=ApiResponse)
async def unread_count(
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """未读消息数"""
    from sqlalchemy import func
    result = await session.execute(
        select(func.count(MessageModel.id)).where(
            MessageModel.user_id == current_user.id,
            MessageModel.read_status == 0,
            MessageModel.is_deleted == 0,
        )
    )
    count = result.scalar() or 0
    return ApiResponse.ok({"count": count})
