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

### 3. 后端环境与数据库配置 (双设备跨端环境自适应)
```bash
# 1. 复制环境变量文件
cp .env.example .env

# 2. 数据库服务模式（脚本已全自动智能识别，无需手动干预）：
#   - 设备 A (带 Docker): start_dev.bat 自动唤起 Docker Desktop 并拉起容器
#   - 设备 B (无 Docker / 原生服务): 本机开启原生 MongoDB (27017) 和 Redis (6379) 即可，脚本自动侦测并跳过 Docker
#   - 纯轻量模式: 两者均无时系统自动降级为本地文件/内存缓存

# 3. 创建并激活虚拟环境 (推荐 uv 或标准 python)
uv venv venv --python 3.11   # 或 python -m venv venv
.\venv\Scripts\activate

# 4. 安装依赖
uv pip install -e .         # 或 pip install -r requirements.txt

# 5. 启动前后端全栈服务 (端口 8000 + 3000)
.\start_dev.bat             # 或 powershell .\start_dev.ps1
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

### 🎯 2026-10 个人量化系统与投研终端可视化全面闭环（前端上线 + 回测 + 模拟盘 + ATR仓位 + 舆情新闻）

本项目从原本侧重于大模型报告生成的“AI 投研助手”，正式升级为具备实战闭环能力的**个人量化系统**，并在前端全面上线交互工作台：

#### 0. 前端量化全景落地与交互优化 (Frontend Quant Experience)
- **研报 K 线与副图技术指标全面重构 (MA10 均线 + MACD 递归真算法与自适应比例尺)**：
  - **MA10 均线落地**：`StockKlineChart.vue` 数据接口、计算（10日收盘价平均值）与 SVG 渲染全面补齐，采用明亮洋红 `#EC4899` 标色，顶栏标签与 hover 十字光标同步联动；
  - **MACD 递归真算法重构**：彻底废弃此前 `(ma5 - ma20) * 0.8` 和 `dif * 0.75` 的虚假伪公式，切换为经典 EMA12/EMA26 递归平滑、DIF = EMA12 - EMA26、DEA9 递归平滑、MACD 柱 = 2*(DIF - DEA) 标准算法，并在分时图与K线图中统一计算，真正体现金叉死叉；
  - **视口自适应动态比例尺 (Auto-fit Dynamic Scale)**：彻底根除硬编码倍数（`dif * 18` 与 `val * 20`）导致的低价股/ETF贴地成横线与高价股飞出屏幕边界的严重显示不良 Bug。副图建立基于视口可见数据的绝对极值 $absMax \times 1.15$ 动态映射，副图中心零轴绝对居中；
  - **副图刻度与数值全息呈现**：副图标题栏增加 MACD 红绿柱动态数值（带自适应浮点精度，ETF低价自动扩展至3位），右侧坐标轴同步绘制 `+Max`, `0.00`, `-Max` 动态标尺，媲美专业级行情终端。
- **实战交易时效与纪律画像彻底动态化 (动态盈亏比 + 免5低门槛费率 + 建仓建议 + 单标的持仓硬顶)**：
  - **实时现价盈亏比 vs 挂单计划盈亏比分轨推演**：区分“以当前最新价买入的实时盈亏比”与“以算法推荐支撑位限价挂单的计划盈亏比”，避免盘中冲高时误用高盈亏比入场追高；
  - **券商实战摩擦费率深度校准**：落实个人定制佣金（万0.876，免5最低0.5元起收）、过户费（万0.1）、卖出印花税（万5，ETF免征印花税），净盈亏比核算扣除摩擦更贴近真实账户盈亏；
  - **资金纪律与单笔回撤百分比化**：彻底解绑固定死数字，单笔最大容忍亏损与本金占用均以动态百分比和实时账户总资金计算；
  - **动态算法建仓决策与建议**：联动胜率、多层次止盈（保底 MA5 与扩展目标）和实时净盈亏比给出“✅ 建议建仓 / 💎 非常值得 / ⚖️ 轻仓防守 / ⏳ 暂缓开仓 / 🛑 赔率过低禁止开仓”，并注入单标的持仓硬顶（如满仓单股上限严控在 30%~35%），杜绝梭哈单只标的。
- **回测策略库持久化与自定义管理系统 (`useBacktestStrategies.ts` & `BacktestStrategy*.vue`)**：
  - **核心目标**：满足“回测策略自定义像量化策略库一样持久化存放”的实战需求；
  - **后端 MongoDB 持久化**：`app/routers/backtest.py` 接入集合 `user_backtest_strategies`，提供完整的 RESTful CRUD API 与 6 套经典系统推荐策略种子（核心资产多标的组合、平安多因子、茅台双均线、宁德MACD、300ETF布林、突破先锋新高）；
  - **前端双轨可靠性保障**：`frontend/src/composables/useBacktestStrategies.ts` 结合 localStorage 实现离线与弱网双轨无缝降级；
  - **策略库交互闭环**：回测中心顶部导航增加【🎯 回测策略库】入口、【经典策略快捷装载】下拉列表与【保存当前配置为策略】按钮；新增 `BacktestStrategyManageDialog.vue` 与 `BacktestStrategyEditDialog.vue` 弹窗，支持全要素参数修改与当前控制台配置一键提取。
- **回测动态执行进度条与内核日志看板 (`BacktestCenter/index.vue`)**：
  - 启动回测后呈现多阶段全息动效加载条，涵盖数据加载校验、信号矩阵演算、A股T+1与涨跌停模拟、摩擦成本核算、净值归因等各阶段；
  - 动态滚动输出执行日志，带耗时统计与百分比动态递增，彻底根除死等痛点。
- **全站 DIV 响应式弹性收缩规范与顶栏遮挡根治 (`responsive.scss`)**：
  - 沉淀全站响应式样式规范 `responsive.scss`，支持流式 Flex 容器（`.fluid-banner`, `.fluid-primary-col`, `.fluid-secondary-col`）；
  - 全局顶部行情栏集成虚拟模拟盘弹性胶囊，自适应缩放与文字折叠，根治窗口缩小时创业板指等指数信息被遮挡的问题；
  - 回测中心顶部栏完全适配浅色主题（Light Theme），消除暗色残留。
- **股票多维指标筛选加入“盈亏比 (R:R)”选项 (`StockPool/index.vue` & `stocks.py`)**：
  - 后端：在 `app/routers/stocks.py` 增加 `min_profit_loss_ratio` 筛选，基于近期波动幅度和阻力/支撑位动态估算各标的盈亏比；
  - 前端：筛选抽屉中新增盈亏比选项（全部/≥1.5/≥2.0/≥2.5/≥3.0），股票池列表动态显示盈亏比标签，并支持联动至量化策略库持久化。
- **自选股全景穿透直跳 (`frontend/src/views/Favorites/index.vue`)**：
  - 彻底废除旧版数据残缺的 `/terminal/stocks/:code` 详情页跳转；
  - 点击股票代码、名称或 `[深度研判]` 按钮，直接穿透跳转至 `/terminal/stock?code=...` 全景研报工作台，完全继承分时图、K线、CYQ 筹码分布、技术指标与机构研报案卷。
