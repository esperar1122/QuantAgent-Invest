# 智能投研系统：融合量化因子分析与大模型多智能体协同推理

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Frontend-Vue%203-green.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-teal.svg)](https://fastapi.tiangolo.com/)

---

## 📌 项目简介

本项目面向人工智能与金融投资深度融合的应用场景，针对传统大模型在股票投研中结构化数据利用不足、量化分析能力有限及可解释性较弱等问题，设计并实现一套融合量化因子分析与大模型多智能体协同推理的智能投研系统。

系统以股票市场数据为基础，自主实现轻量级量化因子分析模块，从趋势、动量、量价、波动率及基本面等多维度提取股票特征并形成综合评分。系统支持“全市场量化选股”和“指定股票直接分析”两种使用模式：前者对全市场股票进行批量筛选，构建候选股票池供用户选择；后者直接对目标股票进行因子计算并进入多智能体研判。

在智能投研分析层面，系统构建多智能体协同推理框架，将目标股票的量化因子分析结果作为结构化信息输入，由宏观分析、基本面分析、技术分析和风险审查等角色智能体分别开展独立研判并进行交叉博弈，最终生成具备清晰逻辑链条和多空论证的投研决策报告。

---

**🎯 我们的定位与使命**: 专注学习与研究，提供中文化学习中心与工具，合规友好，支持 A股/港股/美股 的分析与教学，推动 AI 金融技术在中文社区的普及与正确使用。

## 🎉 v1.1.0 版本说明 - 火山方舟集成与开发体验增强

> 🚀 **当前推荐版本**: `v1.1.0` 已正式可用，在 v1.0.1 基础上，重点集成火山方舟模型服务、增强推理模型支持、统一开发启动脚本，并完善项目文档体系。

### ✨ 核心特性

#### 🏗️ **全新技术架构**
- **后端升级**: 从 Streamlit 迁移到 FastAPI，提供更强大的 RESTful API
- **前端重构**: 采用 Vue 3 + Element Plus，打造现代化的单页应用
- **数据库优化**: MongoDB + Redis 双数据库架构，性能提升 10 倍
- **容器化部署**: 完整的 Docker 多架构支持（amd64 + arm64）

#### 🚀 **v1.1.0 重点增强**
- **火山方舟集成**: 新增火山方舟（VolcEngine Ark）Provider，支持编程版模型硬编码配置与密码兼容
- **推理模型优化**: `reasoning_effort` 全链路传递，推理模型超时保护优化
- **数据模型扩展**: 添加 `reasoning_effort` / `test_model` 字段，支持火山方舟模型过滤
- **统一启动脚本**: 新增 `start_dev.ps1`，支持 v1.0/v2.0/v2.1/v3.0 多版本开发环境一键启动
- **连接修复**: MongoDB 连接字符串自动构建，Tushare 写 tk.csv 权限错误修复
- **文档体系完善**: 更新版权声明与授权说明、贡献者指南（贡献换授权机制）、项目发展战略规划

#### 🎯 **企业级功能**
- **用户权限管理**: 完整的用户认证、角色管理、操作日志系统
- **配置管理中心**: 可视化的大模型配置、数据源管理、系统设置
- **缓存管理系统**: 智能缓存策略，支持 MongoDB/Redis/文件多级缓存
- **实时通知系统**: SSE+WebSocket 双通道推送，实时跟踪分析进度和系统状态
- **批量分析功能**: 支持多只股票同时分析，提升工作效率
- **智能股票筛选**: 基于多维度指标的股票筛选和排序系统
- **自选股管理**: 个人自选股收藏、分组管理和跟踪功能
- **个股详情页**: 完整的个股信息展示和历史分析记录

#### 🤖 **智能分析增强**
- **动态供应商管理**: 支持动态添加和配置 LLM 供应商
- **模型能力管理**: 智能模型选择，根据任务自动匹配最佳模型
- **多数据源同步**: 统一的数据源管理，支持 Tushare、AkShare、BaoStock
- **报告导出功能**: 支持 Markdown/Word/PDF 多格式专业报告导出

#### 🔧 **重大Bug修复**
- **技术指标计算修复**: 彻底解决市场分析师技术指标计算不准确问题
- **基本面数据修复**: 修复基本面分析师PE、PB等关键财务数据计算错误
- **死循环问题修复**: 解决部分用户在分析过程中触发的无限循环问题
- **数据一致性优化**: 确保所有分析师使用统一、准确的数据源


### 📊 技术栈升级

| 组件 | v0.1.x | v1.1.0 |
|------|--------|----------------|
| **后端框架** | Streamlit | FastAPI + Uvicorn |
| **前端框架** | Streamlit | Vue 3 + Vite + Element Plus |
| **数据库** | 可选 MongoDB | MongoDB + Redis |
| **API 架构** | 单体应用 | RESTful API + WebSocket |
| **部署方式** | 本地/Docker | Docker 多架构 + GitHub Actions |


⚠️ **重要提醒**：在分析股票之前，请按相关文档要求，将股票数据同步完成，否则分析结果将会出现数据错误。



#### 📚 使用指南

在使用前，建议先阅读详细的使用指南：
- **[v1.1.0 发布说明](./docs/releases/v1.1.0-release-notes.md)**
- **[v1.1.0 使用手册](./docs/guides/v1.1.0-user-manual.md)**
- **[v1.1.0 升级指南](./docs/releases/upgrade-guide.md)**
- **[完整更新日志](./docs/releases/CHANGELOG.md)**
- **[0、📘 TradingAgents-CN v1.0.0-preview 快速入门视频](https://www.bilibili.com/video/BV1i2CeBwEP7/?vd_source=5d790a5b8d2f46d2c10fd4e770be1594)**

- **[1、📘 TradingAgents-CN v1.0.0-preview 使用指南](https://mp.weixin.qq.com/s/ppsYiBncynxlsfKFG8uEbw)**
- **[2、📘 使用 Docker Compose 部署TradingAgents-CN v1.0.0-preview（完全版）](https://mp.weixin.qq.com/s/JkA0cOu8xJnoY_3LC5oXNw)**
- **[3、📘 从 Docker Hub 更新 TradingAgents‑CN 镜像](https://mp.weixin.qq.com/s/WKYhW8J80Watpg8K6E_dSQ)**
- **[4、📘 TradingAgents-CN v1.0.0-preview绿色版安装和升级指南](https://mp.weixin.qq.com/s/eoo_HeIGxaQZVT76LBbRJQ)**
- **[5、📘 TradingAgents-CN v1.0.0-preview绿色版端口配置说明](https://mp.weixin.qq.com/s/o5QdNuh2-iKkIHzJXCj7vQ)**
- **[6、📘 TradingAgents v1.0.0-preview 源码版安装手册（修订版）](https://mp.weixin.qq.com/s/cqUGf-sAzcBV19gdI4sYfA)**
- **[7、📘 TradingAgents v1.0.0-preview 源码安装视频教程](https://www.bilibili.com/video/BV1FxCtBHEte/?vd_source=5d790a5b8d2f46d2c10fd4e770be1594)**


使用指南包含：
- ✅ 完整的功能介绍和操作演示
- ✅ 详细的配置说明和最佳实践
- ✅ 常见问题解答和故障排除
- ✅ 实际使用案例和效果展示

### 数据库运维补充

- 数据库版本隔离、共享库保护、迁移脚本与 provider 规范化说明：
  - [数据库版本隔离与 Provider 规范化](./docs/deployment/database/DB_VERSION_ISOLATION_AND_PROVIDER_NORMALIZATION.md)

### 上游吸收补充

- 当前项目采用人工选择性吸收上游更新：
  - [上游同步策略](./docs/maintenance/upstream-sync.md)
  - [人工上游吸收清单](./docs/maintenance/manual-upstream-absorption-checklist.md)

- `v1.1.0` 已明确同步到当前版本的上游能力包括：
  - `llm_clients` 抽象层主链路
  - 共享模型目录与轻量校验
  - provider canonical key 规范化
  - `trading_graph.py` 主要 provider 初始化路径收口
  - `fundamentals_analyst.py` 中 qwen fresh llm 重建逻辑
  - 图层参数透传、工厂别名兼容、风控引用修复
  - provider 默认 URL / 环境变量映射统一
  - MongoDB 默认库名、版本隔离命名与迁移脚本增强

#### 关注公众号

1. **关注公众号**: 微信搜索 **"TradingAgents-CN"** 并关注
2. 公众号每天推送项目最新进展和使用教程


- **微信公众号**: TradingAgents-CN（推荐）

  <img src="assets/wexin.png" alt="微信公众号" width="200"/>


## 🆚 中文增强特色

**相比原版新增**: 智能新闻分析 | 多层次新闻过滤 | 新闻质量评估 | 统一新闻工具 | 多LLM提供商集成 | 模型选择持久化 | 快速切换按钮 | | 实时进度显示 | 智能会话管理 | 中文界面 | A股数据 | 国产LLM | Docker部署 | 专业报告导出 | 统一日志管理 | Web配置界面 | 成本优化



## 🚀 本地开发与启动

### 环境要求
- **Python**: 3.10+ (推荐 3.12)
- **Node.js**: 18+ (推荐 Node 20 / 22)
- **数据库**: MongoDB 6.0+、Redis 6.0+

### 一键启动
```powershell
# 运行项目根目录一键启动脚本
.\start_dev.ps1
```

### 分步启动
1. **后端服务 (FastAPI)**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
2. **异步 Worker 进程**:
   ```bash
   python -m app.worker
   ```
3. **前端界面 (Vue 3)**:
   ```bash
   cd frontend
   npm run dev
   ```

---

## ⚠️ 课题与学术声明

**重要声明**: 本系统为学术研究与毕业设计课题演示系统，仅用于量化因子分析及大模型多智能体推理的学术实验与技术交流，不构成任何实质性证券投资咨询或操作建议。
- 📊 因子分析与回测表现基于历史公开数据，不代表未来走势
- 🤖 大模型研判结果存在偶发性与不确定性，决策需谨慎
- 💰 市场有风险，投资需谨慎
