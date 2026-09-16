# QuantAgent-Invest

### 基于大模型多智能体与量化因子融合的智能投研系统设计与实现

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vue 3](https://img.shields.io/badge/Frontend-Vue%203-4FC08D?style=flat-square&logo=vue.js&logoColor=white)](https://vuejs.org/)
[![TypeScript](https://img.shields.io/badge/Language-TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![LangGraph](https://img.shields.io/badge/Multi--Agent-LangGraph-FF6F00?style=flat-square)](https://github.com/langchain-ai/langgraph)
[![MongoDB](https://img.shields.io/badge/Database-MongoDB-47A248?style=flat-square&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Redis](https://img.shields.io/badge/Cache-Redis-DC382D?style=flat-square&logo=redis&logoColor=white)](https://redis.io/)

</div>

---

## 📌 课题背景与研究目标

随着人工智能与金融科技的深度融合，大语言模型（LLM）在金融文本处理与投研推理中展现出巨大潜力。然而，通用大模型直接应用于证券投研时普遍存在以下痛点：
1. **结构化数据利用不足**：传统大模型擅长非结构化文本分析，但对海量高频量价、财务指标等数值特征的感知与计算能力较弱；
2. **量化分析能力受限**：大语言模型直接进行数学计算和统计推断极易产生幻觉，缺乏严谨的量化指标体系支撑；
3. **单一智能体缺乏审辩与可解释性**：单一智能体易受片面信息误导，缺乏专业金融机构内部“多部门协同、多空辩论、严格风控”的制衡机制。

为解决上述问题，本项目设计并实现了一套**融合量化因子分析与大模型多智能体协同推理的智能投研系统**。系统通过提取多维度量化特征矩阵作为结构化底座，构建基于角色分工的多智能体协同推理与交叉博弈框架，实现**“数据量化驱动”与“认知推理决策”的深度融合**。

---

## 🌟 核心使用模式

系统支持两种端到端的专业智能投研分析模式：

```
┌────────────────────────────────────────────────────────────────────────┐
│                        智能投研系统业务模式                           │
├───────────────────────────────────┬────────────────────────────────────┤
│   模式一：全市场量化选股 (Screening) │   模式二：指定股票直接分析 (Analysis)│
├───────────────────────────────────┼────────────────────────────────────┤
│   1. 全市场股票批量扫描           │   1. 用户输入目标股票代码/名称     │
│   2. 趋势/动量/量价/财务因子提取  │   2. 实时抽取该标的多维度量化特征  │
│   3. 多因子加权综合评分排序       │   3. 结构化特征输入多角色智能体    │
│   4. 构建并输出高分候选股票池     │   4. 宏观/基本面/技术/舆情独立研判 │
│   5. 一键推入多智能体研判队列     │   5. 多空辩论与风控审查(Bull vs Bear)│
│                                   │   6. 流式推导过程与结构化研报生成  │
└───────────────────────────────────┴────────────────────────────────────┘
```

---

## 🏗️ 系统整体架构设计

系统采用前后端分离的分层架构，核心分为四层：

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    表现层（Frontend - Vue 3 + TS）                     │
│    仪表盘看板 | 股票量化筛选 | 单股深度研判 | 批量分析 | 投研研报中心   │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ HTTP RESTful / WebSocket / SSE
┌────────────────────────────────────▼────────────────────────────────────┐
│                    控制与服务层（Backend - FastAPI）                   │
│    API路由网关 | 异步任务调度(Worker) | 缓存控制器 | 投研报告管理       │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│              多智能体协同推理引擎（LangGraph Multi-Agent Core）         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ 宏观分析师   │  │ 基本面分析师 │  │ 技术分析师   │  │ 舆情分析师   │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         └─────────────────┼─────────────────┘                 │         │
│                           ▼                                   │         │
│           多空对抗辩论机制（Bull vs Bear Debate）            │         │
│                           ▼                                   │         │
│           风险审查与合规仲裁（Risk Manager & Critic）         │         │
│                           ▼                                   │         │
│                 最终投资建议与决策生成                        │         │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│                    数据与量化因子特征层（Dataflows）                    │
│    AKShare 实时行情与资讯 | BaoStock 历史K线与财务 | 统一量化计算模块   │
│    趋势均线系统 | 动量振荡指标 | 波动率与成交量 | 财务成长与估值评分     │
└─────────────────────────────────────────────────────────────────────────┘
```

### 智能体角色分工一览
- **宏观分析师 (Macro Analyst)**：研判宏观经济指标、货币政策、利率环境与行业整体景气度。
- **基本面分析师 (Fundamental Analyst)**：深度解析资产负债表、利润表与现金流量表，评估估值合理性与财务健康度。
- **技术分析师 (Technical Analyst)**：依托量化指标（MA、MACD、KDJ、RSI、布林带等）分析量价形态、支撑阻力位与趋势动能。
- **新闻舆情分析师 (News / Sentiment Analyst)**：实时聚合财经资讯与公司公告，提炼市场情绪倾向并评估事件影响。
- **多空辩论团队 (Bull & Bear Researchers)**：分别基于正反面证据展开辩论交锋，充分暴露潜在风险与潜在机会。
- **风险审查官 (Risk Manager / Critic)**：作为最终合规防线，对所有智能体的推导逻辑进行交叉检验，消除模型幻觉并输出稳健策略。

---

## 🛠️ 技术栈

| 层次 | 技术选型 | 说明 |
| :--- | :--- | :--- |
| **前端开发** | Vue 3 + TypeScript + Vite | 响应式单页架构，类型安全 |
| **UI 与可视化** | Element Plus + ECharts | 金融图表、K线图、分析雷达图与看板 |
| **后端框架** | Python 3.12 + FastAPI | 高性能异步 RESTful API 与实时流 |
| **多智能体编排** | LangGraph + LangChain Core | 状态机驱动的智能体拓扑图与多轮博弈 |
| **持久化存储** | MongoDB 6.0+ | 存储股票基础数据、分析任务与历史报告 |
| **高速缓存** | Redis 6.0+ | 因子特征计算缓存与会话状态管理 |
| **金融数据源** | AKShare、BaoStock、Tushare | A股行情、历史 K 线与财务报表接入 |
| **大模型支持** | DeepSeek (V3/R1)、通义千问、OpenAI 等 | 支持 OpenAI 兼容协议与离线 Ollama 部署 |

---

## 📂 项目工程目录结构

```text
QuantAgent-Invest/
├── app/                      # FastAPI 后端核心应用
│   ├── core/                 # 系统核心配置、数据库客户端、日志配置
│   ├── routers/              # RESTful API 路由模块（筛选、分析、行情、报告等）
│   ├── services/             # 业务服务层（数据同步、因子计算、分析任务调度）
│   └── worker/               # 异步计算任务与后台工作进程
├── assets/                   # 必要的基础静态图标资源
├── config/                   # 系统运行时配置文件（logging.toml 等）
├── data/                     # 本地数据存储与缓存文件
├── docs/                     # 核心架构文档与学习中心本地知识库
│   ├── architecture/         # 系统多层架构设计说明
│   ├── learning/             # 交互式学习中心配套学术文章
│   └── paper/                # 核心支撑学术论文与中文导读
├── frontend/                 # Vue 3 + TypeScript 现代化前端工程
│   ├── src/views/            # 业务页面（仪表盘、股票筛选、单股研判、报告中心）
│   └── src/components/       # 可复用组件与金融图表组件
├── tradingagents/            # 核心算法体系
│   ├── agents/               # 各角色智能体定义与提示词工程实现
│   ├── graph/                # 基于 LangGraph 的多智能体工作流与拓扑定义
│   └── dataflows/            # 金融数据适配器与量化指标计算引擎
├── utils/                    # 数据基础设施辅助工具
├── start_dev.ps1             # 本地一键启动脚本
├── pyproject.toml            # Python 项目配置
├── requirements.txt          # 后端依赖环境列表
└── README.md                 # 项目介绍文档
```

---

## 🚀 本地开发与快速运行

### 1. 环境准备
- **Python**: 3.10+（推荐 Python 3.12）
- **Node.js**: 18+（推荐 Node.js 20 LTS）
- **数据库服务**: 本地安装并启动 MongoDB（端口 27017）与 Redis（端口 6379）

### 2. 配置环境变量
复制环境配置模板并填写必要配置（如大模型 API Key）：
```bash
cp .env.example .env
```

### 3. 一键启动（Windows PowerShell）

- **启动后端 API（推荐，极简直出模式，端口 8000）**：
  ```powershell
  .\start_dev.ps1
  ```
  > 默认直接前台启动后端服务并开启热重载（`--reload`），彩色日志实时直显，按 `Ctrl+C` 即可安全秒级退出。

- **启动前端开发服务器（Vite，端口 5173）**：
  ```powershell
  .\start_dev.ps1 frontend
  ```

- **启动分布式双进程模式（后端 API + 任务 Worker）**：
  ```powershell
  .\start_dev.ps1 -WithWorker
  ```

### 4. 分步手动启动（跨平台通用）
如需在 Linux/macOS 或独立调试各端，可分别执行以下命令：

**启动后端 API**：
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**启动前端界面**：
```bash
cd frontend
npm install
npm run dev
```
启动成功后，浏览器访问 `http://localhost:5173` 即可进入系统交互界面。

---

## ⚠️ 免责与学术研究声明

1. **学术研究用途**：本系统为高校计算机/人工智能与金融科技交叉课题的**毕业设计成果与实验演示平台**；
2. **非实盘投资建议**：系统中量化因子评分、大模型智能体研判结果均基于历史公开数据与特定 Prompt 生成，算法推导过程受模型偶发性与回测局限性影响，**不构成任何直接的证券投资操作建议**；
3. **市场有风险，投资需谨慎**。