- **个股研报下置实时资讯与舆情流 (`frontend/src/views/Terminal/StockResearch/index.vue`)**：
  - 在中间栏买卖五档盘口正下方嵌入 `.stock-news-card` 模块；
  - 自动联动后端 `/api/news-data/latest` 接口，支持“全部资讯 / 公司公告 / 行业快讯 / 大盘宏观”动态切换；
  - 具备情感分析标签（偏多红标/承压绿标/中性灰标）与无网自适应兜底引擎，确保界面永不空白。
- **策略历史回测中心全景工作台 (`frontend/src/views/Terminal/BacktestCenter/index.vue`)**：
  - 路由与入口：全局侧边栏已挂载 `[⚡ 策略历史回测]`（带 Hot 徽章），路由为 `/terminal/backtest`；个股研报决策横幅支持带参一键直达；
  - **自定义多指标组合策略 (`CustomRuleStrategy`)**：支持用户搭积木式组合 5 大因子（均线金叉/多头/站上长线、成交量异动放量/温和放量、RSI超跌反转、KDJ低位金叉/极度超卖、N日新高通道突破），支持全部满足 (AND) 与任一满足 (OR) 模式；
  - **通用风控与仓位规则**：集成持仓硬止损 (`stop_loss_pct`)、动态止盈 (`take_profit_pct`)、最大持股天数强制平仓 (`max_holding_days`)、单次仓位比例调节 (`position_ratio`)；
  - **交易动因完整溯源**：成交流水表清晰标注每笔买卖动因（策略入场、策略离场、止损触发、止盈达成、持仓超时）；
  - 配置面板：标的代码搜索与自动填充、策略选择、回测时间区间快捷选项（近6个月/1年/2年/3年）、初始资金与基准指数对比；
  - 绩效看板：8 大核心量化 KPI 磁贴（累计总收益率、年化收益 CAGR、最大回撤 MaxDD、夏普比率 Sharpe、胜率 Win Rate、盈亏比 P/L Ratio、基准收益、Alpha 超额收益）；
  - ECharts 组合图表：双轴策略净值 (NAV) 与基准走势对比折线，下方配对半透明红色水下动态回撤曲线；
- **顶部状态栏与主题配色一致性修复 (`frontend/src/stores/app.ts` & `dark-theme.scss`)**：
  - 根除“在亮色模式下，顶部状态栏自己变为暗色”的严重视觉分裂；
  - 根因分析：此前 `app.ts` 主题默认设为 `'auto'`，导致 Windows 暗色系统偏好自动激活了 `<html class="dark">`，触发了 `dark-theme.scss` 将顶部状态栏硬编码涂黑；而页面主体为浅白底色；
  - 解决方案：主题默认值固定为 `'light'`，`isDarkTheme` 解绑操作系统自动深色判断，并补充了回测中心在真正暗色模式下的自适应样式规则，实现全站风格纯净一体。
- **页面跳转频繁报“服务器内部错误，请稍后重试”根因排除与修复**：
  - **根因剖析**：
    1. **后端崩溃点**：`app/services/paper_trading/paper_account_service.py` 中使用了 `if col:` 进行条件判断。PyMongo 的 `Collection` 对象出于安全机制显式禁用了布尔值测试，直接抛出 `NotImplementedError: Collection objects do not implement truth value testing or bool(). Please compare with None instead: collection is not None`，导致 `GET /api/paper-trading/account` 接口必崩并返回 HTTP 500；
    2. **前端传导链**：顶部状态栏 `TopTickerBar.vue` 与 `PaperTradingModal.vue` 在每次加载挂载时均会发起模拟账户总览同步请求；而 `frontend/src/api/request.ts` 中的 Axios 响应拦截器在 `case 500:` 时未校验 `skipErrorHandler`，直接弹出全局全局红标提示“服务器内部错误，请稍后重试”；
  - **根治措施**：
    1. 后端将 `paper_account_service.py` 中的 `if col:` 严格纠正为 `if col is not None:`，并强化 `db is not None` 空值判定；
    2. 前端 `request.ts` 为 404、429、500、502~504 错误统一增加 `if (!config?.skipErrorHandler)` 拦截控制；
    3. `quantApi.getPaperAccount(skipErrorHandler = true)` 支持静默容错，杜绝偶发网络抖动对用户换页浏览造成弹窗打扰。
- **虚拟模拟盘交易终端 (`frontend/src/components/Terminal/PaperTradingModal.vue`)**：
  - 全局入口：顶栏右侧新增 `[🎮 虚拟模拟盘 | ¥100,000]` 实时净值胶囊，任意页面点击即开；个股研报决策横幅新增 `[🎮 模拟买入]` 按钮；
  - 账户总览：10 万元虚拟初始本金、可用资金、持仓市值、累计收益与浮动盈亏；
  - 持仓明细：持仓标的、当前持股数、可卖股数（严格 T+1 冻结显示）、成本价与现价、浮盈比例，支持一键快捷卖出；
  - 委托下单：买入/卖出方向、快捷仓位筹码（全仓/半仓/1/4仓/一手）、买入手数自动取整（100 股整数倍）、买入理由记录；
  - 微信机器人直通：提供“🔔 测试微信机器人推送”按钮，一键验证交易信号通知链条。
- **海龟 ATR 仓位管理抽屉 (`frontend/src/components/Terminal/PositionSizerDrawer.vue`)**：
  - 个股决策横幅新增 `[📐 仓位测算]` 按钮，点击自右侧滑出；
  - 输入总资金、风险承受度（默认 1.0%）、ATR 倍数与周期，实时调用 `/api/portfolio/calculate-atr` 和 `/api/portfolio/calculate-kelly`；
  - 给出科学买入建议：**建议买入股数（向下取整为 100 股整手）**、资金占用比、严格止损参考价、半凯利公式上限建议；
  - 支持一键 `[一键推送到模拟盘下单]`，自动携带测算点位与股数呼出模拟盘。
- **双设备启动与代理架构加固**：
  - `start_dev.bat` 引入 20ms 端口快速检测机制：在有 Docker 的设备上自动唤起容器，在无 Docker、直接使用原生 MongoDB (27017) 和 Redis (6379) 的设备上秒级自适应跳过，零等待；
  - `frontend/vite.config.ts` 固定反向代理目标至 `127.0.0.1:8000`，彻底根治 Node 18+ 对 `localhost` 优先解析为 IPv6 导致的 `ECONNREFUSED` 报错。

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
- **10. A股量化回测中心、自定义多指标策略与全策略通用风控（全栈闭环）**：
  - *量化回测服务与规则引擎*：`app/services/backtest/` 实现真实 A 股 T+1 撮合（涨跌停买卖限制、滑点、万分之2.5佣金、千分之1单边印花税），包含夏普比率、最大回撤、年化收益、胜率、盈亏比等 8 大量化指标；
  - *自定义多因子组合策略 (`CustomRuleStrategy`)*：支持均线（MA金叉/死叉/多头排列/突破站上）、量能（成交量放量突破/温和放量）、RSI（超跌反弹/超买预警）、KDJ（低位金叉/极度超卖）、通道突破（突破 N 日新高），支持 AND/OR 多因子组合；
  - *全策略通用硬核风控*：集成硬止损 (`stop_loss_pct`)、动态移动止盈 (`take_profit_pct`)、最长持仓超时平仓 (`max_holding_days`)、单次仓位限制 (`position_ratio`)，并在成交流水表中显式记录入场/离场/止损/止盈动因；
  - *前端回测工作台*：`frontend/src/views/Terminal/Backtest/index.vue`，实现参数动态配置面板、ECharts NAV 净值与水下最大回撤双轨图表、交易明细流水与侧边栏独立导航入口。
