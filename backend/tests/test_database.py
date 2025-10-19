import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from database.supabase_client import SupabaseDB
from models import Tool, AnalysisLog


class TestSupabaseDB:
    """Supabase数据库客户端测试"""

    @pytest.fixture
    def db(self):
        with patch('database.supabase_client.create_client'):
            return SupabaseDB(url="test_url", key="test_key")

    @pytest.fixture
    def sample_tools(self):
        """示例工具数据"""
        return [
            Tool(
                id=1,
                tool_name="AI Tool",
                description="Test AI tool",
                category="Productivity",
                votes=100,
                link="https://example.com",
                trend_signal="Rising",
                pain_point="Test pain point",
                micro_saas_ideas=["Idea 1", "Idea 2"],
                date=datetime.now(),
                created_at=datetime.now()
            )
        ]

    @pytest.fixture
    def sample_analysis_log(self):
        """示例分析日志"""
        return AnalysisLog(
            date=datetime.now(),
            tools_analyzed=10,
            tokens_used=1000,
            cost_usd=0.05,
            status="success"
        )

    @pytest.mark.asyncio
    async def test_insert_tools_success(self, db, sample_tools):
        """测试成功插入工具"""
        mock_result = Mock()
        mock_result.data = [{"id": 1}, {"id": 2}]  # 返回插入的记录
        db.client.table.return_value.insert.return_value.execute.return_value = mock_result

        success = await db.insert_tools(sample_tools)
        assert success is True

    @pytest.mark.asyncio
    async def test_insert_tools_partial_failure(self, db, sample_tools):
        """测试部分插入失败"""
        mock_result = Mock()
        mock_result.data = [{"id": 1}]  # 只插入了一条记录
        db.client.table.return_value.insert.return_value.execute.return_value = mock_result

        success = await db.insert_tools(sample_tools)
        assert success is False  # 部分失败也算失败

    @pytest.mark.asyncio
    async def test_insert_tools_exception(self, db, sample_tools):
        """测试插入工具异常"""
        db.client.table.return_value.insert.return_value.execute.side_effect = Exception("Database error")

        success = await db.insert_tools(sample_tools)
        assert success is False

    @pytest.mark.asyncio
    async def test_get_latest_tools(self, db):
        """测试获取最新工具"""
        mock_data = [
            {
                "id": 1,
                "tool_name": "AI Tool",
                "category": "Productivity",
                "created_at": "2024-01-15T10:00:00Z"
            }
        ]
        mock_result = Mock()
        mock_result.data = mock_data
        db.client.table.return_value.select.return_value.order.return_value.limit.return_value.execute.return_value = mock_result

        tools = await db.get_latest_tools(limit=10)
        assert len(tools) == 1
        assert tools[0]["tool_name"] == "AI Tool"

        # 验证调用链
        db.client.table.assert_called_with("tools")
        db.client.table.return_value.select.assert_called_with("*")
        db.client.table.return_value.select.return_value.order.assert_called_with("date", desc=True)

    @pytest.mark.asyncio
    async def test_get_tools_by_category(self, db):
        """测试按分类获取工具"""
        mock_data = [
            {
                "id": 1,
                "tool_name": "Productivity Tool",
                "category": "Productivity"
            }
        ]
        mock_result = Mock()
        mock_result.data = mock_data
        db.client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_result

        tools = await db.get_tools_by_category("Productivity")
        assert len(tools) == 1
        assert tools[0]["category"] == "Productivity"

    @pytest.mark.asyncio
    async def test_get_trending_tools(self, db):
        """测试获取趋势工具"""
        mock_data = [
            {
                "id": 1,
                "tool_name": "Trending Tool",
                "trend_signal": "Rising",
                "votes": 150
            }
        ]
        mock_result = Mock()
        mock_result.data = mock_data
        db.client.table.return_value.select.return_value.eq.return_value.gte.return_value.order.return_value.limit.return_value.execute.return_value = mock_result

        tools = await db.get_trending_tools(days=7)
        assert len(tools) == 1
        assert tools[0]["trend_signal"] == "Rising"

    @pytest.mark.asyncio
    async def test_get_tools_by_date(self, db):
        """测试按日期获取工具"""
        date = "2024-01-15"
        mock_data = [
            {
                "id": 1,
                "tool_name": "Today Tool",
                "date": date
            }
        ]
        mock_result = Mock()
        mock_result.data = mock_data
        db.client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_result

        tools = await db.get_tools_by_date(date)
        assert len(tools) == 1
        assert tools[0]["date"] == date

    @pytest.mark.asyncio
    async def test_get_categories(self, db):
        """测试获取分类"""
        mock_data = [
            {"id": 1, "name": "Productivity", "color": "#f59e0b"},
            {"id": 2, "name": "Video", "color": "#ef4444"}
        ]
        mock_result = Mock()
        mock_result.data = mock_data
        db.client.table.return_value.select.return_value.order.return_value.execute.return_value = mock_result

        categories = await db.get_categories()
        assert len(categories) == 2
        assert categories[0]["name"] == "Productivity"

    @pytest.mark.asyncio
    async def test_get_stats(self, db):
        """测试获取统计信息"""
        # Mock total count
        mock_total = Mock()
        mock_total.count = 100
        db.client.table.return_value.select.return_value.execute.return_value = mock_total

        # Mock today count
        mock_today = Mock()
        mock_today.count = 10
        db.client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_today

        # Mock category stats
        mock_category = Mock()
        mock_category.data = [
            {"category": "Productivity"},
            {"category": "Productivity"},
            {"category": "Video"}
        ]
        db.client.table.return_value.select.return_value.execute.return_value = mock_category

        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value.date.return_value.isoformat.return_value = "2024-01-15"

            stats = await db.get_stats()
            assert "total_tools" in stats
            assert "today_tools" in stats
            assert "category_stats" in stats
            assert "trend_stats" in stats

    @pytest.mark.asyncio
    async def test_insert_analysis_log(self, db, sample_analysis_log):
        """测试插入分析日志"""
        mock_result = Mock()
        mock_result.data = [{"id": 1}]
        db.client.table.return_value.insert.return_value.execute.return_value = mock_result

        success = await db.insert_analysis_log(sample_analysis_log)
        assert success is True

    @pytest.mark.asyncio
    async def test_tool_exists(self, db):
        """测试检查工具是否存在"""
        mock_result = Mock()
        mock_result.data = [{"id": 1}]  # 工具存在
        db.client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result

        exists = await db.tool_exists("AI Tool", "https://example.com")
        assert exists is True

        # 测试工具不存在
        mock_result.data = []
        exists = await db.tool_exists("Non-existent Tool", "https://example.com")
        assert exists is False

    @pytest.mark.asyncio
    async def test_upsert_tool_update_existing(self, db):
        """测试更新现有工具"""
        mock_result = Mock()
        mock_result.data = [{"id": 1}]  # 更新成功
        db.client.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result

        tool = Tool(
            tool_name="AI Tool",
            description="Updated description",
            category="Productivity",
            votes=150,
            link="https://example.com",
            trend_signal="Rising",
            pain_point="Updated pain point",
            micro_saas_ideas=["New idea"],
            date=datetime.now(),
            created_at=datetime.now()
        )

        success = await db.upsert_tool(tool)
        assert success is True

    @pytest.mark.asyncio
    async def test_upsert_tool_insert_new(self, db):
        """测试插入新工具"""
        # 先模拟更新失败（没有找到记录）
        mock_update_result = Mock()
        mock_update_result.data = []  # 没有更新任何记录
        db.client.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = mock_update_result

        # 再模拟插入成功
        mock_insert_result = Mock()
        mock_insert_result.data = [{"id": 1}]
        db.client.table.return_value.insert.return_value.execute.return_value = mock_insert_result

        tool = Tool(
            tool_name="New AI Tool",
            description="New description",
            category="Productivity",
            votes=100,
            link="https://example.com/new",
            trend_signal="Rising",
            pain_point="New pain point",
            micro_saas_ideas=["New idea"],
            date=datetime.now(),
            created_at=datetime.now()
        )

        success = await db.upsert_tool(tool)
        assert success is True

    @pytest.mark.asyncio
    async def test_delete_old_tools(self, db):
        """测试删除旧工具"""
        mock_result = Mock()
        mock_result.data = [{"id": 1}, {"id": 2}]  # 删除了2条记录
        db.client.table.return_value.delete.return_value.lt.return_value.execute.return_value = mock_result

        deleted_count = await db.delete_old_tools(days=30)
        assert deleted_count == 2

    @pytest.mark.asyncio
    async def test_delete_old_tools_exception(self, db):
        """测试删除旧工具异常"""
        db.client.table.return_value.delete.return_value.lt.return_value.execute.side_effect = Exception("Delete error")

        deleted_count = await db.delete_old_tools(days=30)
        assert deleted_count == 0


class TestGlobalDBInstance:
    """测试全局数据库实例"""

    def test_global_db_instance(self):
        """测试全局数据库实例创建"""
        with patch('database.supabase_client.create_client'):
            from database.supabase_client import db
            assert db is not None
            assert hasattr(db, 'client')


if __name__ == "__main__":
    pytest.main([__file__])