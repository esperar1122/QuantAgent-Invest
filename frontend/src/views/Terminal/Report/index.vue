<template>
  <div class="report-view">
    <!-- 顶部工具栏 -->
    <div class="report-toolbar no-print">
      <div class="tb-left">
        <el-button size="small" @click="$router.push('/terminal/stock?code=' + reportStock.code)">
          <el-icon><ArrowLeft /></el-icon>
          返回个股
        </el-button>
        <el-button size="small" @click="$router.push('/terminal/workflow?code=' + reportStock.code)">
          <el-icon><Connection /></el-icon>
          溯源 Agent 工作流
        </el-button>
        <span class="report-no font-mono">DOC ID: QA-202609-{{ reportStock.code }}</span>
      </div>

      <div class="tb-right">
        <el-button type="primary" size="small" @click="handlePrint">
          <el-icon><Printer /></el-icon>
          打印 / 导出研报 PDF
        </el-button>
      </div>
    </div>

    <!-- 研报纸质白皮书主卡片 -->
    <div class="report-paper">
      <!-- 研报顶栏封面标头 -->
      <header class="report-header">
        <div class="inst-brand">
          <span class="inst-name">QuantAgent-Invest 智能投研工作站</span>
          <span class="inst-sub">深度投资研究报告 · 机构级量化与智能体决策内参</span>
        </div>
        <div class="report-meta">
          <div class="meta-row"><span class="mk">发布日期:</span><span class="mv font-mono">2026-09-20</span></div>
          <div class="meta-row"><span class="mk">报告状态:</span><span class="mv text-success">正式发布 (Final)</span></div>
          <div class="meta-row"><span class="mk">安全等级:</span><span class="mv">内部机密 (Level-3)</span></div>
        </div>
      </header>

      <!-- 核心投资评级横幅 (Rating Banner) -->
      <div class="rating-banner">
        <div class="rating-left">
          <div class="stock-title-row">
            <h1 class="stock-name">{{ reportStock.name }}</h1>
            <span class="stock-code font-mono">{{ reportStock.marketSymbol }}</span>
            <span class="badge-board">{{ reportStock.board }}</span>
          </div>
          <p class="stock-desc">{{ reportStock.desc }}</p>
        </div>

        <div class="rating-right">
          <div class="rating-block">
            <span class="rating-title">投资评级</span>
            <span class="rating-value color-up">买入 (BUY)</span>
            <span class="rating-type">首次覆盖</span>
          </div>

          <div class="target-block">
            <span class="target-title">目标区间 (6-12M)</span>
            <span class="target-price font-mono">{{ reportStock.targetPrice }} 元</span>
            <span class="target-upside color-up">潜在空间 +14.0%</span>
          </div>

          <div class="score-block">
            <span class="score-title">综合置信分</span>
            <span class="score-value font-mono">82.4 <span class="max-score">/ 100</span></span>
            <span class="score-desc">多智能体协同打分</span>
          </div>
        </div>
      </div>

      <!-- 核心财务与交易基准对照表 -->
      <div class="benchmark-grid">
        <div class="bm-col">
          <span class="bk">当前股价</span>
          <span class="bv tabular-nums">{{ reportStock.price.toFixed(2) }} 元</span>
        </div>
        <div class="bm-col">
          <span class="bk">52周最高/最低</span>
          <span class="bv tabular-nums">{{ reportStock.high52 }} / {{ reportStock.low52 }} 元</span>
        </div>
        <div class="bm-col">
          <span class="bk">总市值 / 流通市值</span>
          <span class="bv tabular-nums">{{ reportStock.marketCap }} / {{ reportStock.circCap }} 亿元</span>
        </div>
        <div class="bm-col">
          <span class="bk">市盈率 PE (TTM)</span>
          <span class="bv tabular-nums">{{ reportStock.pe }} 倍</span>
        </div>
        <div class="bm-col">
          <span class="bk">建议配置仓位</span>
          <span class="bv tabular-nums highlight">15% - 20%</span>
        </div>
        <div class="bm-col">
          <span class="bk">风控硬止损线</span>
          <span class="bv tabular-nums text-danger">{{ reportStock.stopLossPrice }} 元</span>
        </div>
      </div>

      <!-- 正文章节 1: 核心投资要点与摘要 -->
      <section class="report-section">
        <div class="sec-header">
          <span class="sec-num">01</span>
          <h2 class="sec-title">核心投资观点与摘要 (Executive Summary)</h2>
        </div>
        <div class="sec-content">
          <p class="summary-paragraph">
            <strong>核心逻辑：</strong> 经历前序行业周期探底，当前 {{ reportStock.sector }} 产业景气度呈现明确回升态势。{{ reportStock.name }} ({{ reportStock.code }}) 核心主营业务盈利质量扎实、产能稼动率高位运行。在国家战略产业政策引导与资本协同驱动下，公司作为行业旗舰级企业，市场占有率与核心技术壁垒稳固，中长期资产配置价值凸显。
          </p>
          <div class="highlight-boxes">
            <div class="h-box">
              <div class="h-num font-mono">01 / 量化引擎初筛</div>
              <div class="h-title">全市场 4,892 只标的排位 Top 2.6%</div>
              <div class="h-desc">动量趋势因子得分 92，机构主力资金连续 5 日呈净流入状态。</div>
            </div>
            <div class="h-box">
              <div class="h-num font-mono">02 / 智能体协同实证</div>
              <div class="h-title">宏观、技术与基本面 8 项核心强事实共振</div>
              <div class="h-desc">多头证据权重达 72%，政策红利与产能释放驱动中长期重估。</div>
            </div>
            <div class="h-box warning">
              <div class="h-num font-mono">03 / 风险合规审查</div>
              <div class="h-title">高估值约束下的网格化逢低分批介入</div>
              <div class="h-desc">静态 PE 处于 78% 分位数，杜绝高位追涨，严设 {{ reportStock.stopLossPrice }} 元风控防线。</div>
            </div>
          </div>
        </div>
      </section>

      <!-- 正文章节 2: Quant Engine 因子透视 -->
      <section class="report-section">
        <div class="sec-header">
          <span class="sec-num">02</span>
          <h2 class="sec-title">Quant Engine 量化因子画像与打分分解</h2>
        </div>
        <div class="sec-content">
          <div class="factor-table-wrapper">
            <table class="factor-table">
              <thead>
                <tr>
                  <th style="width: 140px;">因子维度</th>
                  <th style="width: 90px;" class="text-right">因子打分</th>
                  <th style="width: 110px;" class="text-center">全市场分位</th>
                  <th style="width: 80px;" class="text-right">模型权重</th>
                  <th>量化特征描述与关键结论</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td class="fw-bold">动量趋势 (Momentum)</td>
                  <td class="text-right tabular-nums fw-bold color-up">92.0</td>
                  <td class="text-center tabular-nums">Top 3.2%</td>
                  <td class="text-right tabular-nums">35%</td>
                  <td>日线有效突破 60 日横盘平台，MA5/20/60 均线呈完美多头发散，量比达 1.45。</td>
                </tr>
                <tr>
                  <td class="fw-bold">资金流向 (Money Flow)</td>
                  <td class="text-right tabular-nums fw-bold color-up">89.0</td>
                  <td class="text-center tabular-nums">Top 4.8%</td>
                  <td class="text-right tabular-nums">25%</td>
                  <td>机构大单席位近 5 日净流入合计 14.8 亿元，北向资金与融资杠杆共振加仓。</td>
                </tr>
                <tr>
                  <td class="fw-bold">质量成长 (Quality)</td>
                  <td class="text-right tabular-nums fw-bold">85.0</td>
                  <td class="text-center tabular-nums">Top 8.1%</td>
                  <td class="text-right tabular-nums">20%</td>
                  <td>毛利率环比修复 2.4 pct，研发费用率稳定在行业前 10% 分位，盈利韧性强。</td>
                </tr>
                <tr>
                  <td class="fw-bold">估值安全边际 (Value)</td>
                  <td class="text-right tabular-nums fw-bold text-danger">64.0</td>
                  <td class="text-center tabular-nums">Top 42.0%</td>
                  <td class="text-right tabular-nums">20%</td>
                  <td>动态 PE 处于历史 78% 分位数，虽具备成长性溢价支撑，但短期安全边际偏紧。</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- 正文章节 3: 多智能体协同研究事实与决议证据链 -->
      <section class="report-section">
        <div class="sec-header">
          <span class="sec-num">03</span>
          <h2 class="sec-title">多智能体协同研究事实与决议证据链</h2>
        </div>
        <div class="sec-content">
          <div class="evidence-block">
            <h3 class="eb-title">3.1 核心支持证据链条 (Supporting Points)</h3>
            <ul class="eb-list">
              <li><strong>[宏观政策智能体]</strong> 国家战略对高端制造业发展规划明确，自主可控专项投资基金持续撬动社会资本跟进。</li>
              <li><strong>[技术形态智能体]</strong> 股价有效站上 60 日均线生命线，量能放大配合 MACD 零轴二次金叉，中线买点确立。</li>
              <li><strong>[基本面产业智能体]</strong> 核心产线利用率突破 88%，产品平均售价（ASP）触底回升，Q3 业绩指引大概率超越预期。</li>
              <li><strong>[情绪资金智能体]</strong> 龙虎榜与北向资金连续三个交易周呈加仓净买入态势，市场风险偏好提升。</li>
            </ul>
          </div>

          <div class="evidence-block">
            <h3 class="eb-title">3.2 潜在风险审查与防线 (Risk Factors)</h3>
            <ul class="eb-list">
              <li><strong>[风险控制智能体]</strong> 静态估值处于历史偏高水平，融资杠杆买入占比连续 3 日上升，短期存在获利盘回吐压力。</li>
              <li><strong>[宏观政策智能体]</strong> 外部关键半导体零配件出口管制政策潜在升级扰动，需跟踪国内二期/三期替代品验证进度。</li>
            </ul>
          </div>

          <div class="arbitration-paper-box">
            <div class="apb-header">
              <span class="apb-title">决策委员会最终仲裁结论 (Final Committee Ruling)</span>
              <span class="apb-badge">加权打分 82.4 / 100</span>
            </div>
            <p class="apb-text">
              针对「基本面产业智能体看好产能扩张」与「风险控制智能体提示估值溢价」的核心分歧，决策委员会裁定：<strong>中长期产业景气上行与政策催化是主要矛盾，短期估值可通过节奏控制化解。</strong> 投资建议如下：
            </p>
            <div class="action-recommendation-grid">
              <div class="arg-item">
                <span class="arg-k">建仓策略</span>
                <span class="arg-v">禁止盲目追高，建议在 {{ buyRange }} 元区间（回踩 MA5）分批建仓</span>
              </div>
              <div class="arg-item">
                <span class="arg-k">仓位控制</span>
                <span class="arg-v">单标的头寸上限控制在组合总资产的 15% - 20%</span>
              </div>
              <div class="arg-item">
                <span class="arg-k">止损策略</span>
                <span class="arg-v text-danger">以 {{ reportStock.stopLossPrice }} 元为有效跌破硬止损基准（跌破 20 日生命线无条件清仓）</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 报告尾部合规声明 -->
      <footer class="report-footer">
        <div class="disclaimer-title">免责声明与合规说明 (Disclaimer)</div>
        <p class="disclaimer-text">
          本报告由 QuantAgent-Invest 智能投研系统自动汇总生成。本系统结合了量化多因子评分引擎与多智能体协作分析模型，旨在为专业机构投资者提供高效率的投研线索与证据参考。报告中的所有数据均基于公开市场数据及系统模拟回测演算，不构成直接的投资交易要约。股市有风险，投资需谨慎。
        </p>
        <div class="footer-sign">
          <span>QuantAgent-Invest Research Division</span>
          <span>© 2026 QuantAgent. All Rights Reserved.</span>
        </div>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, Connection, Printer } from '@element-plus/icons-vue'