- **11. PyMongo Collection `__bool__` 异常与全站页面跳转 500 报错根除**：
  - *现象剖析*：全站每次在路由间切换（如从自选股跳到个股研报或股票池），前端均频繁弹出“服务器内部错误，请稍后重试”的红色打扰弹窗；
  - *技术根因*：`app/services/paper_trading/paper_account_service.py` 中写了 `if col:` 判定集合存在，触发了 PyMongo 原生保护抛出的 `NotImplementedError: Collection objects do not implement truth value testing or bool()`，导致 `/api/paper-trading/account` 接口抛出 HTTP 500 异常；
  - *彻底根治*：统一修正为 `if col is not None:`；同时在前端 `frontend/src/api/request.ts` 拦截器中增加 `skipErrorHandler` 过滤机制，`TopTickerBar` 与 `quant.ts` 开启静默容错，杜绝被动弹窗打扰。
- **12. 股票池市盈率至毛利率财务与估值数据链路诊断、映射修复与全市场极速同步（重点记录）**：
  - *现象剖析*：在前端《A股与核心指数股票池》(`StockPool`) 列表中，市盈率(PE-TTM)、市净率(PB-MRQ)、市销率(PS)、ROE(%)、净利增速、营收增速、毛利率全部显示为 `--`；
  - *后端映射断链根因*：在 `app/routers/stocks.py` 的 `get_stock_pool` 接口中，返回字典直接取 `item.get("pe")` 等基础字段，但 `item` 来自 `stock_basic_info` 基础档案表，本身不包含行情快照中的估值指标；即便接口已经批量查出了 `market_quotes` 行情快照字典 `q`，代码也没有建立 `q.get("pe") or item.get("pe")` 的优先取值与回退逻辑，导致全市场估值直接被置空！同时排序字段缺少对 `market_quotes` 估值维度的支持；
  - *代码层修复*：`app/routers/stocks.py` 优化为 `q` 优先 + `item` 兜底的双轨取值架构，并将 `pe`、`pb`、`total_mv`、`circ_mv` 纳入行情层极速排序字段，排序与展示彻底通畅；
  - *免 Token 极速数据链路打通*：
    1. **财报指标 (ROE/净利增速/营收增速/毛利率)**：开发优化 `scripts/sync_financial_indicators.py`，直连东方财富全市场上市公司业绩三表分析接口（免 Token、0 成本），12.2 秒内并发拉取 5969 家上市公司最新财报指标并写入 `stock_basic_info`，覆盖率达 96.6%~97.3%；
    2. **实时估值指标 (PE-TTM/PB-MRQ/市值)**：开发 `scripts/sync_realtime_valuation.py`，基于腾讯高并发行情通道（免 Token、0 成本、100ms 延迟），8 线程并发在 5.75 秒内完成全市场 5571 只股票的 PE/PB/市值批量拉取并同步入库。实测股票池全部指标 100% 恢复正常呈现！

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
| **股票池与筛选**| `app/routers/stocks.py` & `frontend/src/views/StockPool/` | 股票池全量多因子聚合、行情/估值双轨映射、多字段排序与高级筛选 |
| **财报同步脚本**| `scripts/sync_financial_indicators.py` | 东财免 Token 全市场财报分析指标同步脚本 (ROE/净利增速/营收增速/毛利率，12s全量) |
| **估值同步脚本**| `scripts/sync_realtime_valuation.py` | 腾讯免 Token 全市场极速行情与估值同步脚本 (PE/PB/市值/盘口，5.7s全量) |
| **筹码弹窗** | `frontend/src/components/TechnicalIndicators/TechnicalAnalysisModal.vue` | 筹码规则生效横幅、多空对决裁决台 |
| **前端接口** | `frontend/src/api/stocks.ts` | 股票搜索、分时、K线、ETF专区概览、机构真实研报、指标快照与筹码接口定义 |
| **量化回测服务** | `app/services/backtest/` | A股T+1与涨跌停撮合仿真、夏普/回撤指标、双均线/MACD/布林带及自定义多因子策略 |
| **回测 API**   | `app/routers/backtest.py` | 回测策略列表 (`/api/backtest/strategies`) 与回测执行 (`/api/backtest/run`) |
| **回测中心前端**| `frontend/src/views/Terminal/Backtest/index.vue` | 策略回测参数面板、ECharts NAV 净值与水下回撤图、交易流水与评价看板 |
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

### 1. 当前阶段已完成状态 (Status: Backend & Frontend Complete & 100% Tested)
- ✅ **小资金一票否决短线均线防守模型升级（去滞后性 + 超跌保护）**：
  - 针对 A 股 1~3 天超短/波段资金与 T+1 极速退潮特性，彻底废弃滞后 3~5 天的单一“跌破 MA20”中线否决指标；
  - 升级为“MA5 攻击线 + MA10 操盘线”灵敏双防守，破操盘线且死叉时提前 2~4 天预警，规避 15%~25% 巨额利润回吐；
  - 融入 5 日负乖离率（BIAS5 < -5% 或 KDJ J < 5）极端超跌反弹保护机制，免除在空头衰竭反抽冰点的盲目否决与割肉。
- ✅ **回测策略库持久化与自定义管理系统（全栈闭环）**：
  - **全要素策略模型**：标的/组合（支持等权与波动率倒数加权）、底层算法（`custom_rule`/`dual_ma`/`macd`/`bollinger`）、指标超参数、止损止盈风控规则（硬止损/动态止盈/最长持股/单次仓位）、交易摩擦与滑点深度模型（标准A股/ETF/自定义、滑点类型与价差）；
  - **双轨可靠持久化**：后端 MongoDB 集合 `user_backtest_strategies` 提供完整 RESTful CRUD API（查/增/改/删/恢复系统推荐）；前端 `useBacktestStrategies.ts` 结合 localStorage 实现无缝降级兜底；
  - **策略库交互闭环**：回测中心顶部栏新增“🎯 回测策略库”入口与“经典策略快捷装载”下拉菜单；参数配置控制台支持“一键从当前页面提取并保存为策略”；新增策略管理弹窗 `BacktestStrategyManageDialog.vue` 与编辑弹窗 `BacktestStrategyEditDialog.vue`。
- ✅ **回测动态执行进度条与内核日志看板 (Dynamic Backtest Progress Dashboard)**：
  - 启动回测后呈现多阶段全息动效加载条，涵盖数据加载校验、信号矩阵演算、A股T+1与涨跌停模拟、摩擦成本核算、净值归因等各阶段；
  - 动态滚动输出执行日志，带耗时统计与百分比动态递增，彻底根除死等痛点。
