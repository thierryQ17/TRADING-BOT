# Polymarket RBI Bot — 项目文档

## 概述

一个完整的 Polymarket 自动化交易系统，使用 Python 和 FastAPI 从零构建。
4 个独立机器人、4 种策略（包括跟单交易）、Web 界面、回测、风险管理、Telegram/Email 警报、Docker 部署。

---

## 项目结构

```
TRADING BOT/
├── api/                    # FastAPI 服务器 + 机器人编排器
│   ├── server.py           # REST API 路由（端口 1818）+ 生命周期关闭
│   └── bot_manager.py      # 后台线程管理 4 个机器人
├── bot/                    # 交易执行逻辑
│   ├── trader.py           # 主循环：信号 → 风险 → 执行
│   ├── risk_manager.py     # 仓位限制、日亏损、止损
│   ├── order_manager.py    # 限价单管理 + 防重
│   └── position_tracker.py # 仓位和盈亏追踪（有文档记录的盈亏计算）
├── strategies/             # 4 种交易策略
│   ├── base_strategy.py    # 抽象基类（BUY/SELL/HOLD）
│   ├── macd_strategy.py    # MACD 直方图（3/15/3）— 动量策略
│   ├── rsi_mean_reversion.py # RSI(14) + VWAP — 均值回归
│   ├── cvd_strategy.py     # 累积成交量 delta — 背离策略
│   └── copytrade_strategy.py # 跟单交易 — 跟随最佳钱包
├── backtesting/            # 历史回测引擎
│   ├── engine.py           # 模拟器，含 K 线内止损（high/low）
│   ├── metrics.py          # 胜率、夏普比率、最大回撤、盈利因子
│   └── runner.py           # 多策略并行执行
├── data/                   # 数据访问
│   ├── downloader.py       # 通过 ccxt 下载 OHLCV 数据（Binance）
│   ├── polymarket_client.py # Polymarket CLOB API 客户端（限价单）
│   ├── wallet_scanner.py   # Polymarket 钱包扫描器（Gamma API）
│   └── storage.py          # 线程安全 SQLite（单例 + 锁）+ CSV
├── incubation/             # 监控、缩放和警报
│   ├── monitor.py          # 实时控制台仪表板
│   ├── scaler.py           # 资金缩放 $1 → $100，支持升级和降级
│   ├── alerter.py          # Telegram + Email 警报（SMTP Gmail）
│   └── logger.py           # 结构化 JSONL 日志 + 文件日志
├── dashboard/              # Web 界面
│   ├── index.html          # 主仪表板（浅灰色主题）
│   ├── audit.html          # 代码审计报告（15 个检查点）
│   ├── docs.html           # 完整项目文档
│   ├── guide.html          # 用户指南（模拟 + 实盘）
│   ├── guide_zh.html       # 用户指南（中文版）
│   ├── docs_zh.html        # 项目文档（中文版）
│   └── i18n.json           # 法语文本和工具提示（外部化）
│   └── i18n_zh.json        # 中文文本和工具提示
├── deploy/                 # 启动脚本
│   ├── run_backtest.py     # 运行 3 种技术策略的回测
│   ├── run_bot.py          # 命令行启动一个机器人（实时数据）
│   └── run_monitor.py      # 启动控制台监控
├── config/                 # 配置
│   ├── settings.py         # 线程安全 Settings 数据类 + 常量
│   └── accounts.py         # Polymarket 多账户
├── tests/                  # 单元测试 + 集成测试
│   ├── test_strategies.py  # 3 种技术策略测试
│   ├── test_copytrade.py   # 跟单交易测试（评分、信号、缓存）
│   ├── test_backtesting.py # 回测引擎测试
│   ├── test_risk_manager.py # 风险管理器测试
│   ├── test_api_integration.py # FastAPI 集成测试（16 个测试）
│   └── test_storage.py     # SQLite 并发测试（3 个测试）
├── nginx/                  # 反向代理配置
│   └── trading.conf        # trading.youpiare.fr 的 nginx 配置
├── scripts/                # 部署脚本
│   └── deploy.sh           # OVH VPS 自动部署
├── Dockerfile              # Python 3.12 Docker 镜像
├── docker-compose.yml      # 容器 + 卷 + 健康检查
├── .dockerignore           # 镜像中排除的文件
├── start.bat               # Windows 启动器（双击）
├── requirements.txt        # Python 依赖
├── .env.example            # 环境变量模板
├── .env                    # 私钥（不提交到版本控制）
└── .gitignore              # 版本控制排除的文件
```

---

## 已构建的内容

### 1. 四种交易策略

| 策略 | 类型 | 入场信号 | 数据源 |
|------|------|---------|--------|
| **MACD (3/15/3)** | 动量 / 趋势追踪 | MACD 线穿越信号线 | Binance（ccxt） |
| **RSI + VWAP** | 均值回归 | RSI < 30 + 价格在 VWAP 下方 | Binance（ccxt） |
| **CVD Divergence** | 成交量 Delta | 价格与成交量的背离 + 近似质量 | Binance（ccxt） |
| **跟单交易** | 社交交易 | 复制最佳钱包的仓位 | Polymarket Gamma API |