import { stocksApi } from '@/api/stocks'

const route = useRoute()

const hotDict: Record<string, { name: string; board: string; sector: string; desc: string }> = {
  'sh000001': { name: '上证指数', board: '核心指数', sector: 'A股大盘基准 / 宏观核心', desc: '上海证券市场核心基准 · 覆盖沪市全部上市股票，反映全市场综合走势' },
  '000001': { name: '上证指数', board: '核心指数', sector: 'A股大盘基准 / 宏观核心', desc: '上海证券市场核心基准 · 覆盖沪市全部上市股票，反映全市场综合走势' },
  'sz399001': { name: '深证成指', board: '核心指数', sector: '深圳主板及成长蓝筹', desc: '深圳证券市场核心成份基准 · 覆盖深市优质标杆标的' },
  '399001': { name: '深证成指', board: '核心指数', sector: '深圳主板及成长蓝筹', desc: '深圳证券市场核心成份基准 · 覆盖深市优质标杆标的' },
  'sz399006': { name: '创业板指', board: '核心指数', sector: '新质生产力 / 高成长创新', desc: '创业板核心资产代表 · 汇聚新能源、高端制造与医疗领军' },
  '399006': { name: '创业板指', board: '核心指数', sector: '新质生产力 / 高成长创新', desc: '创业板核心资产代表 · 汇聚新能源、高端制造与医疗领军' },
  'sh000680': { name: '科创综指', board: '核心指数', sector: '硬科技与战略新兴', desc: '科创板全样本指数 · 展现中国硬科技前沿创新全貌' },
  '000680': { name: '科创综指', board: '核心指数', sector: '硬科技与战略新兴', desc: '科创板全样本指数 · 展现中国硬科技前沿创新全貌' },
  '688981': { name: '中芯国际', board: '科创板', sector: '申万半导体 / 晶圆制造', desc: '全球领先晶圆制造代工龙头 · 先进制程自主可控核心承载标的' },
  '600519': { name: '贵州茅台', board: '主板', sector: '食品饮料 / 白酒', desc: '中国高端白酒卓越龙头 · 超强品牌壁垒与充沛现金流资产' },
  '300750': { name: '宁德时代', board: '创业板', sector: '电力设备 / 动力电池', desc: '全球动力电池与储能系统龙头 · 规模与技术全球领先' },
  '002594': { name: '比亚迪', board: '主板', sector: '汽车 / 新能源车', desc: '新能源整车与垂直产业链领军 · 规模效益与技术出海双轮驱动' },
  '300308': { name: '中际旭创', board: '创业板', sector: '通信 / 光模块', desc: '全球数通光模块龙头 · 800G/1.6T 高速光互联核心供应商' },
  '002371': { name: '北方华创', board: '主板', sector: '电子 / 半导体设备', desc: '高端半导体核心装备旗舰 · 刻蚀与薄膜沉积设备平台级厂商' },
  'sh000300': { name: '沪深300', board: '核心指数', sector: 'A股核心资产代表', desc: '覆盖沪深两市市值规模大、流动性好的 300 只核心蓝筹标的' }
}

