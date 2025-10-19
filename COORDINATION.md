# 总协调指南 — AutoSaaS Radar

## 🎯 窗口1总协调职责

### 前期准备（0-10分钟）
- [x] 创建协作框架文档
- [x] 制定API契约
- [x] 设计数据库结构
- [ ] 检查各窗口初始化状态
- [ ] 确认环境配置要求

### 中期协调（10-20分钟）
- [ ] 实时跟踪各窗口进度
- [ ] 解决跨模块依赖问题
- [ ] 更新整体进度状态
- [ ] 处理阻塞和异常问题

### 后期整合（20-30分钟）
- [ ] 组织集成测试
- [ ] 协调部署准备
- [ ] 验证功能完整性
- [ ] 最终交付检查

## 📊 进度检查清单

### 每分钟检查点
**第5分钟**: 确认所有窗口开始初始化
**第10分钟**: 检查基础架构完成情况
**第15分钟**: 确认核心功能开发进度
**第20分钟**: 验证模块间集成状态
**第25分钟**: 检查部署准备情况
**第30分钟**: 最终功能验证

### 关键依赖关系
```
窗口2,3 (数据抓取) ← 依赖 ← 窗口5 (数据库)
     ↓
窗口4 (GPT分析) ← 依赖 ← 窗口2,3 的数据
     ↓
窗口6 (API接口) ← 依赖 ← 窗口4,5 的结果
     ↓
窗口7,8,9 (前端) ← 依赖 ← 窗口6 的API
     ↓
窗口10 (部署) ← 依赖 ← 所有其他窗口
```

## 🚨 应急处理

### 常见问题解决方案
1. **模块初始化失败**: 检查环境变量配置
2. **API调用失败**: 检查密钥和网络连接
3. **数据库连接问题**: 验证Supabase配置
4. **前端构建失败**: 检查依赖版本兼容性

### 紧急联系协议
- 发现问题立即记录到ISSUES.md
- 在PROGRESS.md更新对应窗口状态
- 如有阻塞，立即通知相关窗口

## 📋 快速状态查询

### 各窗口关键文件检查
- 窗口2: `backend/scrapers/rss_scraper.py`
- 窗口3: `backend/scrapers/social_media_collector.py`
- 窗口4: `backend/analyzer/gpt_analyzer.py`
- 窗口5: `backend/database/supabase_client.py`
- 窗口6: `backend/api/main.py`
- 窗口7: `frontend/pages/index.js`
- 窗口8: `frontend/pages/explore.js`
- 窗口9: `frontend/components/ToolCard.js`
- 窗口10: `scripts/daily_scan.py`

### 快速验证命令
```bash
# 检查Python后端状态
cd backend && python -c "import fastapi, supabase, openai; print('Backend OK')"

# 检查前端状态
cd frontend && npm run build

# 检查数据库连接
cd database && python test_connection.py

# 运行快速测试
make quick-test
```

## 🎯 30分钟倒计时策略

### Phase 1: 快速启动 (0-10分钟)
- 确保所有窗口理解任务
- 检查基础环境配置
- 解决初始化问题

### Phase 2: 并行开发 (10-20分钟)
- 监控各窗口开发进度
- 处理依赖和阻塞问题
- 保持进度同步

### Phase 3: 集成部署 (20-30分钟)
- 组织功能集成测试
- 协调最终部署
- 验证完整工作流

---

*总协调原则：主动发现问题、快速响应解决、确保按时交付*