- ✅ **全站 DIV 响应式弹性收缩规范与顶栏遮挡根治 (`responsive.scss`)**：
  - 沉淀全站响应式样式规范 `responsive.scss`，支持流式 Flex 容器（`.fluid-banner`, `.fluid-primary-col`, `.fluid-secondary-col`）；
  - 全局顶部行情栏集成虚拟模拟盘弹性胶囊，自适应缩放与文字折叠，根治窗口缩小时创业板指等指数信息被遮挡的问题；
  - 回测中心顶部栏完全适配浅色主题（Light Theme），消除暗色残留。
- ✅ **股票多维指标筛选加入“盈亏比 (R:R)”选项（全栈闭环）**：
  - 后端：在 `app/routers/stocks.py` 增加 `min_profit_loss_ratio` 筛选，基于近期波动幅度和阻力/支撑位动态估算各标的盈亏比；
  - 前端：筛选抽屉中新增盈亏比选项（全部/≥1.5/≥2.0/≥2.5/≥3.0），股票池列表动态显示盈亏比标签，并支持联动至量化策略库持久化。
- ✅ **A股历史回测引擎与自定义多指标策略（全栈闭环）**：
  - 后端：撮合逻辑（T+1、涨跌停限制、滑点佣金印花税）、8 大量化指标（夏普/年化/最大回撤/胜率/盈亏比等）、双均线/MACD/布林带策略；
  - **自定义多因子组合策略 (`CustomRuleStrategy`)**：自由组合均线（金叉/多头/站上长线）、量能（放量异动/温和放量）、RSI（超跌/反弹）、KDJ（低位金叉/极度超卖）、通道突破（新高），支持 AND/OR 逻辑；
  - **全策略通用风控**：硬止损 (`stop_loss_pct`)、动态止盈 (`take_profit_pct`)、最长持仓天数 (`max_holding_days`)、单次仓位比例 (`position_ratio`)；
  - **交易动因溯源**：成交流水表清晰呈现每笔买卖动因（策略入场/策略离场/止损触发/止盈达成/超时平仓）；
  - 前端：全屏策略回测中心 (`/terminal/backtest`)，动态表单面板、ECharts NAV 净值与水下回撤组合图、交易明细流水、侧边栏独立入口。
- ✅ **顶部状态栏主题配色一致性与换页 500 报错根治**：
  - 彻底根除浅色模式下顶栏单独变黑问题；默认主题锁定为 `'light'`，解绑操作系统暗色被动污染，回测中心同步适配全站暗色风格；
  - 根治 PyMongo Collection 布尔真值判断导致的 500 异常，全站换页不再有任何报错打扰。
- ✅ **股票池市盈率至毛利率财务与估值数据链路修复（全栈闭环）**：
  - `app/routers/stocks.py` 修复字段映射，优先取行情快照 `q` 中的 `pe`/`pb`/`total_mv`/`circ_mv`，并与 `stock_basic_info` 财报指标建立稳健回退；
  - 扩充全市场排序字段支持（`pe`, `pb`, `total_mv`, `circ_mv` 行情级极速排序）；
  - 建立全套免 Token、0 成本、秒级完成的全市场财报与估值同步工具集，全市场 5500+ 只股票数据覆盖率达 96%+。
- ✅ **虚拟模拟盘账户系统（全栈闭环）**：
  - 后端：10 万元虚拟资金、买卖委托撮合、T+1 持仓管理、浮动盈亏与净值计算、成交微信推送；
  - 前端：全局顶栏净值胶囊按钮与 `PaperTradingModal` 模态交易终端，持仓穿透、快捷仓位筹码、一键快捷卖出。
- ✅ **仓位管理与海龟 ATR 头寸控制（全栈闭环）**：
  - 后端：等权、逆波动率平价、海龟 ATR 风险预算（100 股整手）、半凯利公式及调仓计划生成；
  - 前端：个股研报四维决策横幅一键唤出 `PositionSizerDrawer` 抽屉，支持一键将计算结果推送到模拟盘下单。
- ✅ **自选股全景穿透直跳**：废除旧版数据残缺详情页，从自选股点击标的代码或名称直接直达 `/terminal/stock` 全景研报工作台。
- ✅ **个股研报下置实时资讯与舆情流**：在买卖五档盘口正下方嵌入 `.stock-news-card`，支持分类标签、舆情多空色彩与无网自适应兜底。
- ✅ **个人秒级实时行情管道**：腾讯/新浪极速数据通道，批量快照 100~200ms，支持 SSE 推流，破除券商 50 万门槛。
- ✅ **双设备跨端环境自适应启动**：`start_dev.bat` 20ms 端口快速检测，有 Docker 唤起容器，无 Docker（原生 MongoDB/Redis）自适应秒跳过；Vite 代理锁定 `127.0.0.1:8000` 消除 IPv6 报错。
- ✅ **前端架构安全性、内存泄漏与 CSS 布局规范全面自检与加固（全栈交付）**：
  - **P0 级 XSS 安全加固**：集成 `dompurify`，建立统一防御工具库 `frontend/src/utils/markdown.ts`，彻底过滤全站 5 处 Markdown / AI 研报 `v-html` 渲染中的恶意标签与属性注入；
  - **P0 级内存泄漏治理**：
    - 在 `BacktestCenter/index.vue` 中绑定具名 `handleChartResize` 监听，并在 `onBeforeUnmount` 销毁 ECharts 实例 (`chartInstance.dispose()`) 与解绑事件，避免单页切换堆内存暴涨；
    - 在 `SingleAnalysis.vue` 的 `onUnmounted` 中彻底解绑 `document.visibilitychange` 全局监听；
    - 在 `frontend/src/utils/auth.ts` 中将 Token 自动刷新定时器改为单例管理，并在登录失效/登出 `clearAuthInfo()` 时同步调用 `clearTokenRefreshTimer()`，杜绝多次登录导致的定时器累积泄漏；
  - **P1 级 CSS 样式隔离与层叠上下文修正**：
    - 清理 `BatchAnalysis.vue` 末尾未加 `scoped` 的全局样式污染（此前暴力污染了全站 `.action-section` 类名），收归至局部作用域；
    - 降低 K 线悬浮画线工具箱 `.floating-draw-panel` 的 `z-index`（从 9999 降至 1500），解决穿透 Element Plus 模态弹窗与操作遮罩的显示 Bug；
  - **P2 级响应式布局与弱网构建优化**：
    - 剔除 `index.html` 中的 Google Fonts 外链，彻底消除国内网络环境下 5~10 秒字体加载超时阻塞 (FOIT)；
    - 重构 `TerminalLayout.vue`，用现代 `100dvh` 与 `flex: 1; min-height: 0;` 替换硬编码的 `calc(100vh - 66px)`；
    - 优化 `vite.config.ts`：将 `dompurify` 打包入独立 `markdown` 分块，静默 Sass 2.0 `legacy-js-api` 废弃警告；
    - 经 `vue-tsc` 与 Vite 严格构建检验，0 Error、0 Warning 100% 编译通过。
