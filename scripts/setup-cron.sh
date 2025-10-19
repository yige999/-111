#!/bin/bash

# AutoSaaS Radar - Cron 定时任务设置脚本
# 窗口10：部署自动化

echo "⏰ 设置自动化定时任务..."

# 获取项目根目录
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 创建cron任务
CRON_JOB="0 9 * * * cd $PROJECT_DIR && python scripts/auto-run.py >> logs/cron.log 2>&1"

# 备份现有crontab
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null

# 检查是否已存在相同的任务
if crontab -l 2>/dev/null | grep -q "auto-run.py"; then
    echo "⚠️  检测到已存在的自动化任务，正在移除..."
    crontab -l 2>/dev/null | grep -v "auto-run.py" | crontab -
fi

# 添加新的cron任务
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "✅ 定时任务设置成功！"
echo "📅 执行时间: 每天上午9点"
echo "📝 日志位置: $PROJECT_DIR/logs/cron.log"
echo ""
echo "当前定时任务列表:"
crontab -l | grep auto-run.py