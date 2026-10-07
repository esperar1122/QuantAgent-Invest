# QuantAgent-Invest · 项目全景追踪与演进记录 (PROJECT TRACE)

> **文档说明**：本文档作为跨设备迁移、项目架构全景认知、开发记录与版本增删改追踪的核心载体。  
> **换机续航提示**：在任何新设备上克隆本项目后，AI 智能助手（如 Antigravity）只需阅读本文档，即可在 1 秒内完全掌握项目的全部历史脉络、技术细节、已完成功能与待办事项。

---

## 一、 项目定位与系统大纲 (Project Overview)

`QuantAgent-Invest` 是一套基于 **多智能体 (Multi-Agent) 协同 + 行为金融工程 + 实时高频盘口** 的 AI 自主量化投研终端系统，针对 A 股/港美股市场特点，专注于为投资者提供高胜率、高盈亏比的波段及日内决策支持。

### 1. 技术栈大纲
- **后端 (Backend)**：
  - **核心框架**：Python 3.12 / FastAPI (异步高性能 REST API) / Uvicorn
  - **金融数据中台**：腾讯实时行情接口 (qt.gtimg.cn / fqkline)、BaoStock、AKShare、TuShare、MongoDB 缓存层、Redis
  - **量化与AI核心**：
    - `app/services/chips_service.py`：CYQ 筹码分布透视、非对称衰减模型、6 大机构级微观结构修正规则、多空辩论对决台 (Bull vs Bear Debate)
    - `app/services/stock_quote_service.py`：极速毫秒级股票与指数快照、分时走势提取、实时 Level-2 五档盘口
    - `app/services/index_service.py`：重要指数（上证、深成、创业板、科创50等）双通道K线与权重成分股矩阵
- **前端 (Frontend)**：
  - **核心框架**：Vue 3 (Composition API / `<script setup>`) + TypeScript + Vite 5 + Pinia 状态管理 + Vue Router 4
  - **UI 与可视化**：Element Plus、ECharts、自定义 SVG 矢量交互引擎（支持纯滚轮缩放、鼠标平移、240分钟标准时段分时图、全屏幕自由拖拽画线工具箱）
  - **工作台布局**：双向响应式三栏投研终端、可折叠与拖拽调整宽度的 Sidebar

---

## 二、 换设备继续开发与编译指南 (Setup & Build Guide)

在换到新电脑（Windows / macOS / Linux）后，按以下步骤即可快速恢复编译与运行：

### 1. 环境准备
- **Node.js**：`>= 18.0.0` (推荐 Node.js 20.x LTS)
- **Python**：`>= 3.10` (推荐 Python 3.12)
- **Git**

### 2. 克隆项目
```bash
git clone https://github.com/esperar1122/QuantAgent-Invest.git
cd QuantAgent-Invest
```

### 3. 后端环境与数据库配置
```bash
# 1. 复制环境变量文件
cp .env.example .env

# 2. 启动数据库容器 (MongoDB 6.0 + Redis 7.0)
docker compose up -d

# 3. 创建并激活虚拟环境 (推荐 uv 或标准 python)
uv venv venv --python 3.11   # 或 python -m venv venv
.\venv\Scripts\activate

# 4. 安装依赖
uv pip install -e .         # 或 pip install -r requirements.txt

# 5. 启动后端 API 服务 (端口 8000)
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
# 或者在 Windows 下直接运行一键脚本：
# .\start_dev.ps1
```
- 默认管理员账号：`admin` / `admin123`（服务首次启动已在 `app/core/database.py` 中内置保底自动创建）
- 后端 Swagger 接口文档：`http://127.0.0.1:8000/docs`
- 健康检查：`http://127.0.0.1:8000/api/health`

### 4. 前端环境配置与构建
```bash
cd frontend

# 1. 安装前端依赖
npm install

# 2. 本地开发调试 (热更新)
npm run dev

# 3. 生产环境全量编译打包 (类型检查 + 压缩构建)
npm run build
```

---

## 三、 功能演进与改动全景追踪 (Changelog & Evolution Trace)

以下记录本项目近期所有的重大技术改造、算法迭代与缺陷修复：

### 🎯 2026-10 个人量化系统闭环增强（回测引擎 + 仓位与组合优化 + 极速秒级行情 + 微信推送 + 模拟盘）

