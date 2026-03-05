<template>
  <div class="settings">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>系统设置</span>
        </div>
      </template>

      <el-form :model="form" label-width="160px">
        <el-divider content-position="left">Tushare</el-divider>
        <el-form-item label="Tushare Token">
          <el-input v-model="form.tushare_token" type="password" placeholder="请输入 Tushare Token" />
          <div class="form-tip">获取地址: https://tushare.pro</div>
        </el-form-item>

        <el-divider content-position="left">钉钉通知</el-divider>
        <el-form-item label="Webhook">
          <el-input v-model="form.dingtalk_webhook" placeholder="钉钉机器人 Webhook 地址" />
        </el-form-item>
        <el-form-item label="Secret">
          <el-input v-model="form.dingtalk_secret" type="password" placeholder="加签密钥（可选）" />
        </el-form-item>
        <el-form-item>
          <el-button @click="testNotification">测试通知</el-button>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="saveSettings" :loading="saving">保存设置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { notifyApi } from '@/api'

const saving = ref(false)

const form = ref({
  tushare_token: '',
  dingtalk_webhook: '',
  dingtalk_secret: ''
})

const loadSettings = async () => {
  try {
    const res = await notifyApi.getSettings()
  } catch (e) {
    console.error(e)
  }
}

const saveSettings = async () => {
  saving.value = true
  try {
    await notifyApi.updateSettings(form.value)
    ElMessage.success('设置已保存（请重启后端生效）')
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const testNotification = async () => {
  try {
    await notifyApi.test({
      title: '测试通知',
      text: '这是一条测试消息，来自 Quant Trader'
    })
    ElMessage.success('测试消息已发送')
  } catch (e) {
    ElMessage.error('发送失败，请检查配置')
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings {
  max-width: 800px;
  margin: 0 auto;
}

.card-header {
  font-weight: 600;
}

.form-tip {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}
</style>