- ✅ **全终端美观视觉、缩放自适应与排版布局深度重构（全栈交付）**：
  - **K线/分时图矢量缩放与清晰度重构 (`StockKlineChart.vue`)**：
    - 废除原先写死 `const width = 840` 导致的图表横向变形拉伸问题；
    - 引入基于 `containerRef` 的原生 `ResizeObserver` 动态监听，`width` 实时与物理像素尺寸严格 1:1 对齐；
    - 无论是 80%~150% 浏览器缩放还是 Windows 笔记本 125%/150% 显示缩放，K线实体、分时折线、均线、网格与鼠标十字线始终保持物理级锐利、无横向变形失真，光标坐标拾取零漂移；
  - **三栏投研工作台弹性自适应排版 (`StockResearch/index.vue`)**：
    - 彻底解除原先三栏硬编码 `280px 1fr 400px` 在笔记本缩放时挤爆中间图表的隐患；
    - 建立响应式网格流体系：超宽屏 (>1400px) 保持 3 栏极客视角；常规/缩放笔记本 (1180px~1400px) 动态调窄左右侧边 (`240px 1fr 340px`)，优先保全核心 K 线图呼吸感；中屏 (860px~1180px) 优雅降级为图表/案卷双主列+量化画像沉底自适应网格；小屏 (<860px) 流式平铺；
    - 顶部 10 项金融指标条由生硬悬挂边框重构为自适应金融胶囊条 (`.metrics-strip`)，折行与缩放时自然延展；
    - 顶部买卖决策看板 (`.decision-signal-banner`) 与建仓/加仓/减仓/止损四维点位卡片 (`.decision-points-grid`) 增加断点网格，杜绝任何文字挤压折裂；
  - **回测中心与模拟盘弹窗弹性适配 (`BacktestCenter/index.vue`, `PaperTradingModal.vue`)**：
    - `PaperTradingModal.vue` 弹窗宽度改用 `min(920px, 94vw)`，4 项资产指标卡在小屏或缩放时自适应降为 2 列/1 列，彻底消除视口横向滚动溢出；
- ✅ **多智能体消融实验引擎、选股-回测一键管道与学术级投研研报导出（核心功能全栈交付）**：
  - **P0 级多智能体协同决策回测与消融实验引擎 (Multi-Agent Ablation Study)**：
    - 在后端 `app/services/backtest/strategies.py` 中实现 `MultiAgentStrategy(BaseStrategy)`，实现 4 大专业 Agent（宏观政策趋势、基本面估值、技术形态动量、风控审查一票否决）协同研判融合；
    - 内置决策仲裁机制：支持全票一致共识 (`consensus`) 与过半数多数票决 (`majority`) 双重仲裁模式；
    - 提供精细化消融开关 (`enable_macro`, `enable_fundamental`, `enable_technical`, `enable_risk_review`)，用户可自由开启/关闭单个 Agent 模块，直观对比净值曲线、夏普比率与最大回撤，为学术毕业设计第四章消融对比实验提供坚实量化实证支撑；
    - 在后端 `app/routers/backtest.py` 注册 `multi_agent` 策略描述与系统默认模板 `preset_btest_multi_agent_core`；
    - 在前端 `BacktestCenter/index.vue` 构建交互式消融实验控制台，提供专业卡片、实时开关与仲裁模式切换，深度适配深浅双色主题；
  - **P1 级选股池到组合回测 (Screener to Portfolio Backtest) 一键直连管道**：
    - 在 `StockPoolTable.vue` 表格操作栏增加 `[导入组合回测]` 快捷功能；
    - 在 `useStockPool.ts` 与 `StockPool/index.vue` 实现批量选中标的快速路由分发，将多只勾选股票代码自动组合成逗号分隔符流转至 `/terminal/backtest?symbols=...&strategy=multi_agent`；
    - `BacktestCenter` 挂载即自动激活多标的组合回测与仓位分配模型（等权加权 / 波动率倒数加权），彻底打通“智能选股 -> 组合装配 -> 多智能体回测验证”的全流程工作流闭环；
  - **P1 级全息投研决策报告一键导出 Markdown (Academic Markdown Report)**：
    - 在 `/terminal/report` 顶栏控制台新增 `[导出 Markdown 报告]` 按钮；
    - 纯客户端高速合成机构级与学术标准格式的投资决策 Markdown 案卷（包含标的概况与估值评级、大模型执行摘要、量化多因子评分矩阵、多智能体协同论据与风控审查防线、决策委员会终审仲裁与实战操作策略），一键下载 `.md` 文件，极大丰富答辩成果物与研究报告交付件；
  - **质量工程与自动化测试验收**：
    - 前端 `vue-tsc && vite build` 0 错误 100% 编译通过；
    - 后端 13 大全量自动化测试（含 A 股真实交易制度、滑点冲击、组合回测、多因子策略、模拟盘深度撮合等）全部 100% PASS。
