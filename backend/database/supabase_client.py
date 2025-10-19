from supabase import create_client, Client
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from ..models import Tool, AnalysisLog
from ..config import settings

logger = logging.getLogger(__name__)


class SupabaseDB:
    """Supabase数据库客户端"""

    def __init__(self, url: str = None, key: str = None):
        self.client: Client = create_client(
            url or settings.supabase_url,
            key or settings.supabase_key
        )

    async def insert_tools(self, tools: List[Tool]) -> bool:
        """批量插入工具数据"""
        try:
            # 转换为字典格式
            tools_data = []
            for tool in tools:
                tool_dict = {
                    "tool_name": tool.tool_name,
                    "description": tool.description,
                    "category": tool.category,
                    "votes": tool.votes,
                    "link": tool.link,
                    "trend_signal": tool.trend_signal,
                    "pain_point": tool.pain_point,
                    "micro_saas_ideas": tool.micro_saas_ideas,
                    "date": tool.date.isoformat(),
                    "created_at": datetime.now().isoformat()
                }
                tools_data.append(tool_dict)

            # 批量插入
            result = self.client.table("tools").insert(tools_data).execute()

            if len(result.data) == len(tools_data):
                logger.info(f"成功插入 {len(tools_data)} 个工具到数据库")
                return True
            else:
                logger.warning(f"只插入了 {len(result.data)}/{len(tools_data)} 个工具")
                return False

        except Exception as e:
            logger.error(f"插入工具数据失败: {e}")
            return False

    async def get_latest_tools(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最新工具"""
        try:
            result = (
                self.client.table("tools")
                .select("*")
                .order("date", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data

        except Exception as e:
            logger.error(f"获取最新工具失败: {e}")
            return []

    async def get_tools_by_category(self, category: str, limit: int = 50) -> List[Dict[str, Any]]:
        """按分类获取工具"""
        try:
            result = (
                self.client.table("tools")
                .select("*")
                .eq("category", category)
                .order("date", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data

        except Exception as e:
            logger.error(f"按分类获取工具失败: {e}")
            return []

    async def get_trending_tools(self, days: int = 7, limit: int = 50) -> List[Dict[str, Any]]:
        """获取趋势工具"""
        try:
            result = (
                self.client.table("tools")
                .select("*")
                .eq("trend_signal", "Rising")
                .gte("date", datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat())
                .order("votes", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data

        except Exception as e:
            logger.error(f"获取趋势工具失败: {e}")
            return []

    async def get_tools_by_date(self, date: str, limit: int = 50) -> List[Dict[str, Any]]:
        """按日期获取工具"""
        try:
            result = (
                self.client.table("tools")
                .select("*")
                .eq("date", date)
                .order("votes", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data

        except Exception as e:
            logger.error(f"按日期获取工具失败: {e}")
            return []

    async def get_categories(self) -> List[Dict[str, Any]]:
        """获取所有分类"""
        try:
            result = (
                self.client.table("categories")
                .select("*")
                .order("name")
                .execute()
            )
            return result.data

        except Exception as e:
            logger.error(f"获取分类失败: {e}")
            return []

    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            # 总工具数
            total_result = self.client.table("tools").select("id", count="exact").execute()
            total_tools = total_result.count

            # 今日工具数
            today = datetime.now().date().isoformat()
            today_result = (
                self.client.table("tools")
                .select("id", count="exact")
                .eq("date", today)
                .execute()
            )
            today_tools = today_result.count

            # 按分类统计
            category_result = (
                self.client.table("tools")
                .select("category", count="exact")
                .execute()
            )
            category_stats = {}
            for item in category_result.data:
                category = item["category"]
                category_stats[category] = category_stats.get(category, 0) + 1

            # 按趋势信号统计
            trend_result = (
                self.client.table("tools")
                .select("trend_signal", count="exact")
                .execute()
            )
            trend_stats = {}
            for item in trend_result.data:
                trend = item["trend_signal"]
                trend_stats[trend] = trend_stats.get(trend, 0) + 1

            return {
                "total_tools": total_tools,
                "today_tools": today_tools,
                "category_stats": category_stats,
                "trend_stats": trend_stats
            }

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}

    async def insert_analysis_log(self, log: AnalysisLog) -> bool:
        """插入分析日志"""
        try:
            log_data = {
                "date": log.date.isoformat(),
                "tools_analyzed": log.tools_analyzed,
                "tokens_used": log.tokens_used,
                "cost_usd": log.cost_usd,
                "status": log.status,
                "error_message": log.error_message,
                "created_at": datetime.now().isoformat()
            }

            result = self.client.table("analysis_logs").insert(log_data).execute()
            return len(result.data) > 0

        except Exception as e:
            logger.error(f"插入分析日志失败: {e}")
            return False

    async def tool_exists(self, tool_name: str, link: str) -> bool:
        """检查工具是否已存在"""
        try:
            result = (
                self.client.table("tools")
                .select("id")
                .eq("tool_name", tool_name)
                .eq("link", link)
                .execute()
            )
            return len(result.data) > 0

        except Exception as e:
            logger.error(f"检查工具存在性失败: {e}")
            return False

    async def upsert_tool(self, tool: Tool) -> bool:
        """插入或更新工具"""
        try:
            tool_data = {
                "tool_name": tool.tool_name,
                "description": tool.description,
                "category": tool.category,
                "votes": tool.votes,
                "link": tool.link,
                "trend_signal": tool.trend_signal,
                "pain_point": tool.pain_point,
                "micro_saas_ideas": tool.micro_saas_ideas,
                "date": tool.date.isoformat(),
                "created_at": datetime.now().isoformat()
            }

            # 先尝试更新
            result = (
                self.client.table("tools")
                .update(tool_data)
                .eq("tool_name", tool.tool_name)
                .eq("link", tool.link)
                .execute()
            )

            # 如果没有更新任何记录，则插入新记录
            if len(result.data) == 0:
                result = self.client.table("tools").insert(tool_data).execute()

            return len(result.data) > 0

        except Exception as e:
            logger.error(f"插入/更新工具失败: {e}")
            return False

    async def delete_old_tools(self, days: int = 30) -> int:
        """删除旧工具数据"""
        try:
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)

            result = (
                self.client.table("tools")
                .delete()
                .lt("date", cutoff_date.isoformat())
                .execute()
            )

            deleted_count = len(result.data)
            logger.info(f"删除了 {deleted_count} 个旧工具记录")
            return deleted_count

        except Exception as e:
            logger.error(f"删除旧工具失败: {e}")
            return 0


# 创建全局数据库实例
db = SupabaseDB()