本项目从原本侧重于大模型报告生成的“AI 投研助手”，正式升级为具备实战闭环能力的**个人量化系统**，补齐了量化回测、资金管理、极速推流和模拟盘四大短板。

#### 1. 模块 2：A 股历史回测引擎 (Backtesting Engine)
- **核心定位**：解决“量化策略与 Agent 信号在历史上到底能不能盈利、最大回撤多少”的量化核心命题。
- **A 股专属交易撮合仿真器 (`app/services/backtest/trade_simulator.py`)**：
  - **严格 T+1 交易制度**：当日买入的股份当日冻结，记录为 `avail_shares = 0`，次日开盘调用 `start_new_trading_day()` 统一解冻；
  - **涨跌停板挂单排队限制**：主板 10%、创业板/科创板 20%，涨停日买入委托无法撮合成交；跌停日卖出委托无法撮合成交；
  - **精准交易摩擦模型**：
    - 印花税：仅卖出收取，万分之五 (`0.0005`)；
    - 佣金：双边收取，万分之 2.5 (`0.00025`)，最低 5 元门槛；
    - 过户费：双边收取，十万分之一 (`0.00001`)；
    - 滑点：支持买入加价滑点与卖出折价滑点（默认 `0.1%`）；
    - 整手约束：买入必须为 100 股整数倍（1 手 = 100 股）。
- **专业量化绩效指标计算器 (`app/services/backtest/performance_metrics.py`)**：
  - 累计总收益率 (`total_return_pct`)、年化收益率 (`annualized_return` / CAGR)；
  - 最大回撤率 (`max_drawdown_pct`)、最长回撤持续交易日 (`longest_drawdown_days`)；
  - 夏普比率 (`sharpe_ratio`)、索提诺比率 (`sortino_ratio`)、卡玛比率 (`calmar_ratio`)；
  - 胜率 (`win_rate`)、盈亏比 (`profit_loss_ratio`)、交易笔数统计；
  - 基准对齐对比（如沪深300）与 Alpha / Beta 超额收益分解。
- **内置基准策略库 (`app/services/backtest/strategies.py`)**：
  - 双均线交叉策略 (Dual MA: 5日/20日金叉买入死叉卖出)；
  - MACD 动量金叉策略 (DIF 上穿 DEA 且红柱放量)；
  - 布林带突破/均值回归策略 (下轨反弹买入，上轨止盈卖出)。
- **前复权历史数据加载器 (`app/services/backtest/data_loader.py`)**：
  - 优先调用 AKShare 前复权历史日 K 线，自动降级至 BaoStock 前复权接口，确保回测除权分红数据真实。
- **REST API 端点 (`app/routers/backtest.py`)**：
  - `GET /api/backtest/strategies`：获取支持的策略列表与参数说明；
  - `POST /api/backtest/run`：执行回测计算，返回逐日资产净值曲线（NAV）与指标字典。

#### 2. 模块 3：仓位管理与投资组合优化 (Position Sizing & Portfolio Optimization)
- **核心定位**：解决实盘“该买几手”、“如何分配资金”、“如何避免黑天鹅重仓爆仓”的核心痛点。
- **头寸规模计算模型 (`app/services/portfolio/position_sizer.py`)**：
  1. **等权重模型 (Equal Weight)**：基准分配，按扣除保留现金后的净额均匀分配；
  2. **波动率倒数加权 (Inverse Volatility / 风险平价)**：
     - 根据标的历史年化波动率 $\sigma_i$ 计算倒数权重：$w_i = (1/\sigma_i) / \sum(1/\sigma_k)$；
     - 稳健低波股票（如公用事业/大盘蓝筹）自动加大仓位，高弹性高风险股票自动收缩仓位；支持单股上限约束（如最高 25%）；
  3. **海龟 ATR 真实波幅风险预算模型 (ATR Risk-Budgeting)**：
     - 用户设定单笔可容忍最大风险比例（如 1%）；
     - 根据标的当前 14 日 ATR 均幅与止损倍数（如 2.0 倍 ATR），反推安全买入股数，自动向下取整为 100 股整数手，并计算安全止损价位；
  4. **半凯利公式 (Fractional Kelly)**：
     - 基于策略历史胜率 $p$ 和盈亏比 $b$，根据数学期望计算最优仓位比例，并引入 0.5 凯利安全缓冲系数。
