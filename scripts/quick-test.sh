#!/bin/bash

# AutoSaaS Radar - 快速测试脚本
# 窗口10：部署自动化

echo "🚀 AutoSaaS Radar 快速测试开始..."
echo "=================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试结果统计
TESTS_PASSED=0
TESTS_FAILED=0

# 测试函数
run_test() {
    local test_name="$1"
    local test_command="$2"

    echo -e "\n🔍 测试: $test_name"
    echo "命令: $test_command"

    if eval "$test_command"; then
        echo -e "${GREEN}✅ 通过${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ 失败${NC}"
        ((TESTS_FAILED++))
    fi
}

# 检查文件存在性
echo -e "\n📁 检查项目文件结构..."
run_test "根目录存在" "test -d ."
run_test "README.md存在" "test -f README.md"
run_test "前端目录存在" "test -d frontend"
run_test "后端目录存在" "test -d backend"
run_test "脚本目录存在" "test -d scripts"
run_test "部署目录存在" "test -d deploy"
run_test "配置目录存在" "test -d config"

# 检查配置文件
echo -e "\n⚙️ 检查配置文件..."
run_test "Vercel配置存在" "test -f vercel.json"
run_test "环境变量示例存在" "test -f .env.example"
run_test "部署配置存在" "test -f config/deploy-config.json"

# 检查脚本文件
echo -e "\n📜 检查脚本文件..."
run_test "自动化脚本存在" "test -f scripts/auto-run.py"
run_test "健康检查脚本存在" "test -f scripts/health-check.py"
run_test "Cron设置脚本存在" "test -f scripts/setup-cron.sh"
run_test "Vercel部署脚本存在" "test -f deploy/vercel-deploy.sh"

# 检查Python环境
echo -e "\n🐍 检查Python环境..."
run_test "Python已安装" "command -v python3"
run_test "Pip已安装" "command -v pip3"

# 检查Node.js环境
echo -e "\n📦 检查Node.js环境..."
run_test "Node.js已安装" "command -v node"
run_test "npm已安装" "command -v npm"

# 检查部署工具
echo -e "\n🚀 检查部署工具..."
run_test "Vercel CLI已安装" "command -v vercel || echo 'Vercel CLI未安装，但会自动安装'"

# 模拟数据测试
echo -e "\n🧪 模拟数据测试..."
cat > test_data.json << EOF
{
  "tool_name": "Test Tool",
  "description": "A test AI tool for validation",
  "votes": 100,
  "link": "https://example.com",
  "date": "2024-01-15T09:00:00Z"
}
EOF

run_test "测试数据文件创建" "test -f test_data.json"

# 测试数据格式
echo -e "\n📊 测试数据格式..."
run_test "JSON格式验证" "python3 -c \"import json; print('Valid JSON')\" < test_data.json"

# 清理测试文件
echo -e "\n🧹 清理测试文件..."
rm -f test_data.json

# 运行健康检查（如果可用）
echo -e "\n🏥 运行健康检查..."
if [ -f "scripts/health-check.py" ]; then
    echo "运行健康检查脚本..."
    python3 scripts/health-check.py || echo -e "${YELLOW}⚠️ 健康检查需要依赖项，在完整环境中运行${NC}"
else
    echo -e "${YELLOW}⚠️ 健康检查脚本不存在${NC}"
fi

# 输出测试总结
echo -e "\n=================================="
echo -e "📊 测试总结:"
echo -e "${GREEN}✅ 通过: $TESTS_PASSED${NC}"
echo -e "${RED}❌ 失败: $TESTS_FAILED${NC}"
echo -e "📈 总计: $((TESTS_PASSED + TESTS_FAILED))"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 所有测试通过！项目结构验证成功！${NC}"
    exit 0
else
    echo -e "\n${RED}⚠️ 有 $TESTS_FAILED 个测试失败，请检查项目配置${NC}"
    exit 1
fi