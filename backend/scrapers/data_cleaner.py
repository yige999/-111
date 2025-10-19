import re
import logging
from typing import List, Optional, Set
from datetime import datetime, timezone

from ..models import RawTool

logger = logging.getLogger(__name__)


class DataCleaner:
    """数据清洗和格式化工具"""

    def __init__(self):
        self.duplicate_links: Set[str] = set()
        self.processed_count = 0

    def clean_tools_list(self, tools: List[RawTool]) -> List[RawTool]:
        """清洗工具列表"""
        cleaned_tools = []

        for tool in tools:
            cleaned_tool = self.clean_single_tool(tool)
            if cleaned_tool and self._is_valid_tool(cleaned_tool):
                cleaned_tools.append(cleaned_tool)

        logger.info(f"清洗完成：从 {len(tools)} 个工具清理为 {len(cleaned_tools)} 个有效工具")
        return cleaned_tools

    def clean_single_tool(self, tool: RawTool) -> Optional[RawTool]:
        """清洗单个工具数据"""
        try:
            # 清洗工具名称
            cleaned_name = self._clean_tool_name(tool.tool_name)

            # 清洗描述
            cleaned_description = self._clean_description(tool.description)

            # 标准化分类
            cleaned_category = self._standardize_category(tool.category, cleaned_name, cleaned_description)

            # 验证并标准化URL
            cleaned_link = self._validate_and_normalize_url(tool.link)

            # 验证投票数
            cleaned_votes = self._validate_votes(tool.votes)

            # 确保日期有效
            cleaned_date = self._validate_date(tool.date)

            if not cleaned_name or not cleaned_link:
                return None

            return RawTool(
                tool_name=cleaned_name,
                description=cleaned_description,
                votes=cleaned_votes,
                link=cleaned_link,
                date=cleaned_date,
                category=cleaned_category
            )

        except Exception as e:
            logger.error(f"清洗工具数据失败: {e}")
            return None

    def _clean_tool_name(self, name: str) -> str:
        """清洗工具名称"""
        if not name:
            return ""

        # 移除常见的垃圾前缀和后缀
        patterns_to_remove = [
            r'^\s*[-*_]\s*',
            r'\s*[-*_]\s*$',
            r'^\[.*?\]\s*',
            r'\s*\[.*?\]\s*$',
            r'^\s*\d+\.\s*',
            r'^\s*\d+\)\s*',
            r'🚀\s*|✨\s*|🎯\s*|⭐\s*',  # 移除emoji前缀
        ]

        cleaned = name
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        # 限制长度
        cleaned = cleaned.strip()[:100]

        # 移除多余空格
        cleaned = re.sub(r'\s+', ' ', cleaned)

        return cleaned

    def _clean_description(self, description: str) -> str:
        """清洗描述文本"""
        if not description:
            return ""

        # 移除HTML标签
        cleaned = re.sub(r'<[^>]+>', '', description)

        # 移除特殊字符和多余空白
        cleaned = re.sub(r'[^\w\s\-\.\,\!\?\:\;]', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)

        # 移除重复的句子或短语
        sentences = cleaned.split('. ')
        unique_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and not any(self._similarity_check(sentence, existing) for existing in unique_sentences):
                unique_sentences.append(sentence)

        # 重新组合并限制长度
        cleaned = '. '.join(unique_sentences[:3])  # 最多保留3句话
        cleaned = cleaned.strip()[:500]  # 限制总长度

        return cleaned

    def _standardize_category(self, original_category: str, tool_name: str, description: str) -> str:
        """标准化分类"""
        if original_category:
            # 标准化现有分类
            category_mapping = {
                'video editing': 'Video',
                'video generation': 'Video',
                'text generation': 'Text',
                'content creation': 'Text',
                'productivity tools': 'Productivity',
                'task management': 'Productivity',
                'marketing tools': 'Marketing',
                'social media': 'Marketing',
                'educational': 'Education',
                'learning': 'Education',
                'audio processing': 'Audio',
                'music generation': 'Audio',
                'image generation': 'Image',
                'photo editing': 'Image',
                'code generation': 'Code',
                'programming': 'Code'
            }

            standardized = category_mapping.get(original_category.lower(), original_category)
            if standardized in ['Video', 'Text', 'Productivity', 'Marketing', 'Education', 'Audio', 'Image', 'Code']:
                return standardized

        # 如果没有分类或分类无效，基于名称和描述推断
        return self._infer_category(tool_name, description)

    def _infer_category(self, tool_name: str, description: str) -> str:
        """基于工具名称和描述推断分类"""
        text = (tool_name + ' ' + description).lower()

        category_keywords = {
            'Video': ['video', 'movie', 'animation', 'film', 'video generation', 'video editing'],
            'Text': ['text', 'writing', 'content', 'copywriting', 'article', 'blog', 'text generation'],
            'Productivity': ['productivity', 'task', 'workflow', 'automation', 'efficiency', 'management'],
            'Marketing': ['marketing', 'seo', 'social media', 'advertising', 'email', 'promotion'],
            'Education': ['education', 'learning', 'tutoring', 'course', 'teaching', 'training'],
            'Audio': ['audio', 'music', 'voice', 'sound', 'podcast', 'speech', 'music generation'],
            'Image': ['image', 'photo', 'picture', 'graphic', 'design', 'image generation'],
            'Code': ['code', 'programming', 'development', 'coding', 'software', 'api']
        }

        for category, keywords in category_keywords.items():
            if any(keyword in text for keyword in keywords):
                return category

        return ""

    def _validate_and_normalize_url(self, url: str) -> str:
        """验证并标准化URL"""
        if not url:
            return ""

        # 移除URL参数
        url = re.sub(r'[?&](utm_[^&]*|ref=[^&]*|source=[^&]*)', '', url)

        # 确保有协议
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        # 验证URL格式
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            if parsed.netloc and parsed.scheme in ['http', 'https']:
                return url
        except:
            pass

        return ""

    def _validate_votes(self, votes: int) -> int:
        """验证投票数"""
        if not isinstance(votes, int) or votes < 0:
            return 0
        # 限制最大投票数，防止异常数据
        return min(votes, 10000)

    def _validate_date(self, date: datetime) -> datetime:
        """验证日期"""
        if not isinstance(date, datetime):
            return datetime.now(timezone.utc)

        # 确保日期在合理范围内（不能太早或太晚）
        now = datetime.now(timezone.utc)
        one_year_ago = now.replace(year=now.year - 1)

        if date > now:
            return now
        elif date < one_year_ago:
            return one_year_ago

        return date

    def _is_valid_tool(self, tool: RawTool) -> bool:
        """验证工具是否有效"""
        # 检查必要字段
        if not tool.tool_name or not tool.link:
            return False

        # 检查是否已重复（基于链接）
        if tool.link in self.duplicate_links:
            return False

        # 检查工具名称长度
        if len(tool.tool_name) < 3 or len(tool.tool_name) > 100:
            return False

        # 添加到已处理集合
        self.duplicate_links.add(tool.link)
        self.processed_count += 1

        return True

    def _similarity_check(self, text1: str, text2: str, threshold: float = 0.8) -> bool:
        """检查两个文本的相似度"""
        if not text1 or not text2:
            return False

        # 简单的相似度检查：共同词汇比例
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return False

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        similarity = len(intersection) / len(union) if union else 0
        return similarity >= threshold

    def get_statistics(self) -> dict:
        """获取清洗统计信息"""
        return {
            'processed_count': self.processed_count,
            'duplicate_count': len(self.duplicate_links)
        }


def clean_and_validate_tools(tools: List[RawTool]) -> List[RawTool]:
    """便捷函数：清洗和验证工具列表"""
    cleaner = DataCleaner()
    return cleaner.clean_tools_list(tools)