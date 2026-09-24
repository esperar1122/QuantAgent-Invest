import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { nextTick } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import { ElMessage } from 'element-plus'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

// 配置NProgress
NProgress.configure({
  showSpinner: false,
  minimum: 0.2,
  easing: 'ease',
  speed: 500
})

// 路由配置
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/terminal/overview'
  },
  {
    path: '/terminal',
    name: 'Terminal',
    component: () => import('@/layouts/TerminalLayout.vue'),
    redirect: '/terminal/overview',
    meta: {
      title: 'QuantAgent-Invest 智能投研终端',
      requiresAuth: false
    },
    children: [
      // 投研核心
      {
        path: 'overview',
        name: 'TerminalOverview',
        component: () => import('@/views/Terminal/Overview/index.vue'),
        meta: { title: '市场总览', requiresAuth: false }
      },
      {
        path: 'dashboard',
        name: 'TerminalDashboard',
        component: () => import('@/views/Dashboard/index.vue'),
        meta: { title: '系统仪表盘', requiresAuth: true }
      },
      {
        path: 'screening',
        name: 'TerminalScreening',
        component: () => import('@/views/StockPool/index.vue'),
        meta: { title: '量化选股 (A股股票池)', requiresAuth: false }
      },
      {
        path: 'stock',
        name: 'TerminalStockResearch',
        component: () => import('@/views/Terminal/StockResearch/index.vue'),
        meta: { title: '个股与指数研究', requiresAuth: false }
      },
      {
        path: 'favorites',
        name: 'TerminalFavorites',
        component: () => import('@/views/Favorites/index.vue'),
        meta: { title: '我的自选股', requiresAuth: true }
      },
      {
        path: 'stocks/:code',
        name: 'TerminalStockDetail',
        component: () => import('@/views/Stocks/Detail.vue'),
        meta: { title: '股票详情', requiresAuth: true }
      },

      // 智能体与大模型
      {
        path: 'workflow',
        name: 'TerminalWorkflow',
        component: () => import('@/views/Terminal/Workflow/index.vue'),
        meta: { title: 'Agent 工作流', requiresAuth: false }
      },
      {
        path: 'analysis/single',
        name: 'TerminalSingleAnalysis',
        component: () => import('@/views/Analysis/SingleAnalysis.vue'),
        meta: { title: '单股深度分析 (LLM)', requiresAuth: true }
      },
      {
        path: 'analysis/batch',
        name: 'TerminalBatchAnalysis',
        component: () => import('@/views/Analysis/BatchAnalysis.vue'),
        meta: { title: '批量并发分析 (LLM)', requiresAuth: true }
      },
      {
        path: 'report',
        name: 'TerminalReport',
        component: () => import('@/views/Terminal/Report/index.vue'),
        meta: { title: '全息投研研报', requiresAuth: false }
      },
      {
        path: 'reports',
        name: 'TerminalReports',
        component: () => import('@/views/Reports/index.vue'),
        meta: { title: '分析报告库', requiresAuth: true }
      },
      {
        path: 'reports/view/:id',
        name: 'TerminalReportDetail',
        component: () => import('@/views/Reports/ReportDetail.vue'),
        meta: { title: '报告详情', requiresAuth: true }
      },

      // 任务与调度运维
      {
        path: 'tasks',
        name: 'TerminalTasks',
        component: () => import('@/views/Tasks/TaskCenter.vue'),
        meta: { title: '任务中心', requiresAuth: true }
      },
      {
        path: 'system/sync',
        name: 'TerminalMultiSourceSync',
        component: () => import('@/views/System/MultiSourceSync.vue'),
        meta: { title: '多数据源同步', requiresAuth: true }
      },

      // 系统管理与设置
      {
        path: 'settings',
        redirect: '/terminal/settings/config'
      },
      {
        path: 'settings/config',
        name: 'TerminalConfigManagement',
        component: () => import('@/views/Settings/ConfigManagement.vue'),
        meta: { title: '配置管理', requiresAuth: true }
      },
      {
        path: 'settings/database',
        name: 'TerminalDatabaseManagement',
        component: () => import('@/views/System/DatabaseManagement.vue'),
        meta: { title: '数据库管理', requiresAuth: true }
      },
      {
        path: 'settings/logs',
        name: 'TerminalOperationLogs',
        component: () => import('@/views/System/OperationLogs.vue'),
        meta: { title: '操作日志', requiresAuth: true }
      },
      {
        path: 'settings/system-logs',
        name: 'TerminalLogManagement',
        component: () => import('@/views/System/LogManagement.vue'),
        meta: { title: '系统日志', requiresAuth: true }
      },
      {
        path: 'settings/cache',
        name: 'TerminalCacheManagement',
        component: () => import('@/views/Settings/CacheManagement.vue'),
        meta: { title: '缓存管理', requiresAuth: true }
      },
      {
        path: 'settings/usage',
        name: 'TerminalUsageStatistics',
        component: () => import('@/views/Settings/UsageStatistics.vue'),
        meta: { title: '使用统计', requiresAuth: true }
      },
      {
        path: 'settings/scheduler',
        name: 'TerminalSchedulerManagement',
        component: () => import('@/views/System/SchedulerManagement.vue'),
        meta: { title: '定时任务', requiresAuth: true }
      }
    ]
  },

  // 传统路由兼容平滑重定向
  { path: '/dashboard', redirect: '/terminal/dashboard' },
  { path: '/analysis', redirect: '/terminal/analysis/single' },
  { path: '/analysis/single', redirect: '/terminal/analysis/single' },
  { path: '/analysis/batch', redirect: '/terminal/analysis/batch' },
  { path: '/screening', redirect: '/terminal/screening' },
  { path: '/stock-pool', redirect: '/terminal/screening' },
  { path: '/favorites', redirect: '/terminal/favorites' },
  { path: '/stocks/:code', redirect: to => `/terminal/stocks/${to.params.code}` },
  { path: '/tasks', redirect: '/terminal/tasks' },
  { path: '/queue', redirect: '/terminal/tasks' },
  { path: '/reports', redirect: '/terminal/reports' },
  { path: '/reports/view/:id', redirect: to => `/terminal/reports/view/${to.params.id}` },
  { path: '/settings', redirect: '/terminal/settings/config' },
  { path: '/settings/config', redirect: '/terminal/settings/config' },
  { path: '/settings/database', redirect: '/terminal/settings/database' },
  { path: '/settings/logs', redirect: '/terminal/settings/logs' },
  { path: '/settings/system-logs', redirect: '/terminal/settings/system-logs' },
  { path: '/settings/sync', redirect: '/terminal/system/sync' },
  { path: '/settings/cache', redirect: '/terminal/settings/cache' },
  { path: '/settings/usage', redirect: '/terminal/settings/usage' },
  { path: '/settings/scheduler', redirect: '/terminal/settings/scheduler' },

  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Auth/Login.vue'),
    meta: {
      title: '登录',
      hideInMenu: true,
      transition: 'fade'
    }
  },

  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/Error/404.vue'),
    meta: {
      title: '页面不存在',
      hideInMenu: true,
      requiresAuth: true
    }
  }
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(_to, _from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 全局前置守卫
router.beforeEach(async (to, _from, next) => {
  // 开始进度条
  NProgress.start()

  const authStore = useAuthStore()
  const appStore = useAppStore()

  // 设置页面标题
  const title = to.meta.title as string
  if (title) {
    document.title = `${title} - QuantAgent-Invest`
  }

  console.log('🚦 路由守卫检查:', {
    path: to.fullPath,
    name: to.name,
    requiresAuth: to.meta.requiresAuth,
    isAuthenticated: authStore.isAuthenticated,
    hasToken: !!authStore.token
  })

  // 检查是否需要认证
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    console.log('🔒 需要认证但用户未登录:', {
      path: to.fullPath,
      requiresAuth: to.meta.requiresAuth,
      isAuthenticated: authStore.isAuthenticated,
      token: authStore.token ? '存在' : '不存在'
    })
    // 保存原始路径，登录后跳转
    authStore.setRedirectPath(to.fullPath)
    next('/login')
    return
  }



  // 如果已登录且访问登录页，重定向到终端市场总览
  if (authStore.isAuthenticated && to.name === 'Login') {
    next('/terminal/overview')
    return
  }

  // 更新当前路由信息
  appStore.setCurrentRoute(to)

  next()
})

// 全局后置守卫
router.afterEach((_to, _from) => {
  // 结束进度条
  NProgress.done()

  // 页面切换后的处理
  nextTick(() => {
    // 可以在这里添加页面分析、埋点等逻辑
  })
})

// 路由错误处理
router.onError((error) => {
  console.error('路由错误:', error)
  NProgress.done()
  ElMessage.error('页面加载失败，请重试')
})

export default router

// 导出路由配置供其他地方使用
export { routes }
