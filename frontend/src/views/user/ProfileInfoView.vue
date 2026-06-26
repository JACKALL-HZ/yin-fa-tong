<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { userApi } from '@/api/user'
import { ElMessage } from 'element-plus'
import type { ProfileUpdate } from '@/types'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const saving = ref(false)

const form = ref<ProfileUpdate>({
  real_name: '',
  gender: 1,
  id_card: '',
  birthday: '',
  phone: '',
})

const isEdit = computed(() => !!userStore.info?.real_name)

// 从身份证号自动提取出生日期
function extractBirthday(idCard: string) {
  if (idCard.length === 18) {
    const year = idCard.substring(6, 10)
    const month = idCard.substring(10, 12)
    const day = idCard.substring(12, 14)
    form.value.birthday = `${year}-${month}-${day}`
  }
}

// 身份证号校验
function validateIdCard(rule: any, value: string, callback: any) {
  if (!value) return callback(new Error('请输入身份证号'))
  if (!/^\d{17}[\dXx]$/.test(value)) return callback(new Error('身份证号应为18位'))
  callback()
}

const rules = {
  real_name: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  gender: [{ required: true, message: '请选择性别', trigger: 'change' }],
  id_card: [{ required: true, validator: validateIdCard, trigger: 'blur' }],
  birthday: [{ required: true, message: '请选择出生日期', trigger: 'change' }],
}

onMounted(async () => {
  loading.value = true
  try {
    // 加载当前用户信息
    await userStore.fetchMe()
    const info = userStore.info
    if (info?.real_name) {
      form.value = {
        real_name: info.real_name || '',
        gender: info.gender || 1,
        id_card: info.id_card || '',
        birthday: info.birthday || '',
        phone: info.phone || '',
      }
    }
  } finally {
    loading.value = false
  }
})

async function handleSubmit() {
  saving.value = true
  try {
    const payload: any = { ...form.value }
    if (!payload.birthday) delete payload.birthday
    if (!payload.phone) delete payload.phone
    const { data: result } = await userApi.updateProfile(payload)
    if (result.code === 200) {
      await userStore.fetchMe()
      ElMessage.success(isEdit.value ? '信息已更新' : '信息登记完成')
      router.back()
    } else {
      ElMessage.error(result.message || '保存失败')
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="page-wrap" v-loading="loading">
    <div class="sec-head">
      <span class="sec-head-zh">信息登记</span>
      <span class="sec-head-en">Profile Registration</span>
    </div>

    <div class="card">
      <p class="tip">
        {{ isEdit ? '您可以修改个人信息' : '请填写您的个人信息，便于预约挂号时自动填充' }}
      </p>

      <el-form :model="form" :rules="rules" label-position="top" size="large">
        <el-form-item label="真实姓名" prop="real_name">
          <el-input v-model="form.real_name" placeholder="请输入真实姓名" maxlength="32" />
        </el-form-item>

        <el-form-item label="性别" prop="gender">
          <el-radio-group v-model="form.gender">
            <el-radio :value="1">男</el-radio>
            <el-radio :value="2">女</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="身份证号" prop="id_card">
          <el-input
            v-model="form.id_card"
            placeholder="请输入18位身份证号"
            maxlength="18"
            @blur="extractBirthday(form.id_card)"
          />
        </el-form-item>

        <el-form-item label="出生日期" prop="birthday">
          <el-date-picker
            v-model="form.birthday"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择出生日期（可从身份证号自动提取）"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="联系电话（选填）">
          <el-input v-model="form.phone" placeholder="请输入手机号" maxlength="20" />
        </el-form-item>

        <el-button
          type="primary"
          size="large"
          :loading="saving"
          @click="handleSubmit"
          style="width: 100%; height: 56px; font-size: 18px; font-weight: 700; border-radius: var(--r-pill); margin-top: 8px"
        >
          {{ isEdit ? '保存修改' : '完成登记' }}
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.page-wrap { max-width: 720px; margin: 0 auto; padding: 32px 32px 80px; }
.tip { color: var(--c-ink-500); font-size: 15px; margin-bottom: 24px; line-height: 1.6; }
</style>
