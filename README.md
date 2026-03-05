# Quant Trader

量化交易策略工具 - 按策略选择股票，侧重实时交易信号和策略回测。

## 功能特性

- 预设策略（均线双金叉、RSI超跌反弹、动量突破、多因子选股、量价齐升）
- 策略回测（收益率、最大回撤、胜率、夏普比率）
- 实时信号扫描
- 钉钉通知
- Web 界面

## 技术栈

**后端:**
- FastAPI
- SQLAlchemy + SQLite
- Tushare
- APScheduler

**前端:**
- Vue 3 + Vite
- Element Plus
- ECharts
- Pinia + Vue Router

## 快速开始

### 1. 后端启动

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 复制并配置 .env
cp .env.example .env
# 编辑 .env，填入 Tushare Token 和钉钉 Webhook

# 启动
uvicorn main:app --reload --port 8000
```

### 2. 前端启动

```bash
cd frontend
npm install
npm run dev
```

### 3. 访问

打开浏览器访问 http://localhost:5173

## 项目结构

```
quant-trader/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置
│   ├── database.py          # 数据库
│   ├── models.py            # 数据模型
│   ├── api/                 # API 路由
│   ├── core/                # 核心模块
│   └── strategies/          # 策略实现
├── frontend/
│   ├── src/
│   │   ├── views/           # 页面
│   │   ├── components/      # 组件
│   │   ├── api/             # API 调用
│   │   └── router/          # 路由
│   └── package.json
└── docs/
    └── plans/               # 设计文档
```

## 注意事项

- 仅供学习研究，不构成投资建议
- Tushare API 有调用频率限制
- 实盘交易请谨慎
