"""
数据库管理器 - 提供高级数据库操作接口
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from pydantic import BaseModel, ValidationError

from .supabase_client import SupabaseDB, db

logger = logging.getLogger(__name__)

class ToolData(BaseModel):
    """工具数据验证模型"""
    tool_name: str
    description: Optional[str] = None
    category: Optional[str] = None
    votes: int = 0
    link: Optional[str] = None
    trend_signal: Optional[str] = None
    pain_point: Optional[str] = None
    micro_saas_ideas: Optional[List[str]] = None
    date: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class DatabaseManager:
    """数据库管理器 - 提供高级操作接口"""

    def __init__(self, db_client: SupabaseDB = None):
        self.db = db_client or db

    async def validate_tool_data(self, tool_data: Dict[str, Any]) -> Optional[ToolData]:
        """验证工具数据格式"""
        try:
            # 确保必要字段存在
            if not tool_data.get('tool_name'):
                logger.warning("工具数据缺少必要字段: tool_name")
                return None

            # 处理日期格式
            if isinstance(tool_data.get('date'), str):
                try:
                    tool_data['date'] = datetime.fromisoformat(tool_data['date'].replace('Z', '+00:00'))
                except:
                    tool_data['date'] = datetime.now()

            # 确保votes是整数
            if not isinstance(tool_data.get('votes'), int):
                try:
                    tool_data['votes'] = int(tool_data.get('votes', 0))
                except:
                    tool_data['votes'] = 0

            # 确保micro_saas_ideas是列表
            if tool_data.get('micro_saas_ideas') and not isinstance(tool_data['micro_saas_ideas'], list):
                tool_data['micro_saas_ideas'] = [tool_data['micro_saas_ideas']]

            # 使用Pydantic验证
            return ToolData(**tool_data)

        except ValidationError as e:
            logger.warning(f"工具数据验证失败: {e}")
            return None
        except Exception as e:
            logger.error(f"验证工具数据时出错: {e}")
            return None

    async def batch_insert_tools(self, tools_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """批量插入工具数据（带验证）"""
        stats = {"success": 0, "failed": 0, "duplicates": 0}

        if not tools_data:
            logger.info("没有工具数据需要插入")
            return stats

        # 验证所有数据
        validated_tools = []
        for tool_data in tools_data:
            validated_tool = await self.validate_tool_data(tool_data)
            if validated_tool:
                validated_tools.append(validated_tool.dict())
            else:
                stats["failed"] += 1

        if not validated_tools:
            logger.warning("没有有效的工具数据可以插入")
            return stats

        # 分批插入（每批20个）
        batch_size = 20
        for i in range(0, len(validated_tools), batch_size):
            batch = validated_tools[i:i + batch_size]

            try:
                # 检查重复
                new_batch = []
                for tool in batch:
                    exists = await self.db.tool_exists(
                        tool["tool_name"],
                        tool.get("link", "")
                    )
                    if exists:
                        stats["duplicates"] += 1
                    else:
                        new_batch.append(tool)

                if new_batch:
                    # 插入新数据
                    success = await self.db.insert_tools([
                        ToolData(**tool) for tool in new_batch
                    ])

                    if success:
                        stats["success"] += len(new_batch)
                        logger.info(f"成功插入批次 {i//batch_size + 1}: {len(new_batch)} 个工具")
                    else:
                        stats["failed"] += len(new_batch)
                        logger.error(f"批次 {i//batch_size + 1} 插入失败")

            except Exception as e:
                logger.error(f"批次 {i//batch_size + 1} 处理失败: {e}")
                stats["failed"] += len(batch)

        logger.info(f"批量插入完成 - 成功: {stats['success']}, 失败: {stats['failed']}, 重复: {stats['duplicates']}")
        return stats

    async def get_today_top_tools(self, limit: int = 5) -> List[Dict[str, Any]]:
        """获取今日Top工具"""
        today = datetime.now().date().isoformat()
        return await self.db.get_tools_by_date(today, limit)

    async def get_trending_tools_by_category(self, category: str = None, days: int = 7, limit: int = 20) -> List[Dict[str, Any]]:
        """获取趋势工具（可按分类筛选）"""
        if category:
            # 先获取分类下的工具，再筛选趋势
            category_tools = await self.db.get_tools_by_category(category, limit * 2)
            trending = [tool for tool in category_tools if tool.get('trend_signal') == 'Rising']
            return trending[:limit]
        else:
            return await self.db.get_trending_tools(days, limit)

    async def search_tools(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """搜索工具"""
        try:
            # 使用PostgreSQL的全文搜索
            result = (
                self.db.client.table("tools")
                .select("*")
                .or_(f"tool_name.ilike.%{query}%,description.ilike.%{query}%,category.ilike.%{query}%")
                .order("votes", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data

        except Exception as e:
            logger.error(f"搜索工具失败: {e}")
            return []

    async def get_category_summary(self, days: int = 7) -> Dict[str, Any]:
        """获取分类汇总信息"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).date().isoformat()

            # 按分类统计
            result = (
                self.db.client.table("tools")
                .select("category, trend_signal, votes")
                .gte("date", cutoff_date)
                .execute()
            )

            summary = {}
            for item in result.data:
                category = item["category"] or "Other"
                trend = item["trend_signal"] or "Unknown"
                votes = item["votes"] or 0

                if category not in summary:
                    summary[category] = {
                        "total": 0,
                        "rising": 0,
                        "stable": 0,
                        "declining": 0,
                        "total_votes": 0
                    }

                summary[category]["total"] += 1
                summary[category]["total_votes"] += votes

                if trend in summary[category]:
                    summary[category][trend] += 1

            return summary

        except Exception as e:
            logger.error(f"获取分类汇总失败: {e}")
            return {}

    async def get_daily_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取每日统计"""
        try:
            stats = []
            for i in range(days):
                date = (datetime.now() - timedelta(days=i)).date().isoformat()

                # 获取当日数据
                daily_tools = await self.db.get_tools_by_date(date, 1000)

                # 统计分类和趋势
                categories = {}
                trends = {"Rising": 0, "Stable": 0, "Declining": 0}

                for tool in daily_tools:
                    category = tool.get("category", "Other")
                    categories[category] = categories.get(category, 0) + 1

                    trend = tool.get("trend_signal")
                    if trend in trends:
                        trends[trend] += 1

                stats.append({
                    "date": date,
                    "total_tools": len(daily_tools),
                    "categories": categories,
                    "trends": trends
                })

            return reversed(stats)

        except Exception as e:
            logger.error(f"获取每日统计失败: {e}")
            return []

    async def cleanup_duplicate_tools(self) -> int:
        """清理重复工具"""
        try:
            # 获取所有可能有重复的工具
            all_tools = await self.db.get_latest_tools(10000)

            # 按名称和链接分组
            tool_groups = {}
            for tool in all_tools:
                key = (tool.get("tool_name", ""), tool.get("link", ""))
                if key not in tool_groups:
                    tool_groups[key] = []
                tool_groups[key].append(tool)

            # 找出重复项并删除旧的
            duplicates_to_delete = []
            for (name, link), tools in tool_groups.items():
                if len(tools) > 1:
                    # 保留最新的，删除其他的
                    sorted_tools = sorted(tools, key=lambda x: x.get("date", ""), reverse=True)
                    duplicates_to_delete.extend(sorted_tools[1:])

            # 删除重复项
            deleted_count = 0
            for tool in duplicates_to_delete:
                try:
                    result = (
                        self.db.client.table("tools")
                        .delete()
                        .eq("id", tool["id"])
                        .execute()
                    )
                    if result.data:
                        deleted_count += 1
                except Exception as e:
                    logger.error(f"删除重复工具失败 {tool.get('tool_name')}: {e}")

            logger.info(f"清理重复工具完成，删除了 {deleted_count} 个重复项")
            return deleted_count

        except Exception as e:
            logger.error(f"清理重复工具失败: {e}")
            return 0

    async def export_tools_data(self, format: str = "json", days: int = 30) -> Optional[str]:
        """导出工具数据"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).date().isoformat()

            # 获取数据
            tools = (
                self.db.client.table("tools")
                .select("*")
                .gte("date", cutoff_date)
                .order("date", desc=True)
                .execute()
            )

            if format.lower() == "json":
                import json
                return json.dumps(tools.data, indent=2, ensure_ascii=False, default=str)

            elif format.lower() == "csv":
                import csv
                import io

                if not tools.data:
                    return ""

                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=tools.data[0].keys())
                writer.writeheader()

                for tool in tools.data:
                    # 处理JSON字段
                    tool_copy = tool.copy()
                    if isinstance(tool_copy.get('micro_saas_ideas'), list):
                        tool_copy['micro_saas_ideas'] = ';'.join(tool_copy['micro_saas_ideas'])

                    writer.writerow(tool_copy)

                return output.getvalue()

            else:
                logger.error(f"不支持的导出格式: {format}")
                return None

        except Exception as e:
            logger.error(f"导出数据失败: {e}")
            return None

# 创建全局数据库管理器实例
db_manager = DatabaseManager()