### 2. 跟单交易（策略 #4）

- **钱包扫描器**：通过 Polymarket Gamma API 发现活跃交易者
- **评分**：胜率、盈利因子、综合评分（60% 胜率 + 40% 盈利因子）
- **筛选**：排名前 N 的钱包，要求至少 20 笔交易且胜率 ≥ 55%
- **缓存**：每小时重新评分（可配置）
- **信号**：检测排名前钱包的新仓位并复制
- **动态 Token ID**：机器人自动适应排名前钱包交易的品种
- **置信度**：同意的钱包数 / 总数 × 最佳钱包评分

### 3. 回测引擎

- 通过 ccxt 下载历史数据（Binance）
- 在数据上执行策略，含止损和止盈
- **K线内止损**：检查 high/low（不仅是收盘价）— 保守方法
- 计算：胜率、盈利因子、最大回撤、夏普比率（按交易计算，不年化）
- 多策略并行执行
- 命令：`python deploy/run_backtest.py`

### 4. 实时交易系统

- **交易者**：信号 → 风险验证 → 订单执行的循环
  - 实时模式：可调用的 `data_fetcher` 获取实时数据
  - 回放模式：静态 DataFrame 用于开发/回测
  - 跟单模式：扫描钱包 → 检测信号 → 执行
  - `on_trade` 回调向 BotManager 报告事件
- **风险管理器**：仓位限额、最大持仓数、最大日亏损、止损/止盈
- **订单管理器**：仅限限价单（Polymarket 0 手续费），防重
- **仓位追踪器**：追踪开仓仓位、已实现/未实现盈亏
- 默认开启 **DRY_RUN** 模式（无真实订单）

### 5. 警报（Telegram + Email）

- **Telegram**：通过 Bot API（免费、无限制）
- **Email**：通过 SMTP Gmail（应用密码）
- 两个渠道并行运行
- 防spam，每个警报类型有冷却时间

| 事件 | 阈值 | 冷却时间 |
|------|------|---------|
| 单笔交易亏损 | > $5 | 15 分钟 |
| 单笔交易盈利 | > $10 | 15 分钟 |
| 日亏损 | > $20 | 1 小时 |
| 日盈利 | > $50 | 1 小时 |
| 升级/降级 | 始终 | 即时 |
| 机器人错误/全部停止 | 始终 | 即时 |

### 6. 孵化和缩放

- 渐进式规模：$1 → $5 → $10 → $50 → $100
- 升级条件：至少 20 笔交易，胜率 > 55%，盈利因子 > 1.3
- **自动降级**：胜率 < 40% 或连续 5 次亏损 → 返回上一级
- 持续监控，结构化日志（JSONL）