const initialCode = (route.query.code as string) || 'sh000001'
const isIndex = initialCode.startsWith('sh000') || initialCode.startsWith('sz399') || initialCode === '000001'
const preset = hotDict[initialCode] || {
  name: `标的 ${initialCode}`,
  board: initialCode.startsWith('688') ? '科创板' : initialCode.startsWith('30') ? '创业板' : '主板',
  sector: 'A股重点战略产业',
  desc: '行业领军标的 · 机构重点配置资产'
}

const defaultPrice = isIndex ? 3911.87 : 86.40

const reportStock = ref({
  code: initialCode,
  name: preset.name,
  board: preset.board,
  sector: preset.sector,
  desc: preset.desc,
  price: defaultPrice,
  targetPrice: (defaultPrice * 1.14).toFixed(2),
  stopLossPrice: (defaultPrice * 0.92).toFixed(2),
  high52: (defaultPrice * 1.18).toFixed(2),
  low52: (defaultPrice * 0.68).toFixed(2),
  marketCap: isIndex ? '99,417' : '2,840',
  circCap: isIndex ? '99,417' : '1,220',
  pe: isIndex ? '14.2' : '48.2',
  marketSymbol: initialCode.startsWith('6') ? `${initialCode}.SH` : (initialCode.startsWith('8') || initialCode.startsWith('4') || initialCode.startsWith('9')) ? `${initialCode}.BJ` : `${initialCode}.SZ`
})

