"""
数据验证器 - 提供全面的数据验证和清洗功能
"""
import re
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime, date
from urllib.parse import urlparse
import logging
from pydantic import BaseModel, validator, ValidationError
from enum import Enum

logger = logging.getLogger(__name__)

class TrendSignal(str, Enum):
    """趋势信号枚举"""
    RISING = "Rising"
    STABLE = "Stable"
    DECLINING = "Declining"
    UNKNOWN = "Unknown"

class ToolCategory(str, Enum):
    """工具分类枚举"""
    VIDEO = "Video"
    TEXT = "Text"
    PRODUCTIVITY = "Productivity"
    MARKETING = "Marketing"
    EDUCATION = "Education"
    AUDIO = "Audio"
    DESIGN = "Design"
    CODING = "Coding"
    ANALYTICS = "Analytics"
    OTHER = "Other"

class ValidationResult(BaseModel):
    """验证结果"""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    cleaned_data: Optional[Dict[str, Any]] = None

class ToolValidator(BaseModel):
    """工具数据验证器"""
    tool_name: str
    description: Optional[str] = None
    category: Optional[ToolCategory] = ToolCategory.OTHER
    votes: int = 0
    link: Optional[str] = None
    trend_signal: Optional[TrendSignal] = TrendSignal.UNKNOWN
    pain_point: Optional[str] = None
    micro_saas_ideas: Optional[List[str]] = None
    date: Union[datetime, date, str]

    @validator('tool_name')
    def validate_tool_name(cls, v):
        """验证工具名称"""
        if not v or not v.strip():
            raise ValueError('工具名称不能为空')

        v = v.strip()

        # 长度限制
        if len(v) > 200:
            raise ValueError('工具名称过长（最大200字符）')

        # 移除多余空格
        v = re.sub(r'\s+', ' ', v)

        return v

    @validator('description')
    def validate_description(cls, v):
        """验证描述"""
        if v is None:
            return v

        v = v.strip()

        # 长度限制
        if len(v) > 2000:
            logger.warning(f"描述过长，截断到2000字符: {v[:50]}...")
            v = v[:2000]

        # 移除多余空格和换行
        v = re.sub(r'\s+', ' ', v)

        return v if v else None

    @validator('votes')
    def validate_votes(cls, v):
        """验证投票数"""
        if v < 0:
            raise ValueError('投票数不能为负数')
        if v > 1000000:  # 合理上限
            logger.warning(f"投票数异常高: {v}")
        return v

    @validator('link')
    def validate_link(cls, v):
        """验证链接"""
        if v is None:
            return v

        v = v.strip()

        if not v:
            return None

        # URL格式验证
        try:
            parsed = urlparse(v)
            if not parsed.scheme or not parsed.netloc:
                logger.warning(f"链接格式可能不正确: {v}")
        except Exception as e:
            logger.warning(f"链接解析失败: {v}, 错误: {e}")

        # 长度限制
        if len(v) > 500:
            logger.warning(f"链接过长，截断到500字符: {v[:50]}...")
            v = v[:500]

        return v if v else None

    @validator('pain_point')
    def validate_pain_point(cls, v):
        """验证痛点描述"""
        if v is None:
            return v

        v = v.strip()

        # 长度限制
        if len(v) > 1000:
            logger.warning(f"痛点描述过长，截断到1000字符: {v[:50]}...")
            v = v[:1000]

        # 移除多余空格
        v = re.sub(r'\s+', ' ', v)

        return v if v else None

    @validator('micro_saas_ideas')
    def validate_micro_saas_ideas(cls, v):
        """验证Micro SaaS点子"""
        if v is None:
            return v

        if not isinstance(v, list):
            # 如果是字符串，转换为列表
            if isinstance(v, str):
                v = [v]
            else:
                v = [str(v)]

        # 清洗每个点子
        cleaned_ideas = []
        for idea in v:
            if idea is None:
                continue

            idea = str(idea).strip()
            if not idea:
                continue

            # 长度限制
            if len(idea) > 300:
                logger.warning(f"点子描述过长，截断到300字符: {idea[:50]}...")
                idea = idea[:300]

            # 移除多余空格
            idea = re.sub(r'\s+', ' ', idea)

            if idea:
                cleaned_ideas.append(idea)

        return cleaned_ideas if cleaned_ideas else None

    @validator('date')
    def validate_date(cls, v):
        """验证日期"""
        if isinstance(v, str):
            try:
                # 尝试解析ISO格式
                if 'T' in v:
                    return datetime.fromisoformat(v.replace('Z', '+00:00'))
                else:
                    # 只有日期部分
                    return datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                try:
                    # 尝试其他常见格式
                    return datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    logger.warning(f"日期格式无法解析，使用当前时间: {v}")
                    return datetime.now()

        elif isinstance(v, date):
            return datetime.combine(v, datetime.min.time())

        elif isinstance(v, datetime):
            return v

        else:
            logger.warning(f"日期类型无效，使用当前时间: {type(v)}")
            return datetime.now()

