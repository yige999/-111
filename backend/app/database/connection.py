import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncpg
from supabase import create_client, Client

from ..core.config import settings
from ..models.tool import Tool, ToolCreate, ToolUpdate, ToolResponse, Category, TrendSignal

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器"""

    def __init__(self):
        self.supabase: Optional[Client] = None
        self.pool: Optional[asyncpg.pool.Pool] = None

    async def initialize(self):
        """初始化数据库连接"""
        try:
            # 初始化 Supabase 客户端
            self.supabase = create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_KEY
            )
            logger.info("Supabase 客户端初始化成功")

            # 这里也可以初始化 PostgreSQL 连接池用于复杂查询
            # self.pool = await asyncpg.create_pool(
            #     database_url,
            #     min_size=5,
            #     max_size=20
            # )

        except Exception as e:
            logger.error(f"数据库连接初始化失败: {e}")
            raise

    async def close(self):
        """关闭数据库连接"""
        if self.pool:
            await self.pool.close()
        logger.info("数据库连接已关闭")

    # ==================== 工具数据操作 ====================

    async def create_tool(self, tool_data: ToolCreate) -> ToolResponse:
        """创建工具记录"""
        try:
            data = tool_data.dict()
            if data.get("date"):
                data["date"] = data["date"].isoformat()

            response = self.supabase.table("tools").insert(data).execute()

            if response.data:
                return ToolResponse(**response.data[0])
            else:
                raise Exception("创建工具记录失败")

        except Exception as e:
            logger.error(f"创建工具记录失败: {e}")
            raise

    async def get_tool_by_id(self, tool_id: int) -> Optional[ToolResponse]:
        """根据ID获取工具"""
        try:
            response = self.supabase.table("tools").select("*").eq("id", tool_id).execute()

            if response.data:
                return ToolResponse(**response.data[0])
            return None

        except Exception as e:
            logger.error(f"获取工具失败: {e}")
            raise

  
    async def update_tool(self, tool_id: int, tool_data: ToolUpdate) -> Optional[ToolResponse]:
        """更新工具信息"""
        try:
            update_data = {k: v for k, v in tool_data.dict().items() if v is not None}

            response = self.supabase.table("tools")\
                .update(update_data)\
                .eq("id", tool_id)\
                .execute()

            if response.data:
                return ToolResponse(**response.data[0])
            return None

        except Exception as e:
            logger.error(f"更新工具失败: {e}")
            raise

    async def batch_create_tools(self, tools_data: List[ToolCreate]) -> List[ToolResponse]:
        """批量创建工具记录"""
        try:
            data_list = []
            for tool_data in tools_data:
                data = tool_data.dict()
                if data.get("date"):
                    data["date"] = data["date"].isoformat()
                data_list.append(data)

            response = self.supabase.table("tools").insert(data_list).execute()

            return [ToolResponse(**item) for item in response.data]

        except Exception as e:
            logger.error(f"批量创建工具失败: {e}")
            raise

    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            # 总工具数
            total_response = self.supabase.table("tools").select("id", count="exact").execute()
            total_count = total_response.count if total_response.count else 0

            # 今日新增
            today = datetime.utcnow().strftime("%Y-%m-%d")
            today_response = self.supabase.table("tools")\
                .select("id", count="exact")\
                .gte("date", f"{today}T00:00:00Z")\
                .execute()
            today_count = today_response.count if today_response.count else 0

            # 分类统计
            category_response = self.supabase.table("tools")\
                .select("category")\
                .execute()

            category_stats = {}
            for item in category_response.data:
                cat = item.get("category", "Unknown")
                category_stats[cat] = category_stats.get(cat, 0) + 1

            return {
                "total_tools": total_count,
                "today_new": today_count,
                "category_stats": category_stats,
                "last_updated": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            raise

    # ==================== API路由需要的额外方法 ====================

    async def get_latest_tools(self, limit: int = 10, offset: int = 0) -> List[ToolResponse]:
        """获取最新工具（支持分页）"""
        try:
            response = self.supabase.table("tools")\
                .select("*")\
                .order("date", desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()

            return [ToolResponse(**item) for item in response.data]

        except Exception as e:
            logger.error(f"获取最新工具失败: {e}")
            raise

    async def get_tools_by_category(self, category: str, start_date: datetime, limit: int = 20) -> List[ToolResponse]:
        """根据分类和时间范围获取工具"""
        try:
            response = self.supabase.table("tools")\
                .select("*")\
                .eq("category", category)\
                .gte("date", start_date.isoformat())\
                .order("votes", desc=True)\
                .limit(limit)\
                .execute()

            return [ToolResponse(**item) for item in response.data]

        except Exception as e:
            logger.error(f"根据分类获取工具失败: {e}")
            raise

    async def get_trending_tools(self, start_date: datetime, category: Optional[str] = None,
                               min_votes: int = 10, limit: int = 20) -> List[ToolResponse]:
        """获取趋势工具"""
        try:
            query = self.supabase.table("tools")\
                .select("*")\
                .gte("date", start_date.isoformat())\
                .gte("votes", min_votes)\
                .in_("trend_signal", ["Rising", "Stable"])

            if category:
                query = query.eq("category", category)

            response = query.order("votes", desc=True).limit(limit).execute()

            return [ToolResponse(**item) for item in response.data]

        except Exception as e:
            logger.error(f"获取趋势工具失败: {e}")
            raise

    async def get_tools_by_date(self, target_date: datetime) -> List[ToolResponse]:
        """根据日期获取工具"""
        try:
            date_str = target_date.strftime("%Y-%m-%d")
            start_datetime = f"{date_str}T00:00:00Z"
            end_datetime = f"{date_str}T23:59:59Z"

            response = self.supabase.table("tools")\
                .select("*")\
                .gte("date", start_datetime)\
                .lte("date", end_datetime)\
                .order("votes", desc=True)\
                .execute()

            return [ToolResponse(**item) for item in response.data]

        except Exception as e:
            logger.error(f"根据日期获取工具失败: {e}")
            raise

    async def search_tools(self, query: str, category: Optional[str] = None, limit: int = 20) -> List[ToolResponse]:
        """搜索工具"""
        try:
            search_query = self.supabase.table("tools")\
                .select("*")\
                .or(f"tool_name.ilike.%{query}%,description.ilike.%{query}%")

            if category:
                search_query = search_query.eq("category", category)

            response = search_query.order("votes", desc=True).limit(limit).execute()

            return [ToolResponse(**item) for item in response.data]

        except Exception as e:
            logger.error(f"搜索工具失败: {e}")
            raise

    async def insert_tools_batch(self, tools_data: List[Dict[str, Any]]) -> int:
        """批量插入工具数据"""
        try:
            # 转换日期格式
            for tool in tools_data:
                if isinstance(tool.get('date'), datetime):
                    tool['date'] = tool['date'].isoformat()
                if tool.get('created_at') and isinstance(tool['created_at'], datetime):
                    tool['created_at'] = tool['created_at'].isoformat()

            response = self.supabase.table("tools").insert(tools_data).execute()

            if response.data:
                logger.info(f"批量插入工具成功，插入 {len(response.data)} 条记录")
                return len(response.data)
            else:
                logger.warning("批量插入工具未返回数据")
                return 0

        except Exception as e:
            logger.error(f"批量插入工具失败: {e}")
            raise

    async def is_refreshing(self) -> bool:
        """检查是否正在刷新数据"""
        try:
            # 这里可以使用 Redis 或数据库记录来检查刷新状态
            # 暂时返回 False，表示没有正在进行的刷新
            return False

        except Exception as e:
            logger.error(f"检查刷新状态失败: {e}")
            return False

    async def set_refreshing_status(self, status: bool) -> None:
        """设置刷新状态"""
        try:
            # 这里可以使用 Redis 或数据库记录来设置刷新状态
            # 暂时只记录日志
            logger.info(f"设置刷新状态: {status}")

        except Exception as e:
            logger.error(f"设置刷新状态失败: {e}")

    async def log_analysis(self, tools_analyzed: int, duration_seconds: float,
                          status: str, error_message: Optional[str] = None) -> None:
        """记录分析日志"""
        try:
            log_data = {
                "date": datetime.utcnow().isoformat(),
                "tools_analyzed": tools_analyzed,
                "duration_seconds": duration_seconds,
                "status": status,
                "error_message": error_message
            }

            # 记录到 analysis_logs 表
            self.supabase.table("analysis_logs").insert(log_data).execute()

        except Exception as e:
            logger.error(f"记录分析日志失败: {e}")

    async def get_tools_statistics(self, start_date: datetime) -> Dict[str, Any]:
        """获取工具统计信息"""
        try:
            # 基础统计
            total_response = self.supabase.table("tools")\
                .select("id", count="exact")\
                .gte("date", start_date.isoformat())\
                .execute()

            total_count = total_response.count if total_response.count else 0

            # 分类统计
            category_response = self.supabase.table("tools")\
                .select("category, trend_signal, votes")\
                .gte("date", start_date.isoformat())\
                .execute()

            category_stats = {}
            trend_stats = {"Rising": 0, "Stable": 0, "Declining": 0}
            total_votes = 0

            for item in category_response.data:
                cat = item.get("category", "Unknown")
                trend = item.get("trend_signal", "Unknown")
                votes = item.get("votes", 0)

                # 分类统计
                if cat not in category_stats:
                    category_stats[cat] = {"count": 0, "total_votes": 0, "trends": {"Rising": 0, "Stable": 0, "Declining": 0}}

                category_stats[cat]["count"] += 1
                category_stats[cat]["total_votes"] += votes
                total_votes += votes

                # 趋势统计
                if trend in trend_stats:
                    trend_stats[trend] += 1
                    category_stats[cat]["trends"][trend] += 1

            # 计算平均投票数
            avg_votes = total_votes / total_count if total_count > 0 else 0

            return {
                "total_tools": total_count,
                "total_votes": total_votes,
                "average_votes": round(avg_votes, 2),
                "category_stats": category_stats,
                "trend_stats": trend_stats,
                "period_start": start_date.isoformat(),
                "period_end": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"获取工具统计失败: {e}")
            raise

    # ==================== 健康检查相关方法 ====================

    async def health_check(self) -> bool:
        """数据库健康检查"""
        try:
            # 简单的查询测试
            response = self.supabase.table("tools").select("id").limit(1).execute()
            return True

        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            return False

    async def get_metrics(self) -> Dict[str, Any]:
        """获取数据库指标"""
        try:
            # 获取各种统计指标
            stats = await self.get_statistics()

            # 添加数据库特定指标
            metrics = {
                "database": {
                    "total_tools": stats.get("total_tools", 0),
                    "today_new": stats.get("today_new", 0),
                    "last_updated": stats.get("last_updated"),
                    "category_count": len(stats.get("category_stats", {}))
                }
            }

            return metrics

        except Exception as e:
            logger.error(f"获取数据库指标失败: {e}")
            return {"database": {"status": "error", "message": str(e)}}