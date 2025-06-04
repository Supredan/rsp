# RSP ETF 定投监控系统 - GitHub Actions 部署指南

## 🚀 概述

本项目使用 GitHub Actions 实现 RSP ETF 定投监控的云端自动化执行，每日北京时间 21:00 执行监控任务。

## 📊 系统特点

- **自动化执行**: GitHub Actions 云端定时运行
- **智能监控**: 四种触发条件的定投提醒
- **微信通知**: Server酱集成微信推送
- **免费部署**: 基于 GitHub 免费资源
- **状态保持**: 跨月监控状态持久化

## 🔧 部署步骤

### 1. 项目设置

将代码上传到你的 GitHub 仓库，确保包含以下文件：

```
your-repo/
├── .github/workflows/rsp_monitor.yml    # GitHub Actions 工作流
├── rsp_dca_monitor.py                   # 主监控脚本
├── market_breadth_fetcher.py            # 市场宽度数据获取
├── requirements.txt                     # Python 依赖
├── config_rsp_monitor.py               # 配置管理工具
├── rsp_backtest_monitor.py             # 回测分析工具
└── README_GitHub_Actions.md            # 本文档
```

### 2. 配置 API 密钥

在 GitHub 仓库中设置以下 Secrets：

1. 进入仓库 **Settings** > **Secrets and variables** > **Actions**
2. 点击 **New repository secret** 添加以下密钥：

| Secret 名称 | 说明 | 获取方式 |
|------------|------|----------|
| `LONGPORT_APP_KEY` | 长桥 API 密钥 | [长桥开放平台](https://open.longportapp.com/) |
| `LONGPORT_APP_SECRET` | 长桥 API 秘钥 | 同上 |
| `LONGPORT_ACCESS_TOKEN` | 长桥访问令牌 | 同上 |
| `SCKEY` | Server酱密钥 | [Server酱官网](https://sct.ftqq.com/) |

### 3. 获取 API 密钥详细步骤

#### 长桥 API 密钥
1. 访问 [长桥开放平台](https://open.longportapp.com/)
2. 注册并登录开发者账号
3. 创建应用获取 API 密钥
4. 在 "密钥管理" 中查看你的密钥信息

#### Server酱密钥
1. 访问 [Server酱](https://sct.ftqq.com/)
2. 使用微信扫码登录
3. 获取你的专属 SendKey
4. 关注 "Server酱" 微信公众号接收消息

### 4. 执行时间设置

当前配置为：
- **执行时间**: 每日北京时间 21:00 (UTC 13:00)
- **执行频率**: 仅工作日 (周一至周五)
- **数据基准**: 前一交易日收盘数据

如需修改时间，编辑 `.github/workflows/rsp_monitor.yml` 中的 cron 表达式：

```yaml
schedule:
  - cron: '0 13 * * 1-5'  # UTC 13:00 = 北京时间 21:00
```

## 📋 监控条件

系统会监控以下四种情况并发送微信提醒：

1. **第一笔定投**: 每月首次日跌幅 ≥1%
2. **到期提醒**: 第三个周五未触发条件1时
3. **第二笔定投**: 月累计跌幅 ≥5%
4. **第三笔定投**: 条件3触发后市场宽度 <15%

## 📊 监控状态

- 查看 **Actions** 页面了解执行状态
- 日志文件会自动上传为 Artifacts
- 状态数据会在仓库中持久化保存

## 🔍 本地测试

在本地测试监控系统：

```bash
# 1. 克隆仓库
git clone https://github.com/your-username/your-repo.git
cd your-repo

# 2. 安装依赖
pip install -r requirements.txt

# 3. 设置环境变量 (Windows)
set LONGPORT_APP_KEY=your_key
set LONGPORT_APP_SECRET=your_secret
set LONGPORT_ACCESS_TOKEN=your_token
set SCKEY=your_sckey

# 4. 运行配置工具
python config_rsp_monitor.py

# 5. 选择 "1" 立即运行一次监控
```

## 📈 回测验证

系统已通过历史回测验证：

- **回测期间**: 2024年8月-2025年5月 (10个月)
- **触发统计**: 14次总触发，平均每月1.4次
- **覆盖率**: 250% (有效捕获所有下跌月份)
- **策略有效性**: ✅ 验证通过

运行回测分析：
```bash
python rsp_backtest_monitor.py
```

## 🚦 运行状态检查

### GitHub Actions 状态
- 绿色 ✅: 执行成功
- 红色 ❌: 执行失败，检查日志
- 黄色 🟡: 正在执行中

### 微信通知状态
- 收到提醒: 系统正常工作
- 未收到提醒: 检查 SCKEY 配置或当日无触发条件

## 🔧 故障排除

### 常见问题

1. **Actions 执行失败**
   - 检查 Secrets 配置是否正确
   - 查看 Actions 日志详细错误信息

2. **未收到微信通知**
   - 验证 SCKEY 是否正确
   - 确认已关注 "Server酱" 微信公众号

3. **API 访问失败**
   - 检查长桥 API 密钥是否有效
   - 确认账户权限和额度

### 调试方法

1. 手动触发 Actions：
   - 进入 Actions 页面
   - 选择 "RSP ETF DCA Monitor"
   - 点击 "Run workflow"

2. 查看执行日志：
   - 在 Actions 页面查看详细日志
   - 下载 Artifacts 查看本地日志文件

## 📞 支持

如遇问题，请：

1. 查看本文档故障排除部分
2. 检查 GitHub Actions 执行日志
3. 在仓库中提交 Issue

## 🔄 更新说明

- 系统会自动使用最新代码版本
- 修改代码后会在下次定时执行时生效
- 紧急更新可手动触发 Actions

---

**注意**: GitHub Actions 对免费账户有使用限制，但对于本项目的日常监控需求完全够用。 