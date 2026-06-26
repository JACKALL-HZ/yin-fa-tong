import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAppStore = defineStore('app', () => {
  /** 界面模式: 'elder' 长者极简 | 'normal' 子女标准 */
  const mode = ref<'elder' | 'normal'>(
    (localStorage.getItem('app_mode') as 'elder' | 'normal') || 'normal'
  )
  const isElderMode = computed(() => mode.value === 'elder')

  function toggleMode() {
    mode.value = mode.value === 'elder' ? 'normal' : 'elder'
    localStorage.setItem('app_mode', mode.value)
  }

  function setMode(m: 'elder' | 'normal') {
    mode.value = m
    localStorage.setItem('app_mode', m)
  }

  return { mode, isElderMode, toggleMode, setMode }
})
