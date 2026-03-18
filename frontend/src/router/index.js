import { createRouter, createWebHistory } from 'vue-router'
import { isAuthenticated } from '@/store/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/dashboard'
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue')
      },
      {
        path: 'data-sources',
        name: 'DataSourceList',
        component: () => import('@/views/DataSourceList.vue')
      },
      {
        path: 'elt-tasks',
        name: 'ELTTaskList',
        component: () => import('@/views/ELTTaskList.vue')
      },
      {
        path: 'elt-tasks/create',
        name: 'ELTConfig',
        component: () => import('@/views/ELTConfig.vue')
      },
      {
        path: 'elt-tasks/:id/edit',
        name: 'ELTEdit',
        component: () => import('@/views/ELTConfig.vue')
      },
      {
        path: 'schedules',
        name: 'ScheduleList',
        component: () => import('@/views/ScheduleList.vue')
      },
      {
        path: 'schedules/create',
        name: 'ScheduleCreate',
        component: () => import('@/views/ScheduleCreate.vue')
      },
      {
        path: 'schedules/:id/edit',
        name: 'ScheduleEdit',
        component: () => import('@/views/ScheduleCreate.vue')
      },
      {
        path: 'workflows',
        name: 'WorkflowList',
        component: () => import('@/views/WorkflowList.vue')
      },
      {
        path: 'workflows/create',
        name: 'WorkflowCreate',
        component: () => import('@/views/WorkflowEditor.vue')
      },
      {
        path: 'workflows/:id/edit',
        name: 'WorkflowEdit',
        component: () => import('@/views/WorkflowEditor.vue')
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard - 直接使用导出的 isAuthenticated
router.beforeEach((to, from, next) => {
  // isAuthenticated 是 computed ref，需要用 .value 访问
  const authenticated = isAuthenticated.value

  if (to.meta.requiresAuth && !authenticated) {
    // 需要登录但未登录，跳转到登录页
    next({ path: '/login', query: { redirect: to.fullPath } })
  } else if ((to.path === '/login' || to.path === '/register') && authenticated) {
    // 已登录访问登录/注册页，跳转到首页
    next('/dashboard')
  } else {
    next()
  }
})

export default router