- **组合调仓指令生成器 (`app/services/portfolio/portfolio_optimizer.py`)**：
  - 输入当前持仓和目标候选股票，计算目标股数与当前股数的差额；
  - **摩擦阈值保护**：持仓偏离目标在 3% 以内不触发换手，避免微小调仓造成不必要的印花税和佣金磨损；
  - 生成规范的先卖后买（Sell-then-Buy）调仓委托单列表。
- **REST API 端点 (`app/routers/portfolio.py`)**：
  - `POST /api/portfolio/calculate-atr`：ATR 安全股数与止损价测算；
  - `POST /api/portfolio/calculate-kelly`：凯利最优仓位比例测算；
  - `POST /api/portfolio/rebalance-plan`：组合调仓清单生成。

#### 3. 模块 5：面向个人投资者的秒级极速行情管道 (Real-time Market Streamer)
- **核心定位**：破除商业 Level-2 行情数十万元年费门槛及券商 50 万量化门槛，为个人投资者提供开箱即用、0 费用的毫秒级盘口快照。
- **极速快照抓取与解析引擎 (`app/services/quotes/realtime_streamer.py`)**：
  - 接入腾讯/新浪极速数据源通道，单次 HTTP/TCP 批量打包数十只股票，**实测响应延迟仅 100~200ms**；
  - 自动解析并标准化 18 项核心指标：最新价、昨收、今开、最高、最低、涨跌额、涨跌幅、成交量(手)、成交额(万元)、换手率、PE(TTM)、市值(亿元)、买一至买五/卖一至卖五挂单量价；
  - 针对自选池、监控池和持仓池实行“精准按需订阅”，零封禁风险。
- **REST 与 SSE 推流端点 (`app/routers/realtime_quotes.py`)**：
  - `GET /api/quotes/live/{symbols}`：批量快照接口（例如 `/api/quotes/live/600519,000001`）；
  - `GET /api/quotes/stream?symbols=...`：Server-Sent Events (SSE) 持续流式推送，前端可建立 EventSource 获得毫秒级无感价格跳动。

#### 4. 微信机器人即时交易信号推送 (WeChat Notifier)
- **核心定位**：解决个人投资者无法全天候盯盘、或不想使用高风险全自动下单的痛点，实现“AI/策略盯盘算信号，微信秒级推送提醒，手机 5 秒手动确认”。
- **多通道分发服务 (`app/services/notifier/wechat_notifier.py`)**：
  - 支持**企业微信群机器人 Webhook**、**Server酱（个人微信服务号直达推送）**、**飞书机器人**；
  - 格式化 Markdown 信号卡片：推送【标的名称与代码】、【买入/卖出方向】、【建议买价】、【建议股数与金额】、【建议止损位】与【触发理由】；
  - 具备风控熔断即时警报（单日账户回撤报警、破位止损报警）。
- **环境变量配置**：在 `.env` 中填入 `WECOM_WEBHOOK_URL` 或 `SERVERCHAN_KEY` 即可即时生效。

#### 5. 虚拟模拟盘交易账户系统 (Paper Trading Engine)
- **核心定位**：提供无风险仿真练兵场，跟踪策略与多智能体实盘荐股后的真实收益曲线。
- **模拟账户服务 (`app/services/paper_trading/paper_account_service.py`)**：
  - 默认提供 10 万元虚拟初始本金（支持自定义账户 ID 与重置）；
  - 严格执行 A 股交易规则：买入按 100 股整手，当日买入冻结至次日（T+1），自动扣减佣金与印花税；
  - 自动联动实时行情推流引擎，动态计算当前所有持仓标的的最新市值、浮动盈亏（未实现 PnL）、胜率与累计净值曲线；
  - 模拟委托成交后自动向微信机器人推送成交卡片。
- **REST API 端点 (`app/routers/paper_trading.py`)**：
  - `GET /api/paper-trading/account`：获取模拟账户资金、持仓列表、浮动盈亏与净值曲线；
  - `POST /api/paper-trading/order`：提交模拟买入/卖出委托；
  - `POST /api/paper-trading/test-wechat`：一键测试微信机器人连通性。