### 7. REST API（FastAPI）

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/bots` | 4 个机器人的状态 |
| POST | `/api/bots/{key}/start?token_id=...` | 启动机器人（token_id 可选） |
| POST | `/api/bots/{key}/stop` | 停止机器人 |
| POST | `/api/bots/kill-all` | 紧急停止 |
| GET | `/api/metrics` | 全局指标 |
| GET | `/api/trades?limit=50` | 交易日志 |
| GET | `/api/risk` | 风险管理器状态 |
| GET | `/api/settings` | 当前参数 |
| PUT | `/api/settings` | 修改参数（Pydantic 验证） |
| GET | `/api/alerts/status` | 警报状态 |
| POST | `/api/alerts/test` | 发送测试消息 |

- **验证**：`position_size`（0-1000$）、`stop_loss_pct`（0-100%）、`take_profit_pct`（0-100%）
- **CORS**：默认限制为 localhost:1818（可通过 `CORS_ORIGINS` 配置）
- **优雅关闭**：FastAPI 生命周期 → `kill_all()` + `close_db()`
- Swagger 文档：http://localhost:1818/docs

### 8. Web 仪表板

- **4 张机器人卡片**，含启动/停止开关、迷你图、成功率、盈亏
- **4 个关键指标**：总盈亏、最佳策略、交易总数、夏普比率
- **资金曲线**（按策略显示）
- **成功率对比**（柱状图）
- **风险管理**：日亏损条、开仓机器人、每个机器人的仓位、紧急停止按钮
- **交易日志**（可排序，最近 50 笔交易）
- **参数设置**：仓位大小、止损、止盈、模拟模式、账户
- 浅灰色主题，响应式设计
- 所有元素有工具提示
- 文本外部化到 `i18n.json`
- 链接：指南、文档、审计和 API

### 9. 文档

- **docs.html**：完整文档
- **audit.html**：代码审计报告（15 个检查点）
- **guide.html**：用户指南（模拟 + 实盘，15 个步骤）
- **docs_zh.html**：完整文档（中文版）
- **guide_zh.html**：用户指南（中文版）
- 可从仪表板访问

### 10. 部署

- **本地**：`start.bat`（双击）或 Docker（`docker compose up -d`）
- **Docker**：Dockerfile + docker-compose.yml，端口 8818，持久化卷，健康检查
- **OVH VPS**：`deploy.sh` 脚本，nginx 反向代理，Let's Encrypt SSL
- **子域名**：`trading.youpiare.fr`（需在 OVH DNS 配置）

### 11. 测试

- **47 个测试**总计
- 单元测试：3 种技术策略、回测、风险管理器
- 跟单交易测试：钱包评分、信号、缓存、去重（11 个测试）
- 集成测试：FastAPI（16 个测试）、SQLite 并发（3 个测试）
- 命令：`python -m pytest tests/ -v`

---

## 架构技术

### 线程安全配置

可变参数封装在带 `threading.Lock` 的 `Settings` 数据类中。
常量（策略参数、端点）保持在模块级别。
每个机器人在实例化时收到自己的 `dry_run` 副本 — 无全局状态修改。

### 线程安全 SQLite

连接单例使用 `check_same_thread=False` 和 `threading.Lock` 序列化写入。
关闭时调用 `close_db()`。

### 跟单交易

跟单交易策略使用**适配器模式**：它实现 `BaseStrategy`，但内部委托给 `WalletScanner` 获取 Polymarket Gamma API。`token_id` 是动态的 — 根据排名前钱包交易的品种变化。

---

## 配置

### 环境变量（.env）

| 变量 | 描述 | 默认值 |
|------|------|--------|
| `POLYMARKET_PRIVATE_KEY` | Polygon 钱包私钥 | — |
| `POLYMARKET_FUNDER_ADDRESS` | 钱包地址 | — |
| `POLYMARKET_TOKEN_ID` | 要交易的品种 Token ID（留空 = 模拟） | — |
| `MAX_POSITION_SIZE` | 每笔仓位最大金额（$） | 10 |
| `MAX_DAILY_LOSS` | 最大日亏损（$） | 50 |
| `MAX_OPEN_POSITIONS` | 最大开仓数 | 3 |
| `DRY_RUN` | 模拟模式 | true |
| `CORS_ORIGINS` | 允许的 CORS 来源 | localhost:1818 |
| `LOG_LEVEL` | 日志级别 | INFO |
| `TELEGRAM_BOT_TOKEN` | Telegram 机器人 Token | — |
| `TELEGRAM_CHAT_ID` | Telegram 聊天 ID | — |
| `SMTP_USER` | Gmail 警报邮箱 | — |
| `SMTP_PASSWORD` | Gmail 应用密码 | — |
| `ALERT_EMAIL_TO` | 警报接收邮箱 | SMTP_USER |
| `ALERT_LOSS_THRESHOLD` | 单笔交易亏损阈值（$） | 5 |
| `ALERT_GAIN_THRESHOLD` | 单笔交易盈利阈值（$） | 10 |
| `ALERT_DAILY_LOSS_THRESHOLD` | 日亏损阈值（$） | 20 |
| `ALERT_DAILY_GAIN_THRESHOLD` | 日盈利阈值（$） | 50 |
| `COPYTRADE_MIN_TRADES` | 钱包评分的最小交易数 | 20 |
| `COPYTRADE_MIN_WIN_RATE` | 排名前钱包的最低胜率 | 0.55 |
| `COPYTRADE_TOP_N` | 跟随的钱包数量 | 6 |
| `COPYTRADE_SCAN_INTERVAL` | 扫描间隔（秒） | 60 |
| `COPYTRADE_RESCORE_INTERVAL` | 重新评分间隔（秒） | 3600 |

---

## 依赖

- py-clob-client（Polymarket API）
- pandas、numpy（计算）
- ta（技术指标）
- ccxt（Binance 市场数据）
- requests（Polymarket Gamma API）
- fastapi、uvicorn（Web 服务器）
- python-dotenv（配置）
- Chart.js（仪表板图表 — 通过 CDN）

---

## 启动

```bash
# 方法一 — Windows（双击）
start.bat
# → http://localhost:1818

# 方法二 — Docker
docker compose up -d --build
# → http://localhost:8818

# 方法三 — 手动
cd "C:\DEV POWERSHELL\__Q17\TRADING BOT"
.venv\Scripts\activate
python api/server.py
# → http://localhost:1818
```

---

## 安全

- 默认开启 DRY_RUN 模式
- 私钥存储在 .env（不提交到版本控制）
- CORS 限制为 localhost（可配置）
- 所有可修改参数均通过 Pydantic 验证
- 仅限限价单（0 手续费）
- 风险管理器阻止超出限额的交易
- 缩放器降级保护资金
- 优雅关闭保存状态
- Telegram/Email 警报通知亏损和错误
- 仪表板紧急停止按钮

---

## 中文本地化说明

本中文翻译版由 Claude Code 自动生成。
原始项目：[thierryQ17/TRADING-BOT](https://github.com/thierryQ17/TRADING-BOT)
中文版：[santbabaq-ops/TRADING-BOT](https://github.com/santbabaq-ops/TRADING-BOT)
