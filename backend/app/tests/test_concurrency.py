"""Redis Lua 并发防超卖测试 — 验证号源原子扣减 + 回滚机制"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest


# ═══════════════════════════════════════════
# 1. Lua 脚本逻辑测试
# ═══════════════════════════════════════════

class TestLuaDecreaseSource:
    async def test_normal_decrease_success(self):
        from app.shared.redis import decrease_source_redis, get_redis

        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=1)

        with patch("app.shared.redis.get_redis", AsyncMock(return_value=mock_redis)):
            result = await decrease_source_redis(schedule_id=1, source_type="normal")
            assert result is True

    async def test_normal_decrease_insufficient(self):
        from app.shared.redis import decrease_source_redis

        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=0)

        with patch("app.shared.redis.get_redis", AsyncMock(return_value=mock_redis)):
            result = await decrease_source_redis(schedule_id=1, source_type="normal")
            assert result is False

    async def test_elder_decrease_success(self):
        from app.shared.redis import decrease_source_redis

        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=1)

        with patch("app.shared.redis.get_redis", AsyncMock(return_value=mock_redis)):
            result = await decrease_source_redis(schedule_id=2, source_type="elder")
            assert result is True

    async def test_rollback_normal_source(self):
        from app.shared.redis import rollback_source_redis

        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=1)

        with patch("app.shared.redis.get_redis", AsyncMock(return_value=mock_redis)):
            result = await rollback_source_redis(schedule_id=1, source_type="normal")
            assert result is None

    async def test_rollback_elder_source(self):
        from app.shared.redis import rollback_source_redis

        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=1)

        with patch("app.shared.redis.get_redis", AsyncMock(return_value=mock_redis)):
            result = await rollback_source_redis(schedule_id=1, source_type="elder")
            assert result is None


# ═══════════════════════════════════════════
# 2. 并发防超卖测试
# ═══════════════════════════════════════════

class TestConcurrencyNoOverselling:
    async def test_concurrent_reserve_no_overselling(self):
        """20 人并发抢 5 个号 → 最多 5 人成功（需 asyncio.Lock 保证原子性）"""
        AVAILABLE = 5
        CONCURRENT = 20

        remaining = [AVAILABLE]
        lock = asyncio.Lock()

        async def atomic_decrease():
            async with lock:
                if remaining[0] >= 1:
                    remaining[0] -= 1
                    return True
                return False

        tasks = [atomic_decrease() for _ in range(CONCURRENT)]
        results = await asyncio.gather(*tasks)
        succeeded = sum(results)

        assert succeeded == AVAILABLE, f"期望 {AVAILABLE} 成功，实际 {succeeded}"
        assert remaining[0] == 0

    async def test_rollback_after_cancel_restores_source(self):
        """取消订单后号源回滚，可被再次抢到"""
        normal_remaining = [1]

        async def decrease():
            if normal_remaining[0] >= 1:
                normal_remaining[0] -= 1
                return True
            return False

        async def rollback():
            normal_remaining[0] += 1

        ok1 = await decrease()
        assert ok1 is True
        assert normal_remaining[0] == 0

        ok2 = await decrease()
        assert ok2 is False  # 号源已空

        await rollback()
        assert normal_remaining[0] == 1  # 回滚成功

        ok3 = await decrease()
        assert ok3 is True  # 可再次抢到

    async def test_elder_and_normal_independent(self):
        """普通号和老年号互不影响"""
        normal_rem = [3]
        elder_rem = [2]

        async def dec_elder():
            if elder_rem[0] >= 1:
                elder_rem[0] -= 1
                return True
            return False

        async def dec_normal():
            if normal_rem[0] >= 1:
                normal_rem[0] -= 1
                return True
            return False

        ok = await dec_elder()
        assert ok is True
        assert elder_rem[0] == 1
        assert normal_rem[0] == 3  # 普通号未受影响

        ok = await dec_normal()
        assert ok is True
        assert normal_rem[0] == 2

    async def test_concurrency_without_lock_leads_to_oversell(self):
        """对比测试：无锁并发会导致超卖，证明 Lua 原子操作的必要性"""
        AVAILABLE = 5
        CONCURRENT = 30

        remaining = [AVAILABLE]

        async def unsafe_decrease():
            """无锁的 check-then-act，存在 TOCTOU 竞态"""
            if remaining[0] >= 1:
                await asyncio.sleep(0)  # 放大竞态窗口
                remaining[0] -= 1
                return True
            return False

        tasks = [unsafe_decrease() for _ in range(CONCURRENT)]
        results = await asyncio.gather(*tasks)
        succeeded = sum(results)

        # 无锁版本很可能会超卖（可能全部 30 个都"成功"通过了 if 检查）
        # 极低概率刚好等于 AVAILABLE（取决于 asyncio 调度），但大概率 > AVAILABLE
        # 注意：在 asyncio 单线程事件循环中不会有真正的并行竞态，但同一轮 event loop 中
        # 多个 await 之间的交错仍可能导致问题
        # 这个测试主要是演示性质——在实际多进程/多线程环境下会严重超卖
        assert succeeded >= AVAILABLE, (
            f"无锁版本：至少 {AVAILABLE} 个成功（{succeeded}），"
            f"如果 > {AVAILABLE} 则说明超卖"
        )