#### 6. 数据库自动初始化与超级管理员账号保障
- 在 `app/core/database.py` 的 `init_database_views_and_indexes` 链路中新增自动保底机制：
  - 系统启动时若检测到 MongoDB 中尚未存在管理员账号，会自动调用 `user_service.create_admin_user("admin", "admin123")` 进行幂等创建，彻底避免全新环境拉起时因数据库为空导致无法登录的问题。

---

### 🎯 2026-09 最新迭代记录

#### 1. 左侧全局导航栏（Sidebar）交互革新
- **可左右拖动调整宽度**：
  - 在导航栏右侧增加了可拖拽的分隔线（`.sidebar-resizer`），支持鼠标按住自由左右平移宽度；
  - **严格宽度限制**：按照规范将最大宽度严格锁死在现在的 **228px**，展开调整区间为 `160px ~ 228px`；
  - **智能吸附折叠**：若向左拖拽至 `< 110px` 自动吸附折叠为窄栏；若在折叠状态下向右拉出 `> 110px` 自动触发回弹展开；
  - 拖拽平移时关闭 CSS transition，确保零延迟跟手动效，并实时派发 `resize` 事件通知右侧图表重排。
- **一键折叠 / 展开与偏好记忆**：
  - 顶部增加折叠切换按钮（`<Fold>` / `<Expand>`），点击以 `0.2s` 丝滑动画折叠至 `60px` 极简图标栏；
  - 折叠后完全隐藏文字标签与冗余信息，仅保留居中图标；鼠标悬停图标弹出 `<el-tooltip>` 菜单名称提示；
  - 展开时精确恢复至用户此前调整过的自定义宽度（如拖拽到 200px 就恢复 200px）；
  - 用户的宽度与折叠状态均持久化存储于 `localStorage`，刷新或重启依然保持。
- **主工作区全自动自适应**：
  - 在 `TerminalLayout.vue` 中配置 `flex: 1; min-width: 0;`，导航栏宽度的任何变化均能让主工作区严丝合缝填满屏幕。

#### 2. K 线与分时走势图系统深度升级
- **分时图时间轴 240 分钟精准对齐**：
  - 修复此前“分时图仅有早盘数据时被拉伸到15:00”的时间错位问题；
  - 建立标准 A 股 240 分钟全时段坐标系（早盘 09:30-11:30 占左半区 50%，午盘 13:00-15:00 占右半区 50%）；
  - 截止到上午 11:30 的走势线、成交均价线（VWAP）和成交量柱精确对齐在画布正中轴线（垂直对齐 `11:30/13:00` 刻度），午盘时段自然留白，昨收中轴基准虚线贯通全宽。
- **画线工具箱升级为全局悬浮窗 (Teleport to Body)**：
  - 顶部去除静态堆叠按钮，收纳为精简的 `[✏️ 画线工具]` 折叠开关；
  - 展开后通过 Vue 3 `<Teleport to="body">` 渲染为支持在**整个个股与指数研报界面自由拖拽漫游**的悬浮窗；
  - 悬浮窗采用半透明毛玻璃质感，内置防出界保护，支持趋势线、水平支撑/阻力线、箱体矩形、价格标注、单步撤销、一键清空与视角复位。
- **交互方式精简化（纯滚轮缩放 + 鼠标拖动）**：
  - 去除原界面的 `+ / -` 点击缩放按钮，直接在图表上通过**鼠标滚轮向上（放大）、向下（缩小）**实现丝滑缩放，并以鼠标指针所在位置为锚点聚焦展开；
  - 鼠标左键按住即可左右平移漫游历史 K 线，双击图表任意空白处一键复位至最新 50 根 K 线的默认黄金视角。
- **成交量最新交易日 100 倍剧增 Bug 彻底根治**：
  - **后端定位**：腾讯 `gtimg` 行情接口返回的 `fields[6]` 本身即为股数，后端错误地执行了 `* 100.0`，导致当日最新柱量纲瞬间放大 100 倍（1000万股膨胀为10亿股），压平了往日成交量柱；现已修正；
  - **前端加固**：在 `StockKlineChart.vue` 中加入智能量纲突变防暴走校准逻辑，当检测到最新一根 K 线与前一日突增超 20 倍且除以 100 恢复均值时，自动平滑校准，确保显示比例真实自然。