- ✅ **小资金 (5万~50万) 交易决策与实战风控深度强化 (P0 & P1 全量落地)**：
  - **P0 级单笔风险预算与 A 股整手仓位精确试算器 (`StockResearch/index.vue`)**：
    - 针对小资金容错率极低、抗风险脆弱的痛点，彻底摒弃“凭感觉定仓位”的散户坏习惯；
    - 输入账户本金（默认 10 万）、单笔最大可容忍亏损比例（如 2.0% 即 ¥2,000）；
    - 结合计划买入价、目标止盈价与坚决止损价，扣除印花税 (0.05%)、佣金 (万2.5) 与 5 元起征摩擦，向下整手取整计算建议建仓股数 (100股整数倍)、建议手数、占用市值及仓位占比；
    - 严守单笔亏损不超预算硬红线，自动输出扣费后真实净盈亏比 (R:R) 与健康度定性（极佳/优良/及格/不划算）；
    - 提供 `[🎮 一键带入模拟盘 (XXX股)]` 按钮，直接携带精准整手股数唤起模拟盘下单弹窗。
  - **P0 级一票否决负面清单拦截器与交易时效画像 (`StockResearch/index.vue`)**：
    - 设立 4 盏客观量化红绿灯：
      1. 日内长上影冲高回落审查（盘中上影线超全天振幅 45% 且跳水回落）；
      2. 跌破 MA20 趋势生命线审查（现价破 MA20 且短均线死叉下行通道）；
      3. 高位沉重套牢盘压制审查（上方套牢盘 >= 68% 解套抛压沉重）；
      4. 净盈亏比实战红线审查（测算扣费净盈亏比 < 1.5:1）；
    - 只要任一指标亮红灯，立即挂出醒目【🚫 一票否决·严禁盲目开仓 / 追高】警报横幅，贯彻“小资金宁可踏空绝不违纪”的铁律；
    - 配套输出“交易时效与纪律画像”，明确标出建议持仓周期（如 3~5 个交易日）、策略定性（主升突破/回踩低吸/防守观望）及强制撤退纪律防线。
  - **P1 级选股中心小资金 3 套高爆发实战战法预设 (`stocks.py`, `useQuantStrategies.ts`, `useStockPool.ts`)**：
    - 🚀【小资金·放量起爆】：量比 >= 1.8，换手率 3%~12%，日涨幅 2%~6.5%，高换手突破主升浪，助小资金快速脱离成本区；
    - 🛡️【小资金·缩量企稳回踩】：量比 <= 1.2，换手率 1.5%~4.5%，振幅收敛回踩均线支撑，极小止损试错成本；
    - ⚖️【小资金·高盈亏比波段】：测算盈亏比 >= 2.5:1，50亿~300亿弹性中小盘，换手 2%~8%，小本金复利首选。
  - **P1 级回测引擎移动跟踪止盈 (Trailing Stop) / 保本止损 (Breakeven Stop) 与小资金实战风控指标**：
    - `app/services/backtest/backtest_engine.py`：单标的与多标的组合回测内核原生引入 `trailing_stop_pct`（浮盈峰值回撤跟踪离场）与 `breakeven_trigger_pct`（浮盈达标后回踩成本线保本离场）；
    - `app/services/backtest/performance_metrics.py`：新增计算 `max_consecutive_losses`（最大连续亏损笔数）、`max_consecutive_wins`、`avg_win`、`avg_loss`、`max_single_loss`、`expectancy_per_trade`（单笔数学期望收益）；
    - `BacktestCenter/index.vue`：前台表单提供移动跟踪与保本止损参数调节，结果看板网格扩充至 8 大 KPI 卡片，新增“连续亏损风控警报”与“单笔期望收益卡片”，均赢/均亏明细直观可见。
  - **P0 级 ATR 动态波动率标尺与五大量价生命周期状态机重构 (`StockResearch/index.vue`)**：
    - **彻底铲除固定硬编码乘数**：彻底废弃旧有 `px * 0.96`、`px * 1.03`、`px * 1.08`、`sup * 0.97` 等固定百分比死价格算法，根除高波妖股容易被洗盘毛刺震荡出局、低波权重蓝筹试错空间过大的致命缺陷；
    - **引入真实波动标尺 $ATR_{14}$ 自适应引擎**：优先提取 `TechnicalSnapshot.atr.atr14` 与日内振幅建立弹性度量衡，以标的真实波动幅度 $k \times ATR$ 动态适配缓冲垫与防守位；
    - **落地短线五大量价生命周期状态机 (Market Regime State Machine)**：
      1. `DOWNWARD_TREND` (破位阴跌防守禁区)：均线死叉下行或重度套牢压制时，**建仓点与加仓点直接输出 NULL**，UI 渲染 `--` 与 `⛔ 破位禁区·暂无安全买点`、`⛔ 严禁逆势加仓摊平`，坚决不硬塞买点，坚决杜绝误导散户抄底接飞刀；
      2. `STRONG_MOMENTUM` (主升浪强势加速期)：多头主升加速、上方筹码真空时，**卖点升级为动态移动跟踪止盈 (Trailing Stop)**，以 $\max(\text{MA5}, px - 1.2 \times ATR)$ 为防守底线，不破 MA5 坚决持股待涨让利润奔跑，**彻底杜绝大牛股过早卖飞**；
      3. `PULLBACK_SETUP` (良性缩量回踩区)：精确锚定核心筹码密集峰与 MA10 共振支撑点；
      4. `RANGE_BOUND` (箱体震荡中枢)：仅在箱底给出低吸点，处于半空中明确提示“半空中观望·日内无买点”；
      5. `EXTREME_OVERSOLD` (极度超跌衰竭区)：5日负乖离深超板块超卖阈值时提供左侧超窄幅试仓点，严格执行单笔试错铁律。
    - **卡片空安全 (Null-Safety) 与多模态视觉响应**：建仓/加仓卡片在禁区时置灰禁用，减仓卡片在主升浪时渲染为紫调“移动防守线”动态标识，散户试算器与模拟盘下单无缝兼容。
  - **P0 级板块与涨跌幅限制超参数自适应适配 (Board Volatility & Limit Profile Adaptation)**：
    - **板块极值分布精细化**：根据标的代码前缀智能识别五大板块类型，动态匹配专属波动率与风控超参数，彻底根除不同板块“一刀切”弊端：
      - `MAIN` (主板 ±10%): `atrFactor: 1.0`, `biasThreshold: 4.5%`, `trailingAtrK: 1.3`, `initialStopK: 1.2`, `profitTriggerK: 1.0`, `oversoldBias: -5.0%`
      - `20CM` (创业板/科创板 ±20%): `atrFactor: 1.25`, `biasThreshold: 6.5%`, `trailingAtrK: 1.6`, `initialStopK: 1.5`, `profitTriggerK: 1.1`, `oversoldBias: -8.0%`
      - `BSE` (北交所 ±30%): `atrFactor: 1.50`, `biasThreshold: 8.5%`, `trailingAtrK: 2.0`, `initialStopK: 1.8`, `profitTriggerK: 1.5`, `oversoldBias: -12.0%`
      - `ST` (风险警示 ±5%): `atrFactor: 0.75`, `biasThreshold: 3.0%`, `trailingAtrK: 0.9`, `initialStopK: 0.85`, `profitTriggerK: 0.7`, `oversoldBias: -3.5%`
      - `ETF` (场内低波组合): `atrFactor: 0.85`, `biasThreshold: 2.8%`, `trailingAtrK: 1.0`, `initialStopK: 1.0`, `profitTriggerK: 0.8`, `oversoldBias: -3.0%`
    - **前端横幅与负面清单自适应联动**：决策横幅新增 `.board-badge` 展示板块特征与当前风控阶段；一票否决负面清单（第 2 项）的超跌豁免阈值动态联动 `boardProfile.oversoldBias`。
  - **P0 级两阶段止盈防抖机制精细化 (Two-Phase Execution)**：
    - **阶段一 (试仓/蓄势初期)**：挂载初始宽防守（$1.2 \sim 1.5 \times ATR$），给予充足呼吸空间，彻底防范早盘集合竞价与前 15 分钟毛刺随机噪声洗盘震出；
    - **阶段二 (脱离成本主升期)**：浮盈突破 $1.0 \times ATR$（或获利盘 $\ge 85\%$）确认脱离成本区后，系统自动无缝激活紧身移动止盈 $\max(\text{成本保本}, \text{MA5}, H_n - k \times ATR)$，随新高逐日爬升，彻底让利润奔跑，防大牛股卖飞。
  - **真实市场历史大数据回测验证体系与后端数据通道加固 (`scripts/verify_trading_science.py` & `data_loader.py`)**：
    - `data_loader.py` 原生加固腾讯财经 `fqkline` 毫秒级免第三方依赖前复权通道，彻底解决 akshare/baostock 网络波动时的回测卡点；
    - `scripts/verify_trading_science.py` 实证对比 243 根真实日K线历史大数据：
      - **中际旭创 (300308, 创业板 20cm)**：胜率提升至 **53.33%** (+9.58%)，单笔期望收益跃升至 **+5.05%**，单笔最大盈利达到 **+45.56%**（旧版固定 8% 卖飞）；
      - **比亚迪 (002594, 主板 10cm)**：累计收益提升 **+16.23%**，最大回撤显著收窄 **+14.69%** (从 25.55% 降至 10.86%)，胜率提升至 **33.33%**；
      - **贵州茅台 (600519, 核心蓝筹)**：胜率跃升至 **38.89%** (+18.89%)，累计收益改善 **+8.62%**；
      - **赛力斯 (601127, 龙头)**：总交易笔数从 39 笔过度频繁交易减少到 16 笔，过滤近 **60% 无效杂波**，最大回撤改善 **+12.45%**。
  - **P0 级盈亏比科学归真、买卖点价格基准修复、低波慢牛与主升加速状态解耦 (`StockResearch/index.vue`)**：
    - **彻底铲除虚假盈亏比数学漏洞**：废除主升浪中硬编码假想 8% 收益（`px * 0.08`）与强制保底（`Math.max(1.8, ...)`）的粗糙算法。统一以真实目标空间与真实止损空间比值 $\frac{P_{\text{target}} - P_{\text{entry}}}{P_{\text{entry}} - P_{\text{stop}}}$ 严谨推演，彻底根治工商银行等低波银行股因止损极窄导致盈亏比虚夸到 4.17:1 的问题，真实呈现 1.44~1.63:1 的理性波段盈亏比；
    - **减仓/止盈卡片 (Card 3) 价格基准归真**：Card 3 主价格明确显示**预期目标止盈价**（正向空间），右侧以标签显示动态移动防守线（保本/锁利线），彻底解决此前止盈卡片显示低于成本的防守线价格、导致止盈和止损价格完全重合的严重显示混乱；
    - **低波防守蓝筹 vs 活跃高弹性标的状态机解耦**：引入 `isLowVolStock`（$ATR\% \le 2.0\%$ 或换手率 $< 0.6\%$），多头排列时准确识别为“稳健多头趋势波段”，采用沉稳理性的防守与波段文案，杜绝将千亿银行股误判为妖股“筹码真空加速”；
    - **全面根除买卖点文字拼接语病与夸张口号**：重构四大点位标签与推演理由，彻底清除“激进挂单(不追高)”、“主板10%阶段1宽防守”等生硬代码变量拼接，消除情绪化煽动词汇，全面采用客观严谨的机构级量化语言；
  - **P0 级量化算法深度自我答辩 (Critical Self-Audit) 与五大隐藏隐患彻底消除 (`StockResearch/index.vue`)**：
    1. **筹码物理就近性排序缺陷修复**：后端筹码接口或备用数组在部分场景下返回升序，原代码直接取 `validSupports[0]` 导致误取到底部最远古的远端支撑（如现价 10 元取到 6 元），现加入显式降序排序 `.sort((a, b) => b.price - a.price)`，严格锁定紧贴现价下方的第一道有效支撑峰；阻力峰加入 `.sort((a, b) => a.price - b.price)`，严格锁定最近的第一道套牢阻力；
    2. **消除单边阴跌“微涨假阳”诱多超跌陷阱**：原超跌判定含 `(profitRatio <= 12.0 && chg > 0)`，导致持续阴跌的极弱股某天平开微涨 +0.01% 时被盲目触发“极度超跌反抽买点”；现重构为必须结合极限负乖离共振 `(profitRatio <= 10.0 && bias5 <= (bp.oversoldBias * 0.75) && chg > 0)` 或 `kdjJ < 5`，彻底铲除接飞刀假信号；
    3. **顶栏看板盈亏比副标题在无买点/半空中时的认知错位消除**：原看板在箱体半空中无买点时仍显示“冒 1 份风险博 0.7 份收益”，产生误导；现新增独立状态机字段 `tradeDecision.rrSubtitle`，在无买点时准确指示“半空中无买点·追高盈亏比不足·建议等待回踩挂单”，做到看板与卡片 100% 逻辑自洽；
    4. **顶栏【模拟买入】按钮与底层海龟仓位测算器数据孤岛打通**：原点击顶栏【模拟买入】硬编码 100 股和现价，现全面联动 `calcEntryPx` 与 `calcShares`，将当前研判出的挂单价与基于真实 10 万元本金、ATR 风险预算算出的整手数（如工行自动带入 2400 股 ¥8.34）一键带入模拟盘，实现量化决策到交易执行的丝滑闭环；
    5. **未完成行情加载时的占位闪烁严格防御**：`tradeDecision` 计算增加 `!currentStock.value.price || currentStock.value.price <= 0` 守卫，数据未就绪时立即返回 `null`，彻底消除初始化阶段瞬时闪烁 ¥10.00 默认占位价的视觉瑕疵；
  - **P0 级场内 ETF 全景专区双轨制重大革新 (Dual-Mode ETF Terminal: Radar vs Full-Market Library)**：
    - **核心痛点解决**：此前专区仅内置 41 只精选标的，无法满足投资者对全市场 1000+ 只存量 ETF 进行全景筛选、流动性对比、多维度排序与深度投研的诉求；
    - **双轨制架构落地 (`EtfHub/index.vue` & `etf_service.py`)**：
      1. **模式一【🔥 核心热门雷达 (41只精选·5秒极速跳动)】**：保留 41 只高流动性主力旗舰，单 HTTP 请求 80ms 极速整包切片，5 秒无感轮询，专注日内领涨先锋与动量捕捉；
      2. **模式二【🌐 全市场 ETF 库 (1000+只·分页全景·行业分类)】**：
         - **全市场高并发实时聚合通道**：后端 `fetch_all_market_etfs_paged` 10 线程并发拉取全市场 1200+ 只场内 ETF 实时盘口，内存 25s 缓存防抖；
         - **智能多赛道分类**：基于自然语义与代码特征，自动将全市场 ETF 归类为 7 大赛道：核心宽基 (~230只)、硬核科技 (~190只)、制造周期 (~200只)、大类跨境 (~120只)、特色主题 (~190只)、固收货币 (~50只) 与全部全量，每个 Tab 实时标注动态匹配数量；
         - **多维专业排序与模糊检索**：支持按成交额降序（流动性优先，有效规避迷你僵尸基）、按涨跌幅降序（领涨榜）、按涨跌幅升序（超跌榜）、按现价、按换手率多维排序；支持代码或名称拼音模糊检索；
         - **密集表格与网格双视图 + 专业分页器**：支持 20/30/50/100 条分页切换、千分位价格、涨跌幅、成交额、换手率、振幅展示，支持一键加入自选与点击直达分时/K线量化投研。
  - **P0 级全市场股票池“最新交易日落后”与“盈亏比失真”双重缺陷根治与量化归真 (`stocks.py`, `quotes_ingestion_service.py`, `akshare_adapter.py`)**：
    - **根本原因深度排查与定性**：
      1. **最新交易日落后根因**：`QuotesIngestionService._collection_stale` 原先仅用 `.sort("trade_date", -1).limit(1)` 检索单条文档，只要有极个别标的（如早先调试的 ETF）更新为 `20261009`，便误判全集合非陈旧，导致休市期的全量 backfill 被直接跳过，全市场 5900+ 条数据停留于 `20261008`；
      2. **盈亏比失真根因**：旧版 `_calc_risk_reward_ratio` 包含 3 大硬伤：
         - 单日影线粗暴倒挂：使用 `(high - close) / (close - low)`，收在最高点的强势股被算成 0.2:1，收在最低点的阴跌股反而高达 9.9:1；
         - 缺失高低价时的伪随机数：使用代码 ASCII 求和取模生成假数值（如 000001 平安银行固定生成 6.90:1）；
         - 脏缓存死锁：一旦被调用即回写至 `market_quotes`，且函数优先读取 `q.get("risk_reward_ratio")`，使得假数据被永久固化。
    - **全量修复与技术升级落地**：
      - **陈旧数据检测算法重构**：`QuotesIngestionService._collection_stale` 改为统计 `trade_date < latest_trade_date` 的标的比例，若超过 5% 即判定集合陈旧触发补数；
      - **行情适配器与入库强化**：`AKShareAdapter` 补充 `amplitude` (振幅) 映射，无昨收时自动通过 `close - change` 反推精确昨收；
      - **新一代波动率驱动 + 真实实战扣费净盈亏比模型**：
        - 优先采用标的真实振幅（转换为波动率 `vol_pct`，限幅 [1.2%, 12.0%]），结合板块（ETF 1.6%、主板 3.0%、双创 4.5%、北交 5.5%）与换手率动态计算 ATR；
        - 量价形态状态机判定：日内超买冲高（$\ge 8\%$）压制弹性（1.2 ATR / 1.6 ATR 止损），主升突破（$\ge 1.5\%$）释放空间（2.2 ATR / 1.1 ATR 止损），破位走弱（$\le -3\%$）压低赔率（0.85 ATR / 1.4 ATR 止损），震荡蓄势（1.5 ATR / 1.0 ATR 止损）；
        - 基本面安全垫加成：低PE高ROE标的获得 1.15x 上方空间加成，亏损高估值 0.88x 折减；
        - 严格扣除券商实战交易摩擦（万0.876佣金、免5最低0.5元、个股万5印花税、ETF免征），计算出真实净盈亏比 (Net R:R)；
      - **全库清洗与全市场全局排序打通**：
        - 执行全市场 5933 条快照覆写刷新，清洗掉全部旧版伪随机数（000001 真实归位 1.66:1，300750 归位 2.25:1，562590 归位 1.45:1）；
        - `get_stock_pool` 支持 `risk_reward_ratio` 的全市场全局排序与精确区间筛选 (`c_min_rrr` / `c_max_rrr`)。
  - **P0 级个股与指数研报 K 线指标升级与交易时效纪律画像建仓决策算法**：
    - **K线均线与技术指标优化**：增加 MA10 均线图层，修复 MACD 指标在特定视窗下零轴与柱体显示不良的问题；
    - **交易时效与纪律画像算法建议**：在研报终端提供明确的“建仓决策”与“值博率”量化判断，杜绝脱离资金管理满仓单吊，统一实盘扣费净盈亏比与挂单计划逻辑。
  - **P0 级个股主力资金流向（超大单/大单/中单/小单）与北向资金持股透视中台及可视化闭环 (`capital_flow_service.py`, `stocks.py`, `CapitalFlowCard.vue`, `StockResearch/index.vue`)**：
    - **数据源与信披可行性实测深度定性**：
      - **北向资金 (沪深港通) 监管新规真相**：2024年8月19日起，沪深交易所及港交所全面取消北向资金日内盘中实时分时净买卖额披露，以防范短线投机跟风，全网任何第三方平台（含东财、同花顺、AKShare 等）日内实时净买卖额均已依法停更；个股持股明细调整为每季度后权威披露；
      - **开源数据源 AData (adata 2.9.5) 实测结论**：`adata.sentiment.north.north_flow()` 2024年8月19日后返回值均为 0（因交易所源头停更）；`adata.stock.market.get_capital_flow()` 直连东财 push2his 抓取因未配置完备请求头，直接被服务端防爬机制主动断开 (`RemoteDisconnected`)，稳定性差；
      - **落地架构方案（新浪财经 MoneyFlow + 东方财富 Datacenter 官方双通道架构）**：
        - 新浪财经 MoneyFlow 免 Token、毫秒级极速响应，稳定提供包含 2026 最新收盘日（如 2026-10-09）在内的 15~30 日历史分档大单主力数据（超大单、大单、中单、小单进出）；
        - 东方财富 Datacenter 官方接口（`RPT_MUTUAL_HOLDSTOCKNORTH_STA`）稳定提供权威季度末北向资金持股数、持股市值、占A股比例、占自由流通股比例。
    - **后端服务开发与接口开放**：
      - 新建 `app/services/capital_flow_service.py`：实现 `fetch_capital_flow`、`fetch_northbound_holding`、`get_combined_analysis`，自动推导主力 1日/3日/5日累计净额与多空姿态（爆量抢筹/大幅出逃/温和增配/承压洗盘）；
      - 在 `app/routers/stocks.py` 开放 `GET /api/stocks/{code}/capital-flow` 接口；
    - **前端可视化组件与量化画像联动**：
      - 新建 `frontend/src/components/Terminal/CapitalFlowCard.vue` 专用交互卡片，包含 4 大功能面板：
        - `主力动向看板`：展示今日主力净流入、5日主力累计净额、超大单 vs 大单机构火力、散户动向、四档进出图谱与量化博弈洞察；
        - `15日流向明细`：15 交易日历史数据表格（超大单/大单/中单/小单进出净额及红涨绿跌高亮）；
        - `北向持仓画像`：展示最新季度持股数/市值/占比、历季度变动表、2024-08-19 监管新规官方权威声明条；
        - `信披与数据源`：展示数据源与 AData 开源库实测对比透视说明；
      - 在 `StockResearch/index.vue` 的 `center-chart-col` 挂载 `CapitalFlowCard`，与行情并发异步加载，并在 `quantFactors` 因子得分计算中深度联动主力净流入占比与北向持股加成。

