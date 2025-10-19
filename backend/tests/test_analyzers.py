import pytest
import json
from unittest.mock import Mock, patch, AsyncMock

from analyzers.gpt_analyzer import GPTAnalyzer
from models import RawTool, AnalyzedTool


class TestGPTAnalyzer:
    """GPT分析器测试"""

    @pytest.fixture
    def analyzer(self):
        return GPTAnalyzer(api_key="test_key")

    @pytest.fixture
    def sample_tools(self):
        """示例工具数据"""
        return [
            RawTool(
                tool_name="AI Resume Builder",
                description="Build perfect resumes with AI assistance",
                votes=150,
                link="https://example.com/resume-builder",
                date=None,
                category=""
            ),
            RawTool(
                tool_name="Productivity Tracker",
                description="Track daily productivity and habits",
                votes=89,
                link="https://example.com/tracker",
                date=None,
                category=""
            )
        ]

    def test_build_analysis_prompt(self, analyzer, sample_tools):
        """测试构建分析prompt"""
        prompt = analyzer._build_analysis_prompt(sample_tools)

        # 验证prompt包含必要信息
        assert "AI Resume Builder" in prompt
        assert "Productivity Tracker" in prompt
        assert "Video" in prompt  # 分类选项
        assert "Rising" in prompt  # 趋势信号选项
        assert "analyzed_tools" in prompt

    def test_parse_gpt_response_success(self, analyzer):
        """测试解析GPT响应成功"""
        response_json = {
            "analyzed_tools": [
                {
                    "tool_name": "AI Resume Builder",
                    "category": "Productivity",
                    "trend_signal": "Rising",
                    "pain_point": "Users struggle with ATS optimization",
                    "micro_saas_ideas": ["Resume Tailor Tool", "ATS Score Checker"]
                }
            ]
        }

        response = json.dumps(response_json)
        analyzed_tools = analyzer._parse_gpt_response(response)

        assert len(analyzed_tools) == 1
        tool = analyzed_tools[0]
        assert tool.tool_name == "AI Resume Builder"
        assert tool.category == "Productivity"
        assert tool.trend_signal == "Rising"
        assert len(tool.micro_saas_ideas) == 2

    def test_parse_gpt_response_with_code_blocks(self, analyzer):
        """测试解析包含代码块的GPT响应"""
        response_json = {
            "analyzed_tools": [
                {
                    "tool_name": "Test Tool",
                    "category": "Video",
                    "trend_signal": "Stable",
                    "pain_point": "Test pain point",
                    "micro_saas_ideas": ["Idea 1"]
                }
            ]
        }

        response = f"```json\n{json.dumps(response_json)}\n```"
        analyzed_tools = analyzer._parse_gpt_response(response)

        assert len(analyzed_tools) == 1
        assert analyzed_tools[0].tool_name == "Test Tool"

    def test_parse_gpt_response_invalid_category(self, analyzer):
        """测试解析包含无效分类的响应"""
        response_json = {
            "analyzed_tools": [
                {
                    "tool_name": "Test Tool",
                    "category": "Invalid Category",  # 无效分类
                    "trend_signal": "Rising",
                    "pain_point": "Test pain point",
                    "micro_saas_ideas": ["Idea 1"]
                }
            ]
        }

        response = json.dumps(response_json)
        analyzed_tools = analyzer._parse_gpt_response(response)

        assert len(analyzed_tools) == 1
        # 无效分类应该被替换为"Other"
        assert analyzed_tools[0].category == "Other"

    def test_parse_gpt_response_missing_fields(self, analyzer):
        """测试解析缺少字段的响应"""
        response_json = {
            "analyzed_tools": [
                {
                    "tool_name": "Test Tool",
                    "category": "Productivity"
                    # 缺少其他必要字段
                }
            ]
        }

        response = json.dumps(response_json)
        analyzed_tools = analyzer._parse_gpt_response(response)

        # 缺少必要字段的工具应该被跳过
        assert len(analyzed_tools) == 0

    def test_parse_gpt_response_invalid_json(self, analyzer):
        """测试解析无效JSON响应"""
        invalid_json = "{ invalid json }"

        analyzed_tools = analyzer._parse_gpt_response(invalid_json)
        assert len(analyzed_tools) == 0

    def test_calculate_cost(self, analyzer):
        """测试成本计算"""
        # 测试1000 tokens的成本
        cost = analyzer.calculate_cost(1000)
        assert cost > 0
        assert isinstance(cost, float)

        # 测试0 tokens
        cost = analyzer.calculate_cost(0)
        assert cost == 0

    @pytest.mark.asyncio
    async def test_call_gpt_analysis_success(self, analyzer):
        """测试成功调用GPT分析"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "analyzed_tools": [
                {
                    "tool_name": "Test Tool",
                    "category": "Productivity",
                    "trend_signal": "Rising",
                    "pain_point": "Test pain point",
                    "micro_saas_ideas": ["Idea 1"]
                }
            ]
        })
        mock_response.usage.total_tokens = 500

        with patch.object(analyzer.client.chat.completions, 'create', return_value=mock_response):
            result = await analyzer._call_gpt_analysis("test prompt")

            assert "analyzed_tools" in result
            analyzer.client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_gpt_analysis_api_error(self, analyzer):
        """测试GPT API错误"""
        with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
            import openai
            mock_create.side_effect = openai.APIError("API Error")

            with pytest.raises(openai.APIError):
                await analyzer._call_gpt_analysis("test prompt")

    @pytest.mark.asyncio
    async def test_analyze_tools_success(self, analyzer, sample_tools):
        """测试成功分析工具"""
        mock_response_content = json.dumps({
            "analyzed_tools": [
                {
                    "tool_name": "AI Resume Builder",
                    "category": "Productivity",
                    "trend_signal": "Rising",
                    "pain_point": "Users struggle with ATS optimization",
                    "micro_saas_ideas": ["Resume Tailor Tool"]
                }
            ]
        })

        with patch.object(analyzer, '_call_gpt_analysis', return_value=mock_response_content):
            analyzed_tools = await analyzer.analyze_tools(sample_tools)

            assert len(analyzed_tools) == 1
            assert analyzed_tools[0].tool_name == "AI Resume Builder"

    @pytest.mark.asyncio
    async def test_analyze_tools_empty_list(self, analyzer):
        """测试分析空工具列表"""
        analyzed_tools = await analyzer.analyze_tools([])
        assert len(analyzed_tools) == 0

    @pytest.mark.asyncio
    async def test_analyze_batch_success(self, analyzer, sample_tools):
        """测试批量分析成功"""
        with patch.object(analyzer, 'analyze_tools', return_value=[
            AnalyzedTool(
                tool_name="Test Tool",
                category="Productivity",
                trend_signal="Rising",
                pain_point="Test pain point",
                micro_saas_ideas=["Idea 1"]
            )
        ]):
            result = await analyzer.analyze_batch(sample_tools)

            assert result["status"] == "success"
            assert result["tools_count"] == len(sample_tools)
            assert result["analyzed_count"] == 1
            assert result["tokens_used"] > 0
            assert result["cost_usd"] > 0

    @pytest.mark.asyncio
    async def test_analyze_batch_failure(self, analyzer, sample_tools):
        """测试批量分析失败"""
        with patch.object(analyzer, 'analyze_tools', side_effect=Exception("Analysis failed")):
            result = await analyzer.analyze_batch(sample_tools)

            assert result["status"] == "failed"
            assert "error" in result
            assert result["tools_count"] == len(sample_tools)
            assert result["analyzed_count"] == 0


class TestAnalyzeToolsWithGPT:
    """测试便捷函数"""

    @pytest.mark.asyncio
    async def test_analyze_tools_with_gpt(self):
        """测试便捷分析函数"""
        sample_tools = [
            RawTool(
                tool_name="Test Tool",
                description="Test description",
                votes=10,
                link="https://example.com",
                date=None,
                category=""
            )
        ]

        with patch('analyzers.gpt_analyzer.GPTAnalyzer.analyze_tools', return_value=[]) as mock_analyze:
            result = await __import__('analyzers.gpt_analyzer').analyze_tools_with_gpt(sample_tools)
            mock_analyze.assert_called_once_with(sample_tools)


if __name__ == "__main__":
    pytest.main([__file__])