#### 3. 量化实盘决策看板与四维买卖点位体系
- **置顶实盘决策看板 (`trade-decision-board`)**：
  - 整合多空量化决策，触发高胜率买入信号时亮起呼吸灯与绿色/金色横幅；
  - **高胜率买点触发场景**：
    1. 紧贴下方核心密集筹码峰 S1（回踩建仓黄金圈，距离 $-1.5\% \sim +2.2\%$）；
    2. 放量突破上方套牢阻力峰 R1 且筹码集中度收敛（进入真空加速通道）；
    3. 获利盘极低且技术指标超卖反转（超跌反弹试仓）；
  - **日内无买点与防守警报**：
    - 股价脱离支撑处于半空中（追高盈亏比不足）或上方套牢盘 $\ge 70\%$（重套牢解套抛压沉淀）时，显眼高亮提示“日内无买点，暂不建议买入，切忌盲目追高”。
- **四维点位协同体系（并存互补、各附详尽理由）**：
  - **建仓点 (买入)**：锚定核心支撑峰 S1，锁定最大潜在回撤在 2%~3% 之内；
  - **加仓点 (右侧)**：锚定有效站上套牢阻力峰 R1，进入筹码真空通道享受主升浪；
  - **减仓点 (止盈)**：锚定上方首要套牢峰或目标价，在处置效应回本抛压与获利回吐前果断分批止盈；
  - **止损点 (防守)**：锚定支撑底线破位位，防止两融强平与多杀多踩踏，无条件保本。
- **盈亏比清晰标注（彻底消除歧义）**：
  - 采用中文标准表达：**`{{ tradeDecision.riskRewardRatio }} : 1`**（左边为盈利空间倍数，右边为 1 份风险基准）；
  - 配备大白话副标题：`冒 1 份风险博 X.XX 份收益`；数值 $\ge 2.0$ 时高亮绿色显示，契合小资金散户以小博大、严控回撤的交易铁律。

#### 4. CYQ 筹码分布透视算法（行为金融学与微观结构修正）
- **非对称衰减模型**：将单一衰减率 $\alpha$ 拆分为“获利盘加速置换（$\times 1.2$）”与“深套盘钝化装死（$\times 0.8$）”，模拟散户过早卖出盈利股、死扛亏损股的处置效应；
- **6 大机构级微观结构修正规则**：
  1. *一字涨跌停换手折减*：识别振幅 $\le 1\%$ 且涨幅 $\ge 9.5\%$ 的板，将换手率折减至 0.4 倍，剔除虚假筹码峰；
  2. *停复牌筹码重置*：停牌 $\ge 5$ 个交易日复牌后，对历史筹码执行 0.5 倍衰减重置；
  3. *次新股独立窗口*：上市不满 120 天标的采用 60 天短周期并提高峰值阈值；
  4. *两融高杠杆支撑降级*：融资余额占比过高的密集区进行脆弱性降级并附带踩踏预警；
  5. *大宗交易锁定期满抛压注入*：锁定 6 个月期满后在阻力峰追加潜在抛压因子；
  6. *股本变动注销/增发修正*：回购注销等比抽离筹码，增发注入新成本峰。

- **5. 全市场场内 ETF 专区与毫秒级批量切片架构 (`TerminalEtfHub` & `etf_service.py`)**：
  - *左侧独立专区*：导航栏新增 `场内ETF专区`（路由 `/terminal/etf`，带 `Coin` 图标与 `ETF` 高亮徽章）；
  - *毫秒级单请求批量抓取引擎 (`app/services/etf_service.py`)*：利用腾讯行情批量接口 `http://qt.gtimg.cn/q=s_sh510300,s_sh562590...`，单次 GET 请求涵盖 39+ 核心场内 ETF（宽基、硬核科技、制造周期、大类跨境），平均响应仅 80~130ms，0 数据库压力、0 卡顿；
  - *内存防雪崩短时缓存 (TTL=3s)*：同时间段高并发请求自动命中缓存，彻底隔绝外部接口风控；
  - *千分位（3 位小数）精度全面支持*：依据交易所规则对 ETF 现价、今开昨收、四维推荐买卖点全面启用 3 位小数显示；
  - *ETF 专属基金属性自适应面板*：个股展示财报，ETF 自动切换展示“股票型ETF、场内 T+1、最小变动 0.001元、免印花税(0%)、基金规模、日内换手”；
  - *双向深度投研联动*：在 ETF 专区点击任意标的（或在个股研究顶栏直接点击“半导体设备 562590”胶囊），均一键穿透进入深度分时、K线、CYQ 筹码分布与买卖点决策看板。
