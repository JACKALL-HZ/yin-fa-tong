import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import type { UserInfo } from '@/types'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const info = ref<UserInfo | null>(null)
  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => info.value?.user_type === 3)
  const profileComplete = computed(() => info.value?.profile_complete ?? false)

  async function login(username: string, password: string) {
    const res = await authApi.login({ username, password })
    token.value = res.data.data.access_token
    localStorage.setItem('token', token.value)
    await fetchMe()
  }

  async function register(username: string, password: string, nickname?: string, user_type = 1, admin_code?: string) {
    await authApi.register({ username, password, nickname, user_type, admin_code })
  }

  async function alipayLogin(authCode: string) {
    const res = await authApi.alipayLogin(authCode)
    if (res.data?.code === 200 && res.data.data) {
      const d = res.data.data
      token.value = d.access_token
      localStorage.setItem('token', d.access_token)
      localStorage.setItem('user_type', String(d.user_type))
      await fetchMe()
    }
    return res
  }

  async function fetchMe() {
    const res = await authApi.getMe()
    info.value = res.data.data
    if (!info.value) throw new Error('获取用户信息失败')
    localStorage.setItem('user_type', String(info.value.user_type))
  }

  function logout() {
    token.value = ''
    info.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user_type')
  }

  return { token, info, isLoggedIn, isAdmin, profileComplete, login, register, alipayLogin, fetchMe, logout }
})
