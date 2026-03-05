# 量化交易策略工具 - 设计文档

**日期**: 2026-03-05
**版本**: v1.0 (MVP)

## 1. 项目概述

一个量化投资工具，用于按策略选择股票，侧重实时交易信号，更策略化。

### 目标
- 预设常用策略供用户选择
- 支持策略回测
- 实时交易信号推送
- 钉钉/邮件通知

## 2. 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                      Web 浏览器 (Vue 3)                  │
│  ┌──────────┐  ┌──────────┐  ┌────────┐  ┌─────────┐  │
│  │ 策略选择 │  │ 回测界面 │  │实时信号│  │ 系统设置 │  │
│  └──────────┘  └──────────┘  └────────┘  └─────────┘  │
└─────────────────────────────────────────────────────────┘
                          │ HTTP/WebSocket
                          ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI 后端 (Python)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │  策略引擎     │  │   回测引擎    │  │  信号通知器    │ │
│  └──────────────┘  └──────────────┘  └───────────────┘ │
└─────────────────────────────────────────────────────────┘
         │                  │                  │
         ▼                  ▼                  ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   SQLite     │   │   Tushare    │   │  钉钉/邮件    │
│   数据库     │   │   API        │   │  API          │
└──────────────┘   └──────────────┘   └──────────────┘
```

## 3. 核心功能模块

### 3.1 预设策略模块

| 策略类型 | 策略名称 | 核心逻辑 |
|---------|---------|---------|
| 技术指标 | 均线双金叉 | MA5上穿MA20 + MACD金叉 |
| 技术指标 | RSI超跌反弹 | RSI < 30 后拐头向上 |
| 技术指标 | 动量突破 | 价格突破20日新高 + 成交量放大 |
| 多因子 | 基本面+技术面 | PE/PB合理 + ROE > 15% + 均线多头 |
| 多因子 | 量价齐升 | 主力连续3天净流入 + 价格站上MA20 |
| 反转 | 超跌反弹 | 连续下跌后缩量企稳 |

### 3.2 回测引擎
- 输入：策略 + 时间范围 + 初始资金
- 输出：收益率曲线、最大回撤、胜率、夏普比率
- 支持：日线数据回测

### 3.3 实时信号模块
- 定时任务：每小时检查（交易日），第一阶段先用日线
- 信号触发：记录到 SQLite + 推送通知
- 信号展示：实时信号列表 + 历史信号查询

### 3.4 通知模块
- 钉钉：机器人 Webhook
- 邮件：SMTP 发送（第二阶段）

## 4. 技术栈

### 后端
- **框架**: FastAPI + Uvicorn
- **数据库**: SQLite + SQLAlchemy (ORM)
- **数据处理**: pandas, numpy
- **数据源**: tushare
- **任务调度**: APScheduler

### 前端
- **框架**: Vue 3 (Composition API) + Vite
- **路由**: Vue Router
- **状态管理**: Pinia
- **UI 组件**: Element Plus
- **图表**: ECharts
- **HTTP 客户端**: Axios

## 5. 数据模型

### Stock (股票基本信息)
- `ts_code`: 股票代码
- `name`: 股票名称
- `industry`: 行业
- `list_date`: 上市日期

### Strategy (策略配置)
- `id`: 主键
- `name`: 策略名称
- `type`: 类型 (technical/multi_factor/reversal)
- `params`: JSON 参数配置
- `is_active`: 是否启用
- `created_at`: 创建时间

### Backtest (回测记录)
- `id`: 主键
- `strategy_id`: 关联策略
- `start_date`: 开始日期
- `end_date`: 结束日期
- `initial_capital`: 初始资金
- `final_capital`: 最终资金
- `total_return`: 总收益率
- `max_drawdown`: 最大回撤
- `win_rate`: 胜率
- `sharpe_ratio`: 夏普比率
- `created_at`: 创建时间

### Signal (交易信号)
- `id`: 主键
- `ts_code`: 股票代码
- `strategy_id`: 来源策略
- `signal_type`: BUY/SELL/HOLD
- `price`: 触发价格
- `signal_date`: 信号日期
- `signal_time`: 信号时间（小时级）
- `is_sent`: 是否已通知
- `created_at`: 创建时间

### Config (系统配置)
- `key`: 配置键
- `value`: 配置值

## 6. 项目结构

```
quant-trader/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置
│   ├── database.py          # SQLite 连接
│   ├── models.py            # SQLAlchemy 模型
│   ├── api/
│   │   ├── strategies.py    # 策略 API
│   │   ├── backtest.py      # 回测 API
│   │   ├── signals.py       # 信号 API
│   │   └── notify.py        # 通知 API
│   ├── core/
│   │   ├── strategy_engine.py   # 策略引擎
│   │   ├── backtest_engine.py   # 回测引擎
│   │   ├── data_fetcher.py      # Tushare 数据获取
│   │   └── notifier.py          # 钉钉/邮件通知
│   └── strategies/          # 预设策略实现
│       ├── technical.py
│       ├── multi_factor.py
│       └── reversal.py
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── api/           # API 调用
│   │   ├── components/
│   │   │   ├── StrategySelector.vue
│   │   │   ├── BacktestChart.vue
│   │   │   ├── SignalList.vue
│   │   │   └── SettingsForm.vue
│   │   └── views/
│   │       ├── Dashboard.vue
│   │       ├── Backtest.vue
│   │       └── Signals.vue
├── docs/
│   └── plans/
│       └── 2026-03-05-quant-trader-design.md
└── README.md
```

## 7. 第一阶段实现范围 (MVP)

### 必做功能
- 预设策略（5-6个核心策略）
- 策略参数配置界面
- 日线回测引擎 + 结果展示
- 日线级实时信号扫描
- 信号列表展示
- 钉钉通知
- SQLite 数据持久化

### 第二阶段
- 可视化策略编辑器
- 小时级数据
- 邮件通知
- 实盘交易对接