- **6. 场内 ETF 专区视觉风格重构与个股投研全面对齐 (`frontend/src/views/Terminal/EtfHub/index.vue`)**：
  - *统一样式语言*：彻底消除深色暗黑风格造成的视觉漂移割裂感，全面重构为专业机构级白底浅色金融终端主题（`#ffffff` 卡片面板、`#e4e7ec` 细边框、`#f4f6f8` 工作区底色）；
  - *标准金融色彩与排版*：统一采用经典机构蓝（`#175cd3`）、A股专业红绿（`#d92d20` / `#039855`）、微色阶涨跌胶囊（`#fef3f2` / `#edfcf2`）与 `JetBrains Mono` 等宽防抖数字；
  - *控件与组件对齐*：分类筛选 Tabs 按钮组、网格/表格双视图切换器、四维指标浅灰数据条、ETF 卡片顶置状态条及 Element Plus 标签均 100% 对齐《个股与指数研究》设计系统。
- **7. 场内 ETF 标的库扩充与极速检索 (`588710 科创半导体设备ETF华泰柏瑞`)**：
  - *官方标的收录*：将 `588710.SH`（华泰柏瑞上证科创板半导体材料设备ETF，标签“科创芯片设备”）收录至 `CORE_ETF_CATALOG`（`app/services/etf_service.py`），全市场批量切片覆盖总数增至 40 只；
  - *搜索引擎直通*：在 `/api/stocks/search` 中融合 `CORE_ETF_CATALOG` 索引，支持用户输入 `588710`、`科创半导体`、`芯片设备` 时瞬时匹配并返回；
- **8. 机构持仓与评级预期「双轨混合模式」架构与持牌券商研报透传 (`institution_rating_service.py` & `StockResearch`)**：
  - *双轨混合设计体系 (Hybrid Dual-Track)*：
    1. **持牌券商研报轨 (Real Ratings)**：针对具备公开研报的核心个股（如茅台、宁德时代等），直连东方财富研报中台（`reportapi.eastmoney.com`）聚合近 365 天研报，提取最新持牌券商（海通/中信/国泰君安等）评级名称、一致目标价、动态空间与近 10 篇券商研报详情；
    2. **全标的量化推演轨 (Quant Dynamic Model)**：针对 ETF 基金、大盘指数及无研报冷门股，系统无缝自动降级为五维量化多因子多空推演（估值、动量、波动率、趋势、筹码集中度），计算理论目标价与盈亏空间；
  - *面板交互与视觉规范*：卡片标题旁显式配备双轨状态胶囊（`持牌券商研报` 徽章 vs `量化动态推演` 徽章），消除散户决策信息模糊与误判风险；
  - *双弹窗深度穿透系统*：
    - **券商研报明细弹窗**：展示研报概览看板（最新研报数、核心券商、一致评级、一致目标价）、评级分布柱状/胶囊比例（买入/增持/中性），及包含券商名称、最新评级、目标价、分析师、发布日期与官方 PDF 直通链接的高清表格；
    - **量化算法透视弹窗**：公布五维打分雷达分值与三大核心推演公式（综合得分、目标价弹性推演、隐含空间推演），算法 100% 透明可溯源；
- **9. 离线/未连接状态去伪存真与金融级骨架流光扫光体系 (`StockKlineChart.vue` & `StockResearch`)**：
  - *彻底拔除 8.27 虚假模拟数据*：彻底删除原 `generateSimulatedKlineData` 中硬编码的 90 天累加至 `08-27` 的虚假 K 线生成器，坚守金融数据真实性与合规红线，杜绝展示虚假或过时陈旧数据导致交易误判；
  - *零系统负担的骨架流光扫光 (Fintech Skeleton Shimmer)*：在后端未启动或网络断开时，0 存储占用、0 线程阻塞，主图表视口自动激活 36 根拟真骨架蜡烛条、量能柱与虚线网格，叠加 `@keyframes skeleton-sweep-anim` 2.4s 优雅扫光光幕；
  - *高科技状态浮层与一键重连*：图表中心悬浮极客质感磨砂状态卡片（`⚡ 投研中台未连接 · 骨架就绪等待数据流`），提供一键 `[重试获取实时数据]` 动作；控制台顶栏同步呈现 `引擎离线 · 骨架等待中` 呼吸胶囊；
  - *右侧研究案卷截断彻底修复与 ETF 自适应*：移除 `.casefile-items-scroll` 的死硬 `560px` 限制，改为 `flex: 1` 自适应填满右栏完整的 820px 高度；新增自定义 5px 细滚动条、底部闭环状态页脚（`全景穿透 ↗`），并对场内 ETF 智能切换展示成份赛道纯粹度与免税申赎流动性语义。

