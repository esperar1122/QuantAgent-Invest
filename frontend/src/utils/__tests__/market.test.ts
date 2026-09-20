import { describe, it, expect } from 'vitest'
import { getMarketByStockCode } from '../market'

describe('getMarketByStockCode', () => {
  describe('A股个股识别', () => {
    it('应该识别6位个股代码为A股', () => {
      expect(getMarketByStockCode('600519')).toBe('A股')
      expect(getMarketByStockCode('300750')).toBe('A股')
      expect(getMarketByStockCode('688981')).toBe('A股')
    })
  })

  describe('指数识别', () => {
    it('应该识别常见核心指数', () => {
      expect(getMarketByStockCode('000300')).toBe('指数')
      expect(getMarketByStockCode('399001')).toBe('指数')
      expect(getMarketByStockCode('399006')).toBe('指数')
      expect(getMarketByStockCode('000688')).toBe('指数')
    })
  })

  describe('边界情况', () => {
    it('应该处理空字符串', () => {
      expect(getMarketByStockCode('')).toBe('A股')
    })
  })
})