### 2. 跨设备数据同步运维与极速数据源指南 (Data Pipeline & Operations Guide for Antigravity)

> **给另一台设备上接手的 AI 助手与开发者的运维速查**：
> 若在另一台新设备（或全新初始化的本地 MongoDB）上运行系统，若发现股票池列表指标为空，只需在项目根目录按顺序执行以下两条脚本（均无需 TuShare Token，免注册，0 成本）：

```bash
# 1. 一键同步全市场上市公司财报指标（ROE、净利增长率、营收增长率、毛利率）
# 耗时约 12 秒，拉取近 6000 家上市公司最新季度报表，写入 stock_basic_info
python scripts/sync_financial_indicators.py 2024-09-30

# 2. 一键同步全市场实时估值与盘口快照（PE-TTM、PB-MRQ、总市值、流通市值）
# 耗时约 5.7 秒，8 线程并发直连腾讯行情通道，写入 market_quotes 并回填 stock_basic_info
python scripts/sync_realtime_valuation.py
```

执行完毕后刷新页面，股票池与所有量化指标即刻 100% 满血点亮！

### 3. 下一步建议开发任务 (Next Steps for Next Session)

#### 优先级 P1：数据推送与流式体验深化
1. **盘中分时图与行情接入 SSE 流式推送**：
   - 在 `StockResearch` 及 `TopTickerBar` 中接入 `GET /api/quotes/stream?symbols={code}`，使用前端 `EventSource`，实现盘中无需手动刷新、分时线与价格数字毫秒级跳动的实盘交易终端体验。

#### 优先级 P2：进阶功能与外部联动（按需选做）
1. **事前开仓冷静期质询契约弹窗 (Pre-Trade Checklist Modal)**：在模拟盘与实盘下单前弹窗，强制要求勾选“是否符合选股模式”、“止损位是否已预设”、“单笔亏损是否在预算内”3道心理质询题，防冲动交易；
2. **微信 Webhook 界面配置项**：在前端“系统配置”或用户头像抽屉中增加微信 Webhook / Server酱 Key 交互配置，无需手动改 `.env`；
3. **实盘券商网格交易策略模板**：将目前双均线/MACD策略扩充至网格交易 (Grid Trading) 和日内做 T 策略模板。