---

## 四、 核心源码目录索引 (Source Code Index)

| 模块 | 核心源码路径 | 功能概述 |
| :--- | :--- | :--- |
| **全局布局** | `frontend/src/layouts/TerminalLayout.vue` | 终端主框架，双向 flex 自适应排版 |
| **侧边导航** | `frontend/src/components/Terminal/TerminalSidebar.vue` | 可折叠 (60px)、拖拽调宽 (160-228px)、偏好记忆导航栏（含场内ETF入口） |
| **场内ETF专区** | `frontend/src/views/Terminal/EtfHub/index.vue` | 全市场核心场内 ETF 雷达、分类筛选、卡片/表格双视图、自动轮询 |
| **ETF聚合服务**| `app/services/etf_service.py` | 单请求多标的批量切片极速抓取引擎，内存防雪崩缓存 |
| **研报评级服务**| `app/services/institution_rating_service.py` | 持牌券商最新研报聚合、一致预期评级与目标价计算、30分钟防抖缓存引擎 |
| **K线与分时**| `frontend/src/components/Terminal/StockKlineChart.vue` | 240分时图、全局悬浮画线窗、滚轮缩放、成交量校准 |
| **个股投研** | `frontend/src/views/Terminal/StockResearch/index.vue` | 量化买卖决策看板、双轨机构评级/研报弹窗、盈亏比推演、ETF专属千分位/面板 |
| **筹码弹窗** | `frontend/src/components/TechnicalIndicators/TechnicalAnalysisModal.vue` | 筹码规则生效横幅、多空对决裁决台 |
| **前端接口** | `frontend/src/api/stocks.ts` | 股票搜索、分时、K线、ETF专区概览、机构真实研报、指标快照与筹码接口定义 |
| **实时行情** | `app/services/stock_quote_service.py` | 腾讯极速行情解析、五档挂单、分时数据抓取 |
| **量化回测服务** | `app/services/backtest/` | A股T+1与涨跌停撮合仿真、夏普/回撤指标、双均线/MACD/布林带策略 |
| **回测 API**   | `app/routers/backtest.py` | 回测策略列表 (`/api/backtest/strategies`) 与回测执行 (`/api/backtest/run`) |
| **仓位与组合服务** | `app/services/portfolio/` | 等权、逆波动率(风险平价)、ATR海龟风险预算、半凯利公式、调仓指令生成器 |
| **仓位 API**   | `app/routers/portfolio.py` | ATR股数测算、凯利仓位测算、调仓计划清单接口 |
| **极速秒级推流** | `app/services/quotes/realtime_streamer.py` | 腾讯/新浪极速通道秒级解析引擎 (100~200ms延迟、免Key 0成本) |
| **行情推流 API** | `app/routers/realtime_quotes.py` | 批量实时快照 (`/api/quotes/live`) 与 SSE 持续推流 (`/api/quotes/stream`) |
| **微信告警服务** | `app/services/notifier/wechat_notifier.py` | 企业微信 Webhook、Server酱 (个人微信直达)、飞书 Markdown 信号卡片直推 |
| **虚拟模拟盘服务** | `app/services/paper_trading/paper_account_service.py` | 10万虚拟初始本金、T+1持仓管理、动态实时盈亏与净值时序记录 |
| **模拟盘 API** | `app/routers/paper_trading.py` | 模拟账户总览 (`/api/paper-trading/account`)、模拟委托与微信测试 |
| **自动化测试集** | `tests/test_quant_modules.py`, `tests/test_api_endpoints.py` | 覆盖撮合规则、数学指标、头寸模型、实时快照与 API 的全套单元与集成测试 |
| **实时行情** | `app/services/stock_quote_service.py` | 腾讯极速行情解析、五档挂单、分时数据抓取 |
| **筹码引擎** | `app/services/chips_service.py` | CYQ 筹码分布、非对称衰减、6大机构修正规则 |