const buyRange = computed(() => {
  const p = reportStock.value.price
  return `${(p * 0.98).toFixed(2)} ~ ${(p * 1.01).toFixed(2)}`
})

async function loadStockDetail(code: string) {
  if (!code) return
  const info = hotDict[code]
  let board = info?.board || '主板'
  if (!info) {
    if (code.startsWith('688')) board = '科创板'
    else if (code.startsWith('30')) board = '创业板'
    else if (code.startsWith('8') || code.startsWith('9') || code.startsWith('4')) board = '北交所'
    else if (code.startsWith('sh000') || code.startsWith('sz399')) board = '核心指数'
  }
  const symbol = code.startsWith('6') ? `${code}.SH` : (code.startsWith('8') || code.startsWith('4') || code.startsWith('9')) ? `${code}.BJ` : `${code}.SZ`

  try {
    const res = await stocksApi.getQuote(code)
    const q = (res as any)?.data || res
    if (q && (q.price !== undefined || q.close !== undefined)) {
      const px = Number(q.price ?? q.close ?? 86.4)
      const cap = q.total_mv ? (q.total_mv / 10000).toFixed(0) : (px * 32).toFixed(0)
      const circ = q.circ_mv ? (q.circ_mv / 10000).toFixed(0) : (+cap * 0.45).toFixed(0)
      reportStock.value = {
        code,
        name: q.name || info?.name || `标的 ${code}`,
        board: q.market || board,
        sector: q.industry || info?.sector || 'A股蓝筹 / 优势产业',
        desc: info?.desc || `${q.name || code} · 行业核心骨干企业与战略资产`,
        price: px,
        targetPrice: (px * 1.14).toFixed(2),
        stopLossPrice: (px * 0.92).toFixed(2),
        high52: (px * 1.18).toFixed(2),
        low52: (px * 0.68).toFixed(2),
        marketCap: Number(cap).toLocaleString(),
        circCap: Number(circ).toLocaleString(),
        pe: String(Number(q.pe || 28.5).toFixed(1)),
        marketSymbol: symbol
      }
      return
    }

    const poolRes = await stocksApi.getPool({ keyword: code, page_size: 1 })
    const item = (poolRes as any)?.data?.items?.[0]
    if (item) {
      const px = Number(item.close || 50)
      const cap = item.total_mv ? (item.total_mv / 10000).toFixed(0) : 1500
      reportStock.value = {
        code: item.code,
        name: item.name,
        board: item.market || board,
        sector: item.industry || info?.sector || 'A股优势蓝筹',
        desc: info?.desc || `${item.name} · 行业核心标的与量化优选资产`,
        price: px,
        targetPrice: (px * 1.14).toFixed(2),
        stopLossPrice: (px * 0.92).toFixed(2),
        high52: (px * 1.15).toFixed(2),
        low52: (px * 0.72).toFixed(2),
        marketCap: Number(cap).toLocaleString(),
        circCap: (Number(cap) * 0.5).toFixed(0),
        pe: String(Number(item.pe || 25.0).toFixed(1)),
        marketSymbol: symbol
      }
    }
  } catch (e) {
    console.warn('加载研报标的失败，保持预设回显:', e)
  }
}

