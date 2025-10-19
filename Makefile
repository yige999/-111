# AutoSaaS Radar - 快速启动和部署工具

.PHONY: help install setup test deploy clean

# 默认目标
help:
	@echo "🚀 AutoSaaS Radar - 可用命令:"
	@echo ""
	@echo "📦 安装和设置:"
	@echo "  make install          - 安装所有依赖"
	@echo "  make setup            - 设置开发环境"
	@echo "  make setup-prod       - 设置生产环境"
	@echo ""
	@echo "🧪 测试:"
	@echo "  make test             - 运行所有测试"
	@echo "  make test-backend     - 测试后端服务"
	@echo "  make test-frontend    - 测试前端应用"
	@echo "  make test-db          - 测试数据库连接"
	@echo ""
	@echo "🚀 部署:"
	@echo "  make deploy           - 部署到生产环境"
	@echo "  make deploy-staging   - 部署到测试环境"
	@echo "  make deploy-frontend  - 仅部署前端"
	@echo "  make deploy-backend   - 仅部署后端"
	@echo ""
	@echo "🔧 开发:"
	@echo "  make run-backend      - 启动后端服务"
	@echo "  make run-frontend     - 启动前端服务"
	@echo "  make run-scheduler    - 启动调度器"
	@echo "  make run-monitor      - 启动监控"
	@echo ""
	@echo "🧹 清理:"
	@echo "  make clean            - 清理临时文件"
	@echo "  make clean-deps       - 清理依赖"
	@echo ""
	@echo "📈 其他:"
	@echo "  make daily-scan       - 运行每日扫描"
	@echo "  make status           - 查看系统状态"
	@echo "  make logs             - 查看日志"

# 安装依赖
install:
	@echo "📦 安装项目依赖..."
	@echo "安装后端依赖..."
	cd backend && pip install -r requirements.txt
	@echo "安装前端依赖..."
	cd frontend && npm install
	@echo "安装脚本依赖..."
	pip install schedule psutil httpx tenacity
	@echo "✅ 依赖安装完成"

# 设置开发环境
setup:
	@echo "⚙️ 设置开发环境..."
	python scripts/setup_env.py --env=development --interactive
	@echo "✅ 开发环境设置完成"

# 设置生产环境
setup-prod:
	@echo "⚙️ 设置生产环境..."
	python scripts/setup_env.py --env=production --interactive
	@echo "✅ 生产环境设置完成"

# 运行所有测试
test:
	@echo "🧪 运行所有测试..."
	python scripts/quick_test.py --all --verbose

# 测试后端
test-backend:
	@echo "🧪 测试后端服务..."
	python scripts/quick_test.py --backend --verbose

# 测试前端
test-frontend:
	@echo "🧪 测试前端应用..."
	python scripts/quick_test.py --frontend --verbose

# 测试数据库
test-db:
	@echo "🧪 测试数据库连接..."
	python scripts/quick_test.py --database --verbose

# 部署到生产环境
deploy:
	@echo "🚀 部署到生产环境..."
	python scripts/deploy.py --all --env=production

# 部署到测试环境
deploy-staging:
	@echo "🚀 部署到测试环境..."
	python scripts/deploy.py --all --env=staging

# 仅部署前端
deploy-frontend:
	@echo "🚀 部署前端应用..."
	python scripts/deploy.py --frontend --env=production

# 仅部署后端
deploy-backend:
	@echo "🚀 部署后端服务..."
	python scripts/deploy.py --backend --env=production

# 启动后端服务
run-backend:
	@echo "🔧 启动后端服务..."
	cd backend && python main.py

# 启动前端服务
run-frontend:
	@echo "🔧 启动前端服务..."
	cd frontend && npm run dev

# 启动调度器
run-scheduler:
	@echo "🔧 启动调度器..."
	python scripts/scheduler.py --start

# 停止调度器
stop-scheduler:
	@echo "🛑 停止调度器..."
	python scripts/scheduler.py --stop

# 启动监控
run-monitor:
	@echo "🔧 启动系统监控..."
	python scripts/monitor.py --daemon

# 运行每日扫描
daily-scan:
	@echo "📊 运行每日扫描..."
	python scripts/daily_scan.py

# 试运行扫描
dry-run-scan:
	@echo "📊 试运行每日扫描..."
	python scripts/daily_scan.py --dry-run

# 查看系统状态
status:
	@echo "📈 系统状态:"
	@echo "调度器状态:"
	python scripts/scheduler.py --status
	@echo ""
	@echo "监控状态:"
	python scripts/monitor.py --health-check

# 查看日志
logs:
	@echo "📋 最近日志:"
	@echo "=== 扫描日志 ==="
	@if [ -f logs/daily_scan.log ]; then tail -20 logs/daily_scan.log; else echo "日志文件不存在"; fi
	@echo ""
	@echo "=== 调度器日志 ==="
	@if [ -f logs/scheduler.log ]; then tail -20 logs/scheduler.log; else echo "日志文件不存在"; fi

# 清理临时文件
clean:
	@echo "🧹 清理临时文件..."
	rm -rf tmp/*
	rm -rf reports/*
	rm -rf logs/*.log
	@echo "✅ 临时文件清理完成"

# 清理依赖
clean-deps:
	@echo "🧹 清理依赖..."
	cd backend && pip uninstall -y -r requirements.txt || true
	cd frontend && rm -rf node_modules package-lock.json || true
	@echo "✅ 依赖清理完成"

# 快速启动开发环境
dev: install setup
	@echo "🚀 启动开发环境..."
	@echo "请在新的终端窗口中运行以下命令:"
	@echo "  make run-backend    # 启动后端"
	@echo "  make run-frontend   # 启动前端"
	@echo "  make run-scheduler  # 启动调度器"

# 生产环境部署
prod: test deploy
	@echo "🎉 生产环境部署完成!"

# 检查环境
check-env:
	@echo "🔍 检查环境配置..."
	@if [ ! -f .env ]; then echo "❌ .env 文件不存在，请运行 make setup"; exit 1; fi
	@echo "✅ .env 文件存在"
	@echo "检查关键配置项..."
	@grep -q "OPENAI_API_KEY=" .env && echo "✅ OPENAI_API_KEY 已设置" || echo "❌ OPENAI_API_KEY 未设置"
	@grep -q "SUPABASE_URL=" .env && echo "✅ SUPABASE_URL 已设置" || echo "❌ SUPABASE_URL 未设置"
	@grep -q "SUPABASE_KEY=" .env && echo "✅ SUPABASE_KEY 已设置" || echo "❌ SUPABASE_KEY 未设置"

# 创建必要的目录
init-dirs:
	@echo "📁 创建项目目录..."
	mkdir -p logs
	mkdir -p reports
	mkdir -p tmp
	mkdir -p monitor
	mkdir -p backups
	@echo "✅ 目录创建完成"

# 完整初始化
init: init-dirs install setup
	@echo "🎉 项目初始化完成!"
	@echo "下一步: make dev"