/**
 * 股票与指数代码格式验证工具（QuantAgent-Invest）
 * 专注于中国A股（主板/创业板/科创板/北交所）与核心指数
 */

export interface StockValidationResult {
  valid: boolean
  market?: 'A股' | '指数'
  message?: string
  normalizedCode?: string
}

/**
 * A股/指数代码格式验证
 * 格式：6位数字
 * - 60xxxx: 上海主板
 * - 68xxxx: 科创板
 * - 00xxxx: 深圳主板 / 上证系列指数 (000001上证指数, 000300沪深300等)
 * - 30xxxx: 创业板
 * - 39xxxx: 深证系列指数 (399001深证成指, 399006创业板指等)
 * - 43xxxx/83xxxx/87xxxx: 北交所
 */
export function validateAStock(code: string): StockValidationResult {
  const cleanCode = code.trim().replace(/[^0-9]/g, '')

  if (!/^\d{6}$/.test(cleanCode)) {
    return {
      valid: false,
      message: '代码必须是6位数字'
    }
  }

  const prefix = cleanCode.substring(0, 2)
  const validPrefixes = ['60', '68', '00', '30', '39', '43', '83', '87']

  if (!validPrefixes.includes(prefix)) {
    return {
      valid: false,
      message: '代码前缀不正确（支持：60/68/00/30/39/43/83/87开头）'
    }
  }

  const isIndex = cleanCode.startsWith('39') || ['000001', '000300', '000905', '000852', '000688', '000680'].includes(cleanCode)

  return {
    valid: true,
    market: isIndex ? '指数' : 'A股',
    normalizedCode: cleanCode
  }
}

/**
 * 自动识别代码并验证
 */
export function validateStockCode(
  code: string,
  _marketHint?: string
): StockValidationResult {
  if (!code || !code.trim()) {
    return {
      valid: false,
      message: '请输入股票或指数代码'
    }
  }
  return validateAStock(code)
}

/**
 * 获取股票代码格式说明
 */
export function getStockCodeFormatHelp(market?: string): string {
  if (market === '指数') {
    return '6位数字，如：000300（沪深300）、399001（深证成指）'
  }
  return '6位数字，如：600519（贵州茅台）、000001（平安银行）'
}

/**
 * 获取代码示例
 */
export function getStockCodeExamples(market?: string): string[] {
  if (market === '指数') {
    return ['000300', '000001', '399001', '399006', '000688']
  }
  return ['600519', '000001', '000858', '300750', '688981']
}

/**
 * 格式化股票代码显示
 */
export function formatStockCode(code: string, market?: string): string {
  const validation = validateStockCode(code, market)
  return validation.normalizedCode || code
}