watch(() => route.query.code, (newCode) => {
  if (newCode && typeof newCode === 'string') {
    loadStockDetail(newCode)
  }
})

onMounted(() => {
  const queryCode = (route.query.code as string) || 'sh000001'
  loadStockDetail(queryCode)
})

function handlePrint() {
  window.print()
}
</script>

<style scoped lang="scss">
.report-view {
  max-width: 1080px;
  margin: 0 auto;
  padding-bottom: 40px;
}

.report-toolbar {
  background-color: #ffffff;
  border: 1px solid #e4e7ec;
  border-radius: 6px;
  padding: 10px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;

  .tb-left {
    display: flex;
    align-items: center;
    gap: 12px;

    .report-no {
      font-size: 11px;
      color: #667085;
      background-color: #f2f4f7;
      padding: 2px 6px;
      border-radius: 3px;
    }
  }
}

.report-paper {
  background-color: #ffffff;
  border: 1px solid #d0d5dd;
  border-radius: 4px;
  box-shadow: 0 4px 20px rgba(16, 24, 40, 0.05);
  padding: 40px 48px;
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding-bottom: 20px;
  border-bottom: 2px solid #101828;

  .inst-brand {
    display: flex;
    flex-direction: column;
    gap: 4px;

    .inst-name {
      font-size: 18px;
      font-weight: 800;
      color: #101828;
      letter-spacing: -0.02em;
    }

    .inst-sub {
      font-size: 11px;
      color: #667085;
      font-weight: 500;
    }
  }

  .report-meta {
    display: flex;
    flex-direction: column;
    gap: 2px;
    font-size: 11px;

    .meta-row {
      display: flex;
      justify-content: space-between;
      gap: 8px;

      .mk { color: #98a2b3; }
      .mv { color: #344054; font-weight: 600; }
    }
  }
}

.rating-banner {
  background-color: #f8fafc;
  border: 1px solid #eaecf0;
  border-radius: 6px;
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;

  .rating-left {
    display: flex;
    flex-direction: column;
    gap: 6px;

    .stock-title-row {
      display: flex;
      align-items: center;
      gap: 10px;

      .stock-name {
        font-size: 24px;
        font-weight: 800;
        color: #101828;
        margin: 0;
      }

      .stock-code {
        font-size: 14px;
        font-weight: 600;
        color: #475467;
        background-color: #eaecf0;
        padding: 2px 6px;
        border-radius: 3px;
      }

      .badge-board {
        font-size: 11px;
        font-weight: 600;
        color: #175cd3;
        background-color: #eff8ff;
        padding: 2px 6px;
        border-radius: 3px;
      }
    }

    .stock-desc {
      font-size: 12px;
      color: #667085;
      margin: 0;
    }
  }

  .rating-right {
    display: flex;
    gap: 24px;
    border-left: 1px solid #d0d5dd;
    padding-left: 24px;

    .rating-block, .target-block, .score-block {
      display: flex;
      flex-direction: column;
      gap: 2px;

      .rating-title, .target-title, .score-title {
        font-size: 10px;
        color: #98a2b3;
        font-weight: 600;
      }

      .rating-value {
        font-size: 20px;
        font-weight: 800;
      }

      .rating-type, .target-upside, .score-desc {
        font-size: 11px;
        font-weight: 600;
      }

      .target-price {
        font-size: 18px;
        font-weight: 700;
        color: #101828;
      }

      .score-value {
        font-size: 18px;
        font-weight: 800;
        color: #175cd3;

        .max-score {
          font-size: 11px;
          color: #98a2b3;
          font-weight: 500;
        }
      }
    }
  }
}

.benchmark-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
  background-color: #fafbfc;
  border: 1px solid #eaecf0;
  border-radius: 4px;
  padding: 10px 14px;

  .bm-col {
    display: flex;
    flex-direction: column;
    gap: 2px;

    .bk {
      font-size: 10px;
      color: #98a2b3;
    }

    .bv {
      font-size: 12px;
      font-weight: 700;
      color: #101828;

      &.highlight {
        color: #175cd3;
      }
    }
  }
}

.report-section {
  display: flex;
  flex-direction: column;
  gap: 14px;

  .sec-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding-bottom: 8px;
    border-bottom: 1px solid #eaecf0;

    .sec-num {
      font-size: 14px;
      font-weight: 800;
      color: #175cd3;
      background-color: #eff8ff;
      padding: 1px 6px;
      border-radius: 3px;
    }

    .sec-title {
      font-size: 15px;
      font-weight: 700;
      color: #101828;
      margin: 0;
    }
  }

  .sec-content {
    font-size: 13px;
    color: #344054;
    line-height: 1.6;

    .summary-paragraph {
      margin: 0 0 16px 0;
    }
  }
}

