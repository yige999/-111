# 需要提供的数据 — AutoSaaS Radar

## ✅ 已提供的数据
- **Supabase URL**: https://waxecskeegviaslbvaw.supabase.co
- **Supabase Anon Key**: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... (已配置)

## ✅ 刚提供的数据

### 1. OpenAI API Key (已提供)
- **用途**: AI 分析工具痛点 + 生成 Micro SaaS 点子
- **重要性**: ⭐⭐⭐⭐⭐ (核心功能已就绪)
- **状态**: ✅ 已配置
- **Key**: sk-JLEVLKIf27vTwQLKCa043bF3FfF4499bA5BbA4E9F443A569

### 2. Supabase Service Role Key (建议)
- **用途**: 服务端数据库操作权限
- **重要性**: ⭐⭐⭐⭐ (绕过 RLS 限制)
- **获取方式**: Supabase Dashboard > Settings > API
- **格式**: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

## 🟡 可选但推荐的数据

### 3. Reddit API (提升数据质量)
- **用途**: 抓取 r/SaaS, r/SideProject 讨论
- **重要性**: ⭐⭐⭐ (增加数据源多样性)
- **获取方式**: https://www.reddit.com/prefs/apps
- **需要**: Client ID + Client Secret

### 4. SMTP 邮件配置 (推送功能)
- **用途**: 每日自动发送趋势报告
- **重要性**: ⭐⭐ (提升用户体验)
- **需要**: 邮箱 + App Password

## 🚀 30分钟 MVP 策略

### 最低要求 (必须提供):
```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx
```

### 完整功能 (推荐提供):
```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
```

## 📋 当前配置状态

| 配置项 | 状态 | 优先级 |
|--------|------|--------|
| Supabase URL | ✅ 已配置 | 高 |
| Supabase Anon Key | ✅ 已配置 | 高 |
| OpenAI API Key | 🔴 需要提供 | 最高 |
| Supabase Service Key | 🟡 建议提供 | 高 |
| Reddit API | 🟡 可选提供 | 中 |
| SMTP 配置 | 🟡 可选提供 | 低 |

---

**请优先提供 OpenAI API Key，这样 10 个窗口就可以开始并行开发了！**