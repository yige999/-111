# 🚀 AutoSaaS Radar 集成测试指南

## 📋 测试清单 (窗口1执行)

### Phase 1: 环境验证 (2分钟)

#### 后端环境检查
- [ ] Python环境正常 (>= 3.8)
- [ ] 依赖包安装完成: `pip install -r requirements.txt`
- [ ] 环境变量配置完成: `.env` 文件存在
- [ ] Supabase连接可用
- [ ] OpenAI API Key可用

#### 前端环境检查
- [ ] Node.js环境正常 (>= 18)
- [ ] 依赖包安装完成: `npm install`
- [ ] Next.js项目可启动: `npm run dev`

### Phase 2: 后端API测试 (5分钟)

#### 基础健康检查
```bash
cd backend
python app.py
# 浏览器访问: http://localhost:8000/health
```

#### API接口测试
```bash
# 1. 健康检查
curl http://localhost:8000/health

# 2. 获取最新工具
curl http://localhost:8000/api/tools/latest?limit=5

# 3. 获取分类列表
curl http://localhost:8000/api/categories

# 4. 获取统计信息
curl http://localhost:8000/api/stats

# 5. 手动刷新数据
curl -X POST http://localhost:8000/api/tools/refresh
```

#### 数据流测试
- [ ] RSS抓取正常 (ProductHunt, Futurepedia)
- [ ] 社媒抓取正常 (Reddit, Hacker News)
- [ ] GPT分析正常 (痛点和点子生成)
- [ ] 数据库存储正常
- [ ] API返回格式正确

### Phase 3: 前端界面测试 (5分钟)

#### 页面加载测试
```bash
cd frontend
npm run dev
# 浏览器访问: http://localhost:3000
```

#### 功能验证
- [ ] 首页Dashboard正常显示
- [ ] 工具卡片渲染正确
- [ ] 趋势标记显示正常
- [ ] 筛选功能可用
- [ ] 响应式设计正常

### Phase 4: 完整工作流测试 (5分钟)

#### 自动化流程测试
```bash
# 运行每日扫描脚本
cd scripts
python daily_scan.py

# 检查调度器
python scheduler.py
```

#### 端到端验证
1. **数据抓取** → **AI分析** → **数据存储**
2. **API查询** → **前端展示** → **用户交互**
3. **自动化调度** → **定时执行** → **结果推送**

### Phase 5: 部署准备 (3分钟)

#### Vercel部署测试
```bash
# 前端部署测试
cd frontend
npm run build

# 检查部署配置
cat ../deploy/vercel.json
```

#### 环境变量检查
- [ ] 生产环境API URL配置
- [ ] Supabase生产环境配置
- [ ] OpenAI API生产环境配置
- [ ] 邮件推送配置 (可选)

## 🔧 快速故障排除

### 常见问题
1. **API端口冲突**: 修改config.py中的端口设置
2. **数据库连接失败**: 检查Supabase URL和Key
3. **前端构建失败**: 检查TypeScript类型错误
4. **CORS错误**: 检查API的CORS配置

### 应急方案
- **使用Mock数据**: 绕过真实API调用
- **本地数据库**: 使用SQLite替代Supabase
- **简化界面**: 跳过复杂样式和动画

## ✅ 测试完成标准

### 最低要求 (必须通过)
- [ ] 后端API可正常启动
- [ ] 至少抓取到1个工具数据
- [ ] 前端页面可正常打开
- [ ] 基础数据展示正常

### 理想状态 (加分项)
- [ ] 多个数据源正常工作
- [ ] GPT分析功能正常
- [ ] 完整筛选和搜索功能
- [ ] 部署到Vercel成功

### 卓越表现 (超出预期)
- [ ] 邮件推送功能正常
- [ ] 监控和日志完善
- [ ] 性能优化到位
- [ ] 文档完整详细

## 📊 测试结果记录

### 测试执行记录
```
开始时间: __:__:__
后端API启动: ✅/❌
前端页面加载: ✅/❌
数据抓取测试: ✅/❌
AI分析测试: ✅/❌
完整工作流: ✅/❌
部署测试: ✅/❌
完成时间: __:__:__
总耗时: __分钟
```

### 最终状态
- **功能完成度**: __%
- **测试通过率**: __%
- **部署状态**: ✅就绪/🟡待定/❌失败
- **总体评价**: 🟢优秀/🟡良好/🔴需要改进

---

*测试完成后立即更新PROGRESS.md最终状态！*