class DataValidator:
    """数据验证器主类"""

    def __init__(self):
        self.required_fields = ['tool_name']
        self.optional_fields = [
            'description', 'category', 'votes', 'link', 'trend_signal',
            'pain_point', 'micro_saas_ideas', 'date'
        ]

    async def validate_tool(self, tool_data: Dict[str, Any]) -> ValidationResult:
        """验证单个工具数据"""
        errors = []
        warnings = []
        cleaned_data = tool_data.copy()

        try:
            # 检查必要字段
            for field in self.required_fields:
                if field not in tool_data or tool_data[field] is None:
                    if field == 'tool_name':
                        errors.append(f"缺少必要字段: {field}")
                    else:
                        warnings.append(f"缺少字段: {field}")

            # 使用Pydantic验证器
            validated_tool = ToolValidator(**tool_data)
            cleaned_data = validated_tool.dict()

            # 自定义验证规则
            custom_validation_result = await self._custom_validation(cleaned_data)
            errors.extend(custom_validation_result.get('errors', []))
            warnings.extend(custom_validation_result.get('warnings', []))

            # 数据增强
            enhanced_data = await self._enhance_data(cleaned_data)
            cleaned_data.update(enhanced_data)

            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                cleaned_data=cleaned_data
            )

        except ValidationError as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"验证错误: {str(e)}"],
                warnings=warnings,
                cleaned_data=None
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"验证过程中发生错误: {str(e)}"],
                warnings=warnings,
                cleaned_data=None
            )

    async def validate_batch(self, tools_data: List[Dict[str, Any]]) -> List[ValidationResult]:
        """批量验证工具数据"""
        results = []

        logger.info(f"开始批量验证: {len(tools_data)} 项")

        for i, tool_data in enumerate(tools_data):
            result = await self.validate_tool(tool_data)
            results.append(result)

            if i % 100 == 0 and i > 0:
                logger.info(f"已验证 {i}/{len(tools_data)} 项")

        # 统计结果
        valid_count = sum(1 for r in results if r.is_valid)
        logger.info(f"批量验证完成: {valid_count}/{len(results)} 项有效")

        return results

    async def _custom_validation(self, tool_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """自定义验证规则"""
        errors = []
        warnings = []

        # 检查工具名称是否包含垃圾信息
        tool_name = tool_data.get('tool_name', '').lower()
        spam_keywords = ['free', 'download', 'crack', 'hack', 'cheat', 'mod']
        if any(keyword in tool_name for keyword in spam_keywords):
            warnings.append("工具名称可能包含垃圾信息关键词")

        # 检查描述是否为空的重复
        description = tool_data.get('description', '').strip()
        tool_name = tool_data.get('tool_name', '').strip()

        if description and description == tool_name:
            warnings.append("描述与工具名称相同，可能信息量不足")

        # 检查链接是否有效域名
        link = tool_data.get('link', '')
        if link:
            try:
                parsed = urlparse(link)
                domain = parsed.netloc.lower()

                # 检查是否为已知垃圾域名
                spam_domains = ['spam.com', 'fake.org']
                if any(spam_domain in domain for spam_domain in spam_domains):
                    warnings.append("链接域名可能不可信")

            except Exception:
                warnings.append("链接格式验证失败")

        # 检查分类是否合理
        category = tool_data.get('category', '').lower()
        tool_name_lower = tool_name.lower()
        description_lower = description.lower()

        # 简单的分类一致性检查
        if 'video' in category and not any(keyword in tool_name_lower + description_lower
                                           for keyword in ['video', 'movie', 'film', 'camera']):
            warnings.append("分类与工具内容可能不匹配")

        return {'errors': errors, 'warnings': warnings}

    async def _enhance_data(self, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """数据增强"""
        enhanced = {}

        # 自动分类（如果没有分类）
        if not tool_data.get('category') or tool_data['category'] == ToolCategory.OTHER:
            auto_category = self._auto_categorize(tool_data)
            if auto_category:
                enhanced['category'] = auto_category

        # 清理和标准化文本
        enhanced['tool_name'] = self._clean_text(tool_data.get('tool_name', ''))

        if tool_data.get('description'):
            enhanced['description'] = self._clean_text(tool_data['description'])

        # 确保日期格式
        if not tool_data.get('date'):
            enhanced['date'] = datetime.now()

        return enhanced

    def _auto_categorize(self, tool_data: Dict[str, Any]) -> Optional[str]:
        """自动分类工具"""
        tool_name = tool_data.get('tool_name', '').lower()
        description = tool_data.get('description', '').lower()
        text = f"{tool_name} {description}"

        category_keywords = {
            ToolCategory.VIDEO: ['video', 'movie', 'film', 'camera', 'youtube', 'tiktok'],
            ToolCategory.AUDIO: ['audio', 'music', 'sound', 'podcast', 'voice', 'spotify'],
            ToolCategory.TEXT: ['text', 'writing', 'document', 'content', 'article', 'blog'],
            ToolCategory.DESIGN: ['design', 'ui', 'ux', 'graphic', 'logo', 'color'],
            ToolCategory.CODING: ['code', 'programming', 'developer', 'api', 'github'],
            ToolCategory.MARKETING: ['marketing', 'seo', 'ads', 'social media', 'email'],
            ToolCategory.ANALYTICS: ['analytics', 'data', 'metrics', 'tracking', 'report'],
            ToolCategory.PRODUCTIVITY: ['productivity', 'task', 'project', 'calendar', 'todo'],
            ToolCategory.EDUCATION: ['education', 'learning', 'course', 'tutorial', 'study']
        }

        for category, keywords in category_keywords.items():
            if any(keyword in text for keyword in keywords):
                return category.value

        return None

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return text

        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text.strip())

        # 移除特殊字符（保留基本标点）
        text = re.sub(r'[^\w\s\-.,!?()[\]{}:;\'"/\\]', '', text)

        return text

    def get_validation_summary(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """获取验证结果摘要"""
        total = len(results)
        valid = sum(1 for r in results if r.is_valid)
        invalid = total - valid

        # 统计错误类型
        error_types = {}
        all_warnings = []

        for result in results:
            if not result.is_valid:
                for error in result.errors:
                    error_type = error.split(':')[0] if ':' in error else 'unknown'
                    error_types[error_type] = error_types.get(error_type, 0) + 1

            all_warnings.extend(result.warnings)

        return {
            'total': total,
            'valid': valid,
            'invalid': invalid,
            'valid_rate': round(valid / total * 100, 2) if total > 0 else 0,
            'error_types': error_types,
            'total_warnings': len(all_warnings),
            'unique_warnings': len(set(all_warnings))
        }

# 创建全局数据验证器实例
data_validator = DataValidator()