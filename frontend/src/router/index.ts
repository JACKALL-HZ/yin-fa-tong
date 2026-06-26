import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/LoginView.vue'),
    meta: { title: '登录', guest: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/login/RegisterView.vue'),
    meta: { title: '注册', guest: true },
  },
  {
    path: '/auth/callback',
    name: 'AuthCallback',
    component: () => import('@/views/login/AuthCallback.vue'),
    meta: { title: '支付宝登录', guest: true },
  },
  {
    path: '/',
    component: () => import('@/components/layout/AppLayout.vue'),
    redirect: '/home',
    children: [
      { path: 'home', name: 'Home', component: () => import('@/views/home/HomeView.vue'), meta: { title: '首页' } },
      // P0 核心
      { path: 'hospitals', name: 'Hospitals', component: () => import('@/views/hospital/HospitalList.vue'), meta: { title: '选择医院' } },
      { path: 'hospitals/:hid/departments', name: 'Departments', component: () => import('@/views/department/DeptList.vue'), meta: { title: '选择科室' } },
      { path: 'departments/:did/doctors', name: 'Doctors', component: () => import('@/views/doctor/DoctorList.vue'), meta: { title: '选择医生' } },
      { path: 'doctors/:did/schedules', name: 'Schedules', component: () => import('@/views/schedule/ScheduleList.vue'), meta: { title: '选择号源' } },
      { path: 'reserve', name: 'Reserve', component: () => import('@/views/reserve/ReserveView.vue'), meta: { title: '确认预约' } },
      { path: 'orders', name: 'Orders', component: () => import('@/views/reserve/OrderList.vue'), meta: { title: '我的挂号' } },
      { path: 'reserve-result', name: 'ReserveResult', component: () => import('@/views/reserve/ReserveResult.vue'), meta: { title: '预约结果' } },
      { path: 'payment', name: 'PendingPayment', component: () => import('@/views/payment/PendingPayment.vue'), meta: { title: '在线缴费' } },
      { path: 'payment/confirm', name: 'Payment', component: () => import('@/views/payment/PaymentView.vue'), meta: { title: '确认支付' } },
      { path: 'pay-result', name: 'PayResult', component: () => import('@/views/payment/PayResult.vue'), meta: { title: '支付结果' } },
      { path: 'profile-info', name: 'ProfileInfo', component: () => import('@/views/user/ProfileInfoView.vue'), meta: { title: '信息登记' } },
      { path: 'queue', name: 'Queue', component: () => import('@/views/queue/QueueView.vue'), meta: { title: '候诊排队' } },
      // P1/P2 增强
      { path: 'guide', name: 'Guide', component: () => import('@/views/guide/GuideView.vue'), meta: { title: '智能导诊' } },
      { path: 'reminders', name: 'Reminders', component: () => import('@/views/reminder/ReminderList.vue'), meta: { title: '健康提醒' } },
      { path: 'volunteers', name: 'Volunteers', component: () => import('@/views/accompany/VolunteerList.vue'), meta: { title: '陪诊志愿者' } },
      { path: 'volunteers/:vid', name: 'VolunteerDetail', component: () => import('@/views/accompany/VolunteerDetail.vue'), meta: { title: '志愿者详情' } },
      { path: 'accompany-orders', name: 'AccompanyOrders', component: () => import('@/views/accompany/AccompanyOrders.vue'), meta: { title: '我的陪诊' } },
      { path: 'reports', name: 'Reports', component: () => import('@/views/report/ReportList.vue'), meta: { title: '体检报告' } },
      { path: 'reports/upload', name: 'ReportUpload', component: () => import('@/views/report/ReportUpload.vue'), meta: { title: '上传报告' } },
      { path: 'reports/:id', name: 'ReportDetail', component: () => import('@/views/report/ReportDetailView.vue'), meta: { title: '报告详情' } },
      // 通用
      { path: 'elders', name: 'Elders', component: () => import('@/views/user/ElderList.vue'), meta: { title: '长辈管理' } },
      { path: 'messages', name: 'Messages', component: () => import('@/views/message/MessageList.vue'), meta: { title: '消息中心' } },
      { path: 'profile', name: 'Profile', component: () => import('@/views/user/ProfileView.vue'), meta: { title: '个人中心' } },
    ],
  },
  // 后台管理
  {
    path: '/admin',
    component: () => import('@/components/layout/AdminLayout.vue'),
    meta: { admin: true },
    redirect: '/admin/dashboard',
    children: [
      { path: 'dashboard', name: 'AdminDashboard', component: () => import('@/views/admin/DashboardView.vue'), meta: { title: '数据看板' } },
      { path: 'hospitals', name: 'AdminHospitals', component: () => import('@/views/admin/HospitalManage.vue'), meta: { title: '医院管理' } },
      { path: 'departments', name: 'AdminDepts', component: () => import('@/views/admin/DeptManage.vue'), meta: { title: '科室管理' } },
      { path: 'doctors', name: 'AdminDoctors', component: () => import('@/views/admin/DoctorManage.vue'), meta: { title: '医生管理' } },
      { path: 'schedules', name: 'AdminSchedules', component: () => import('@/views/admin/ScheduleManage.vue'), meta: { title: '排班管理' } },
      { path: 'volunteers', name: 'AdminVolunteers', component: () => import('@/views/admin/VolunteerManage.vue'), meta: { title: '志愿者管理' } },
      { path: 'reserves', name: 'AdminReserves', component: () => import('@/views/admin/ReserveManage.vue'), meta: { title: '挂号管理' } },
      { path: 'accompany', name: 'AdminAccompany', component: () => import('@/views/admin/AccompanyManage.vue'), meta: { title: '陪诊管理' } },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

// 路由守卫
router.beforeEach((to, _from, next) => {
  document.title = (to.meta.title as string) ? `${to.meta.title} - 银发通` : '银发通'
  const token = localStorage.getItem('token')

  if (to.meta.guest) {
    // 登录页：已登录则跳首页
    if (token) return next('/home')
    return next()
  }

  if (!token) return next('/login')

  // 后台鉴权
  if (to.meta.admin) {
    const userType = localStorage.getItem('user_type')
    if (userType !== '3') {
      // 非管理员
      return next('/home')
    }
  }

  next()
})

export default router