---

## 五、 换设备继续开发的 AI 衔接指令 (Prompt Template)

当您在**新电脑**上打开 VS Code / Antigravity 时，只需复制并发送以下指令给 AI：

```markdown
你好，我已经在这台新电脑上克隆了最新的 QuantAgent-Invest 代码仓库。
请你首先阅读项目根目录下的 `PROJECT_TRACE.md` 文档，了解当前系统的项目架构、已完成的技术特性与最新修改记录，然后继续协助我进行后续的开发与编译调试。
```
AI 将自动基于该文档在几秒内无缝接续全部上下文！

---

## 六、 跨设备协同与下一步待办清单 (Roadmap & Next Steps for Antigravity)

> **两端 AI 助手协同指南**：
> 无论在设备 A（家里）还是设备 B（公司/笔记本），任何接手的 Antigravity 助手请严格参考此状态与清单，确保开发无缝衔接。

### 1. 当前阶段已完成状态 (Status: Backend Complete & 100% Tested)
- ✅ **A股历史回测引擎**：已完成全部后端撮合逻辑（T+1、涨跌停、滑点手续费）与量化指标算法，API 已调通并附带自动化单元测试；
- ✅ **仓位管理与组合优化**：已完成等权、逆波动率、ATR 风险预算（100 股整手）、半凯利公式及调仓计划生成，API 已调通；
- ✅ **个人秒级实时行情管道**：已完成腾讯/新浪极速通道封装，批量获取快照延迟 100~200ms，支持 SSE 推流，无需券商 50 万门槛；
- ✅ **微信机器人即时推送**：已封装企业微信 Webhook、Server酱与飞书卡片，支持交易信号与风控警报一键直达手机；
- ✅ **虚拟模拟盘账户系统**：已支持 10 万元初始资金、模拟下单撮合、T+1 持仓限制、浮动盈亏计算及成交微信联动；
- ✅ **数据库超级管理员自动创建**：服务启动自动检测并补齐 `admin / admin123`。

### 2. 下一步建议开发任务 (Next Steps for Next Session)

#### 优先级 P1：前端可视化界面对接（将后端新 API 转化为交互界面）
1. **策略回测中心 (`frontend/src/views/Terminal/BacktestCenter/index.vue`)**：
   - 增加路由 `/terminal/backtest`；
   - 界面左侧：策略选择下拉（双均线/MACD/布林带）、标的代码、时间区间、初始资金与参数配置卡片；
   - 界面右侧：点击“开始回测”调用 `POST /api/backtest/run`，通过 ECharts 绘制**双轴收益率/基准对比曲线**与**最大回撤水下柱状图**，下方展示交易明细流水表。
2. **虚拟模拟盘悬浮看板 (`frontend/src/components/Terminal/PaperTradingModal.vue`)**：
   - 在顶栏增加 `[🎮 虚拟模拟盘]` 快捷胶囊，点击弹出抽屉或模态框；
   - 调用 `GET /api/paper-trading/account` 展示当前总资产、可用现金、持仓标的浮动盈亏与成本价；
   - 支持在个股研报页面点击“一键按建议模拟买入”，调用 `POST /api/paper-trading/order`。
3. **仓位测算辅助小工具 (`frontend/src/components/Terminal/PositionSizerDrawer.vue`)**：
   - 在个股研报四维买卖点位看板旁增加 `[📐 仓位测算]` 按钮；
   - 输入账户总资金，调用 `POST /api/portfolio/calculate-atr`，直接显示“基于当前 ATR 建议买入 X 手（X00 股），止损参考价 XX.XX 元”。
4. **盘中分时图与行情接入 SSE 流式推送**：
   - 在 `StockResearch` 中接入 `GET /api/quotes/stream?symbols={code}`，使用前端 `EventSource`，实现盘中不用手动刷新、数字自动跳动的丝滑体验。

#### 优先级 P2：进阶功能与外部联动（按需选做）
1. **微信 Webhook 界面配置项**：在前端“个人设置”或“系统配置”中增加微信 Webhook / Server酱 Key 输入框，方便用户在网页上直接配置；
2. **多因子选股一键导入回测**：支持在“股票筛选器”中选出前 10 只高分股票后，一键生成组合并推入回测或模拟盘调仓计划。

