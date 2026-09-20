<template>
  <div class="overview-view">
    <!-- 顶部 5 大宏观量化 KPI 卡片栏 -->
    <div class="kpi-banner">
      <div class="kpi-card">
        <div class="kpi-header">
          <span class="kpi-title">市场研判状态</span>
          <span class="kpi-tag status-bull">震荡偏强</span>
        </div>
        <div class="kpi-val tabular-nums">64.5 <span class="sub-val">/ 100</span></div>
        <div class="kpi-sub">
          <span>情绪动能</span>
          <span class="trend-up tabular-nums">+3.2 pt</span>
        </div>
      </div>

      <div class="kpi-card">
        <div class="kpi-header">
          <span class="kpi-title">市场宽度 (涨跌分布)</span>
          <span class="kpi-tag">多头占优</span>
        </div>
        <div class="kpi-val tabular-nums">
          <span class="up-count">3,214</span>
          <span class="mid-slash">/</span>
          <span class="down-count">1,842</span>
        </div>
        <div class="kpi-sub">
          <span>涨停 68 家</span>
          <span class="neutral">跌停 4 家</span>
        </div>
      </div>

      <div class="kpi-card">
        <div class="kpi-header">
          <span class="kpi-title">两市总成交额</span>
          <span class="kpi-tag">温和放量</span>
        </div>
        <div class="kpi-val tabular-nums">2.08 <span class="sub-val">万亿</span></div>
        <div class="kpi-sub">
          <span>较上一日</span>
          <span class="trend-up tabular-nums">+1,420 亿 (+7.3%)</span>
        </div>
      </div>

      <div class="kpi-card clickable" @click="$router.push('/terminal/screening')">
        <div class="kpi-header">
          <span class="kpi-title">量化候选股票池</span>
          <el-icon class="arrow-icon"><ArrowRight /></el-icon>
        </div>
        <div class="kpi-val tabular-nums">126 <span class="sub-val">只</span></div>
        <div class="kpi-sub">
          <span>全市场 4,892 只初筛</span>
          <span class="highlight tabular-nums">筛选率 2.6%</span>
        </div>
      </div>

      <div class="kpi-card clickable" @click="$router.push('/terminal/workflow')">
        <div class="kpi-header">
          <span class="kpi-title">多智能体协同任务</span>
          <el-icon class="arrow-icon"><ArrowRight /></el-icon>
        </div>
        <div class="kpi-val tabular-nums">5 <span class="sub-val">组运行中</span></div>
        <div class="kpi-sub">
          <span>已输出 12 份案卷</span>
          <span class="highlight">0 异常阻塞</span>
        </div>
      </div>
    </div>

    <!-- 01->05 核心全景链路横幅 -->
    <div class="pipeline-section">
      <PipelineBanner />
    </div>

    <!-- 主展示网格 -->
    <div class="main-dashboard-grid">
      <!-- 左侧：市场分时走势与行业表现 -->
      <div class="grid-left-panel">
        <!-- 分时走势 -->
        <MarketTrendChart />

        <!-- 行业与风格板块看板 -->
        <div class="sectors-card">
          <div class="card-header">
            <div class="header-left">
              <span class="header-title">高频行业资金与涨跌监测</span>
              <span class="header-sub">申万一级行业实时监测</span>
            </div>
            <div class="header-right">
              <span class="time-tip tabular-nums">更新于 10:15:30</span>
            </div>
          </div>

          <div class="sectors-table-wrapper">
            <table class="sectors-table">
              <thead>
                <tr>
                  <th class="text-left">行业板块</th>
                  <th class="text-right">涨跌幅</th>
                  <th class="text-right">主力净流入</th>
                  <th class="text-right">领涨龙头</th>
                  <th class="text-right">量化强度分</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="sec in industryList" :key="sec.name">
                  <td class="text-left fw-semibold">{{ sec.name }}</td>
                  <td :class="['text-right tabular-nums', sec.change >= 0 ? 'color-up' : 'color-down']">
                    {{ sec.change >= 0 ? '+' : '' }}{{ sec.change.toFixed(2) }}%
                  </td>
                  <td :class="['text-right tabular-nums', sec.flow >= 0 ? 'color-up' : 'color-down']">
                    {{ sec.flow >= 0 ? '+' : '' }}{{ sec.flow }} 亿
                  </td>
                  <td class="text-right">
                    <span 
                      class="leader-badge clickable" 
                      :title="'点击立即个股研判: ' + sec.leader"
                      @click.stop="goToStock(sec.leaderCode)"
                    >
                      {{ sec.leader }}
                    </span>
                  </td>
                  <td class="text-right tabular-nums fw-bold">
                    <span class="score-pill" :class="sec.score >= 85 ? 'high' : 'medium'">{{ sec.score }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 右侧：量化主线与实时多智能体分析流水线流 -->
      <div class="grid-right-panel">
        <!-- 量化主线卡片 -->
        <div class="themes-card">
          <div class="card-header">
            <span class="header-title">量化重点进攻主线 (Quant Alpha)</span>
            <span class="badge-blue">3 个主线共振</span>
          </div>

          <div class="theme-items">
            <div 
              v-for="t in themeList" 
              :key="t.name" 
              class="theme-item"
              @click="$router.push('/terminal/screening')"
            >
              <div class="theme-top">
                <span class="theme-name">{{ t.name }}</span>
                <span class="theme-score tabular-nums">评分 {{ t.score }}</span>
              </div>
              <p class="theme-logic">{{ t.logic }}</p>
              <div class="theme-stocks">
                <span class="stocks-label">核心成分池:</span>
                <span 
                  v-for="s in t.stocks" 
                  :key="s.code" 
                  class="stock-pill clickable"
                  :title="'点击前往个股研判: ' + s.name"
                  @click.stop="goToStock(s.code)"
                >
                  {{ s.name }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- 实时智能体研判流 -->
        <div class="feed-card">
          <div class="card-header">
            <div class="feed-header-left">
              <span class="pulse-indicator"></span>
              <span class="header-title">智能体协同事件流 (Live Event Feed)</span>
            </div>
            <button class="text-btn" @click="$router.push('/terminal/workflow')">进入工作流 →</button>
          </div>

          <div class="feed-list">
            <div v-for="(ev, idx) in liveEvents" :key="'ev-' + idx" class="feed-item">
              <div class="feed-time tabular-nums">{{ ev.time }}</div>
              <div class="feed-badge" :class="ev.badgeClass">{{ ev.agent }}</div>
              <div class="feed-content">
                <span 
                  class="feed-target"
                  :class="{ clickable: !!ev.code }"
                  :title="ev.code ? '点击立即个股研判: ' + ev.stock : ''"
                  @click.stop="ev.code && goToStock(ev.code)"
                >
                  {{ ev.stock }}
                </span>
                <span class="feed-text">{{ ev.msg }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ArrowRight } from '@element-plus/icons-vue'
import PipelineBanner from '@/components/Terminal/PipelineBanner.vue'
import MarketTrendChart from '@/components/Terminal/MarketTrendChart.vue'

const router = useRouter()

function goToStock(code?: string) {
  if (!code) return
  router.push({ path: '/terminal/stock', query: { code } })
}

const industryList = [
  { name: '半导体与芯片', change: 3.82, flow: 42.6, leader: '中芯国际 (+4.8%)', leaderCode: '688981', score: 94 },
  { name: '光通信/光模块', change: 3.15, flow: 28.3, leader: '中际旭创 (+5.2%)', leaderCode: '300308', score: 91 },
  { name: '算力与服务器', change: 2.78, flow: 21.5, leader: '浪潮信息 (+3.9%)', leaderCode: '000977', score: 88 },
  { name: '人形机器人', change: 2.45, flow: 15.2, leader: '绿的谐波 (+4.1%)', leaderCode: '688017', score: 86 },
  { name: '电力电网设备', change: 1.20, flow: 8.4, leader: '国电南瑞 (+1.6%)', leaderCode: '600406', score: 79 },
  { name: '白酒与食品饮料', change: -1.12, flow: -18.6, leader: '贵州茅台 (-0.9%)', leaderCode: '600519', score: 58 },
  { name: '煤炭与开采', change: -1.45, flow: -12.1, leader: '中国神华 (-1.3%)', leaderCode: '601088', score: 52 },
]

const themeList = [
  {
    name: '先进封测与先进制程国产化',
    score: 94,
    logic: '大基金三期扩容带动核心晶圆厂产能利用率由 76% 攀升至 88%，上游设备与材料景气度持续处于上行通道。',
    stocks: [
      { name: '中芯国际', code: '688981' },
      { name: '北方华创', code: '002371' },
      { name: '中微公司', code: '688012' },
      { name: '拓荆科技', code: '688072' }
    ]
  },
  {
    name: 'AI 数据中心超算与高速光互联',
    score: 91,
    logic: '全球 1.6T 光模块批量出货加速，头部通信硬件厂商 Q3 订单饱满，供应链具备极强盈利弹性。',
    stocks: [
      { name: '中际旭创', code: '300308' },
      { name: '新易盛', code: '300502' },
      { name: '天孚通信', code: '300394' }
    ]
  },
  {
    name: '具身智能与机器人核心零组件',
    score: 86,
    logic: '特斯拉与国内主机厂供应链定点逐步清晰，高精度减速器及六维力传感器出货量呈现倍增势头。',
    stocks: [
      { name: '绿的谐波', code: '688017' },
      { name: '三花智控', code: '002050' },
      { name: '鸣志电器', code: '603728' }
    ]
  }
]

const liveEvents = [
  {
    time: '10:15:30',
    agent: 'Decision Engine',
    badgeClass: 'badge-decision',
    stock: '中芯国际 (688981)',
    code: '688981',
    msg: '综合裁决生成：多头得分 82.4，建议仓位 15%-20%，案卷完成入库'
  },
  {
    time: '10:15:15',
    agent: 'Risk Agent',
    badgeClass: 'badge-risk',
    stock: '中芯国际 (688981)',
    code: '688981',
    msg: '风险审查完成：静态 PE 处于 78% 分位，建议设 78.50 元硬止损'
  },
  {
    time: '10:14:48',
    agent: 'Fund Agent',
    badgeClass: 'badge-fund',
    stock: '中芯国际 (688981)',
    code: '688981',
    msg: '产能利用率回升至 88.5%，Q3 营收预期上调 4.2%，置信度 85%'
  },
  {
    time: '10:13:02',
    agent: 'Tech Agent',
    badgeClass: 'badge-tech',
    stock: '北方华创 (002371)',
    code: '002371',
    msg: '放量突破 60 日横盘箱体，MACD 零轴上方二次金叉成立'
  },
  {
    time: '10:10:00',
    agent: 'Quant Engine',
    badgeClass: 'badge-quant',
    stock: 'A股全市场',
    code: '',
    msg: '4,892 只标的多因子打分跑批完成，初筛候选池精炼至 126 只'
  }
]
</script>

<style scoped lang="scss">
.overview-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 1600px;
  margin: 0 auto;
}

.kpi-banner {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}

.kpi-card {
  background-color: #ffffff;
  border: 1px solid #e4e7ec;
  border-radius: 6px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: all 0.15s ease;

  &.clickable {
    cursor: pointer;
    &:hover {
      border-color: #175cd3;
      box-shadow: 0 2px 8px rgba(23, 92, 211, 0.08);
      .arrow-icon {
        transform: translateX(3px);
        color: #175cd3;
      }
    }
  }

  .kpi-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .kpi-title {
      font-size: 11px;
      font-weight: 600;
      color: #667085;
    }

    .arrow-icon {
      font-size: 13px;
      color: #98a2b3;
      transition: transform 0.15s ease;
    }

    .kpi-tag {
      font-size: 10px;
      font-weight: 600;
      padding: 1px 6px;
      border-radius: 3px;
      background-color: #f2f4f7;
      color: #344054;

      &.status-bull {
        background-color: #fef3f2;
        color: #d92d20;
      }
    }
  }

  .kpi-val {
    font-size: 20px;
    font-weight: 700;
    color: #101828;
    margin: 6px 0 4px 0;
    line-height: 1.2;

    .sub-val {
      font-size: 11px;
      font-weight: 500;
      color: #667085;
    }

    .up-count { color: #d92d20; }
    .down-count { color: #039855; }
    .mid-slash { color: #d0d5dd; margin: 0 4px; font-weight: 400; }
  }

  .kpi-sub {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: #475467;

    .trend-up {
      color: #d92d20;
      font-weight: 600;
    }
    .neutral {
      color: #667085;
    }
    .highlight {
      color: #175cd3;
      font-weight: 600;
    }
  }
}

.pipeline-section {
  width: 100%;
}

.main-dashboard-grid {
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 16px;
  align-items: flex-start;
}

.grid-left-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sectors-card, .themes-card, .feed-card {
  background-color: #ffffff;
  border: 1px solid #e4e7ec;
  border-radius: 6px;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #eaecf0;
  background-color: #fafbfc;

  .header-left {
    display: flex;
    align-items: baseline;
    gap: 8px;
  }

  .header-title {
    font-size: 13px;
    font-weight: 700;
    color: #101828;
  }

  .header-sub {
    font-size: 11px;
    color: #667085;
  }

  .time-tip {
    font-size: 11px;
    color: #98a2b3;
  }

  .badge-blue {
    font-size: 11px;
    font-weight: 600;
    color: #175cd3;
    background-color: #eff8ff;
    padding: 2px 8px;
    border-radius: 4px;
  }

  .text-btn {
    border: none;
    background: transparent;
    color: #175cd3;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    &:hover {
      text-decoration: underline;
    }
  }
}

.sectors-table-wrapper {
  overflow-x: auto;
}

.sectors-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;

  th {
    padding: 8px 16px;
    background-color: #f8fafc;
    color: #475467;
    font-weight: 600;
    border-bottom: 1px solid #eaecf0;
    font-size: 11px;
  }

  td {
    padding: 9px 16px;
    border-bottom: 1px solid #f2f4f7;
    color: #101828;
  }

  tbody tr:hover {
    background-color: #f8fafc;
  }

  .text-left { text-align: left; }
  .text-right { text-align: right; }
  .fw-semibold { font-weight: 600; }
  .fw-bold { font-weight: 700; }

  .color-up { color: #d92d20; font-weight: 600; }
  .color-down { color: #039855; font-weight: 600; }

  .leader-badge {
    color: #344054;
    font-size: 11px;
    background-color: #f2f4f7;
    padding: 2px 6px;
    border-radius: 3px;
    border: 1px solid transparent;

    &.clickable {
      cursor: pointer;
      transition: all 0.15s ease;
      &:hover {
        background-color: #eff8ff;
        color: #175cd3;
        border-color: #b2ddff;
      }
    }
  }

  .score-pill {
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 11px;
    &.high {
      background-color: #fef3f2;
      color: #d92d20;
    }
    &.medium {
      background-color: #eff8ff;
      color: #175cd3;
    }
  }
}

.grid-right-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.theme-items {
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.theme-item {
  border: 1px solid #eaecf0;
  border-radius: 5px;
  padding: 10px 12px;
  background-color: #ffffff;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    border-color: #175cd3;
    background-color: #f8fafc;
  }

  .theme-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;

    .theme-name {
      font-size: 12px;
      font-weight: 700;
      color: #101828;
    }

    .theme-score {
      font-size: 11px;
      font-weight: 700;
      color: #175cd3;
      background-color: #eff8ff;
      padding: 1px 6px;
      border-radius: 3px;
    }
  }

  .theme-logic {
    font-size: 11px;
    color: #475467;
    line-height: 1.45;
    margin: 0 0 6px 0;
  }

  .theme-stocks {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;

    .stocks-label {
      color: #98a2b3;
    }

    .stock-pill {
      background-color: #f2f4f7;
      color: #344054;
      padding: 1px 6px;
      border-radius: 3px;
      font-size: 10px;
      font-weight: 500;
      border: 1px solid transparent;

      &.clickable {
        cursor: pointer;
        transition: all 0.15s ease;
        &:hover {
          background-color: #eff8ff;
          color: #175cd3;
          border-color: #b2ddff;
        }
      }
    }
  }
}

.feed-header-left {
  display: flex;
  align-items: center;
  gap: 8px;

  .pulse-indicator {
    width: 7px;
    height: 7px;
    background-color: #12b76a;
    border-radius: 50%;
    animation: pulse 1.8s infinite;
  }
}

@keyframes pulse {
  0% { transform: scale(0.95); opacity: 0.8; }
  50% { transform: scale(1.3); opacity: 1; }
  100% { transform: scale(0.95); opacity: 0.8; }
}

.feed-list {
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.feed-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 11px;
  line-height: 1.4;

  .feed-time {
    color: #98a2b3;
    font-family: monospace;
    flex-shrink: 0;
    margin-top: 1px;
  }

  .feed-badge {
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 10px;
    font-weight: 700;
    flex-shrink: 0;

    &.badge-decision { background-color: #fef3f2; color: #d92d20; }
    &.badge-risk { background-color: #fffaeb; color: #b54708; }
    &.badge-fund { background-color: #f0f9ff; color: #026aa2; }
    &.badge-tech { background-color: #fdf2fa; color: #c11574; }
    &.badge-quant { background-color: #eff8ff; color: #175cd3; }
  }

  .feed-content {
    color: #344054;
    .feed-target {
      font-weight: 600;
      color: #101828;
      margin-right: 6px;

      &.clickable {
        cursor: pointer;
        color: #175cd3;
        text-decoration: underline;
        text-underline-offset: 2px;
        &:hover {
          color: #154cbd;
        }
      }
    }
    .feed-text {
      color: #475467;
    }
  }
}

.tabular-nums {
  font-variant-numeric: tabular-nums;
}
</style>
