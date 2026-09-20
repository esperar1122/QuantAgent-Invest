import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { favoritesApi, type FavoriteItem, type AddFavoriteReq } from '@/api/favorites'

export const useFavoritesStore = defineStore('favorites', () => {
  const favorites = ref<FavoriteItem[]>([])
  const tags = ref<string[]>([])
  const loading = ref(false)
  const initialized = ref(false)

  // 响应式集合，快速判断是否已收藏
  const favoriteCodes = computed(() => {
    const set = new Set<string>()
    favorites.value.forEach(item => {
      const code = item.symbol || item.stock_code
      if (code) set.add(code)
    })
    return set
  })

  const isFavorite = (code: string): boolean => {
    if (!code) return false
    return favoriteCodes.value.has(code)
  }

  // 加载自选股列表
  const fetchFavorites = async (force = false) => {
    if (initialized.value && !force && favorites.value.length > 0) {
      return favorites.value
    }
    loading.value = true
    try {
      const res = await favoritesApi.list()
      const data = (res as any)?.data || res || []
      favorites.value = Array.isArray(data) ? data : []
      initialized.value = true
      return favorites.value
    } catch (err) {
      console.warn('获取自选股列表失败:', err)
      return []
    } finally {
      loading.value = false
    }
  }

  // 加载标签列表
  const fetchTags = async () => {
    try {
      const res = await favoritesApi.tags()
      const data = (res as any)?.data || res || []
      tags.value = Array.isArray(data) ? data : []
      return tags.value
    } catch (err) {
      console.warn('获取自选股标签失败:', err)
      return []
    }
  }

  // 添加自选股
  const addFavorite = async (payload: AddFavoriteReq) => {
    const code = payload.symbol || payload.stock_code
    if (!code) throw new Error('股票代码不能为空')

    const res = await favoritesApi.add(payload)
    // 本地乐观更新或推入列表
    const exists = favorites.value.some(f => (f.symbol || f.stock_code) === code)
    if (!exists) {
      favorites.value.push({
        symbol: code,
        stock_code: code,
        stock_name: payload.stock_name,
        market: payload.market || 'A股',
        tags: payload.tags || [],
        notes: payload.notes || ''
      })
    }
    return res
  }

  // 移出自选股
  const removeFavorite = async (code: string) => {
    if (!code) return
    const res = await favoritesApi.remove(code)
    favorites.value = favorites.value.filter(f => (f.symbol || f.stock_code) !== code)
    return res
  }

  // 切换自选状态
  const toggleFavorite = async (stock: { code: string; name: string; market?: string }) => {
    const code = stock.code
    try {
      if (isFavorite(code)) {
        await removeFavorite(code)
        ElMessage.success(`已取消自选：${stock.name}(${code})`)
        return false
      } else {
        await addFavorite({
          symbol: code,
          stock_code: code,
          stock_name: stock.name || code,
          market: stock.market || 'A股'
        })
        ElMessage.success(`已加入自选：${stock.name}(${code})`)
        return true
      }
    } catch (err: any) {
      ElMessage.error(err.message || '更新自选状态失败')
      throw err
    }
  }

  return {
    favorites,
    tags,
    loading,
    initialized,
    favoriteCodes,
    isFavorite,
    fetchFavorites,
    fetchTags,
    addFavorite,
    removeFavorite,
    toggleFavorite
  }
})