.highlight-boxes {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;

  .h-box {
    background-color: #fafbfc;
    border: 1px solid #eaecf0;
    border-radius: 4px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 4px;

    &.warning {
      background-color: #fffcf5;
      border-color: #fedf89;
      .h-num { color: #b54708; }
      .h-title { color: #b54708; }
    }

    .h-num {
      font-size: 10px;
      color: #175cd3;
      font-weight: 700;
    }

    .h-title {
      font-size: 12px;
      font-weight: 700;
      color: #101828;
    }

    .h-desc {
      font-size: 11px;
      color: #667085;
      line-height: 1.4;
    }
  }
}

.factor-table-wrapper {
  overflow-x: auto;
}

.factor-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;

  th {
    padding: 8px 12px;
    background-color: #f8fafc;
    color: #475467;
    font-weight: 600;
    border-bottom: 1px solid #eaecf0;
    font-size: 11px;
  }

  td {
    padding: 10px 12px;
    border-bottom: 1px solid #f2f4f7;
    color: #101828;
  }

  .text-right { text-align: right; }
  .text-center { text-align: center; }
  .fw-bold { font-weight: 700; }
}

.evidence-block {
  margin-bottom: 16px;

  .eb-title {
    font-size: 13px;
    font-weight: 700;
    color: #101828;
    margin: 0 0 6px 0;
  }

  .eb-list {
    margin: 0;
    padding-left: 18px;
    display: flex;
    flex-direction: column;
    gap: 6px;

    li {
      font-size: 12px;
      color: #344054;
      line-height: 1.5;
    }
  }
}

.arbitration-paper-box {
  background-color: #fffaeb;
  border: 1px solid #fedf89;
  border-radius: 6px;
  padding: 14px 16px;
  margin-top: 14px;

  .apb-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;

    .apb-title {
      font-size: 13px;
      font-weight: 700;
      color: #b54708;
    }

    .apb-badge {
      font-size: 11px;
      font-weight: 700;
      color: #b54708;
      background-color: #fef0c7;
      padding: 2px 6px;
      border-radius: 3px;
    }
  }

  .apb-text {
    font-size: 12px;
    color: #713b12;
    line-height: 1.5;
    margin: 0 0 10px 0;
  }

  .action-recommendation-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    background-color: #ffffff;
    border: 1px solid #fedf89;
    border-radius: 4px;
    padding: 10px;

    .arg-item {
      display: flex;
      flex-direction: column;
      gap: 2px;

      .arg-k {
        font-size: 10px;
        color: #98a2b3;
        font-weight: 600;
      }

      .arg-v {
        font-size: 11px;
        font-weight: 600;
        color: #101828;
      }
    }
  }
}

.report-footer {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #eaecf0;
  display: flex;
  flex-direction: column;
  gap: 8px;

  .disclaimer-title {
    font-size: 11px;
    font-weight: 700;
    color: #667085;
  }

  .disclaimer-text {
    font-size: 10px;
    color: #98a2b3;
    line-height: 1.5;
    margin: 0;
  }

  .footer-sign {
    display: flex;
    justify-content: space-between;
    font-size: 10px;
    color: #98a2b3;
    margin-top: 6px;
  }
}

.color-up { color: #d92d20; }
.text-danger { color: #d92d20; }
.text-success { color: #039855; }
.tabular-nums { font-variant-numeric: tabular-nums; }
.font-mono { font-family: 'JetBrains Mono', 'Roboto Mono', monospace; }

@media print {
  .no-print {
    display: none !important;
  }
  .report-paper {
    box-shadow: none !important;
    border: none !important;
    padding: 0 !important;
  }
}
</style>
