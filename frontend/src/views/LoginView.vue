<script setup>
import { ref, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref('')
const password = ref('')
const error = ref('')
const mode = ref('login')

// 忘记密码
const showForgot = ref(false)
const forgotEmail = ref('')
const forgotCode = ref('')
const newPassword = ref('')
const codeSent = ref(false)
const sending = ref(false)
const resetting = ref(false)
const cooldown = ref(0)
const forgotMsg = ref('')
const forgotError = ref('')
let forgotTimer = null

async function submit() {
  error.value = ''
  const res = await fetch(`/api/${mode.value}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: username.value, password: password.value }),
  })
  const data = await res.json()
  if (!res.ok) {
    error.value = data.error || '出错了'
    return
  }
  localStorage.setItem('token', data.token)
  localStorage.setItem('username', data.username)
  router.push('/')
}

function openForgot() {
  showForgot.value = true
  forgotEmail.value = ''
  forgotCode.value = ''
  newPassword.value = ''
  codeSent.value = false
  forgotMsg.value = ''
  forgotError.value = ''
}

async function sendForgotCode() {
  if (sending.value || cooldown.value > 0) return
  if (!forgotEmail.value.trim()) {
    forgotError.value = '请输入邮箱'
    return
  }
  sending.value = true
  forgotMsg.value = ''
  forgotError.value = ''
  const res = await fetch('/api/password/forgot', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: forgotEmail.value.trim() }),
  })
  const data = await res.json()
  sending.value = false
  if (res.ok) {
    codeSent.value = true
    forgotCode.value = ''
    newPassword.value = ''
    forgotMsg.value = '验证码已发送，请查收邮件'
    cooldown.value = 60
    forgotTimer = setInterval(() => {
      cooldown.value -= 1
      if (cooldown.value <= 0) clearInterval(forgotTimer)
    }, 1000)
  } else {
    forgotError.value = data.error || '发送失败'
  }
}

async function resetPassword() {
  if (!forgotCode.value.trim()) {
    forgotError.value = '请输入验证码'
    return
  }
  if (!newPassword.value) {
    forgotError.value = '请输入新密码'
    return
  }
  resetting.value = true
  forgotMsg.value = ''
  forgotError.value = ''
  const res = await fetch('/api/password/reset', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: forgotEmail.value.trim(),
      code: forgotCode.value.trim(),
      new_password: newPassword.value,
    }),
  })
  const data = await res.json()
  resetting.value = false
  if (res.ok) {
    forgotMsg.value = '密码重置成功，请用新密码登录'
    codeSent.value = false
    forgotCode.value = ''
    newPassword.value = ''
  } else {
    forgotError.value = data.error || '重置失败'
  }
}

onUnmounted(() => {
  if (forgotTimer) clearInterval(forgotTimer)
})
</script>

<template>
  <div class="page">
    <div class="card">
      <div class="logo">问卷系统</div>
      <p class="subtitle">创建问卷 · 收集反馈 · 查看结果</p>

      <div class="tabs">
        <button :class="{ active: mode === 'login' }" @click="mode = 'login'">登录</button>
        <button :class="{ active: mode === 'register' }" @click="mode = 'register'">注册</button>
      </div>

      <div class="fields">
        <input v-model="username" placeholder="用户名" />
        <input v-model="password" type="password" placeholder="密码" @keyup.enter="submit" />
      </div>

      <p v-if="error" class="error">{{ error }}</p>

      <button class="submit" @click="submit">{{ mode === 'login' ? '登录' : '注册' }}</button>

      <div v-if="mode === 'login'" class="forgot-link" @click="openForgot">忘记密码？</div>
    </div>

    <div v-if="showForgot" class="mask" @click.self="showForgot = false">
      <div class="modal">
        <h3>重置密码</h3>
        <p class="modal-desc">通过你绑定的邮箱重置密码</p>

        <div class="field">
          <label>邮箱</label>
          <div class="row">
            <input v-model="forgotEmail" placeholder="输入绑定的邮箱" />
            <button class="code-btn" :disabled="sending || cooldown > 0" @click="sendForgotCode">
              {{ sending ? '发送中...' : cooldown > 0 ? cooldown + 's' : '发送验证码' }}
            </button>
          </div>
        </div>

        <div v-if="codeSent" class="field">
          <label>验证码</label>
          <input v-model="forgotCode" placeholder="输入邮件中的 6 位验证码" />
        </div>

        <div v-if="codeSent" class="field">
          <label>新密码</label>
          <input v-model="newPassword" type="password" placeholder="设置新密码" />
        </div>

        <p v-if="forgotError" class="msg error">{{ forgotError }}</p>
        <p v-if="forgotMsg" class="msg ok">{{ forgotMsg }}</p>

        <div class="modal-actions">
          <button class="ghost" @click="showForgot = false">关闭</button>
          <button v-if="codeSent" class="primary" :disabled="resetting" @click="resetPassword">
            {{ resetting ? '重置中...' : '重置密码' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: linear-gradient(135deg, #eef2ff 0%, #faf5ff 50%, #fdf2f8 100%);
}

.card {
  width: 100%;
  max-width: 400px;
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(99, 102, 241, 0.15);
  padding: 40px 32px;
  text-align: center;
}

.logo {
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.subtitle {
  color: #94a3b8;
  font-size: 13px;
  margin: 8px 0 28px;
}

.tabs {
  display: flex;
  background: #f1f5f9;
  border-radius: 12px;
  padding: 4px;
  margin-bottom: 24px;
}

.tabs button {
  flex: 1;
  padding: 10px;
  border: none;
  background: transparent;
  color: #64748b;
  font-size: 14px;
  border-radius: 9px;
  cursor: pointer;
  transition: all 0.2s;
}

.tabs button.active {
  background: #fff;
  color: #6366f1;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.fields {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.fields input {
  padding: 13px 16px;
  font-size: 15px;
  border: 1px solid var(--border);
  border-radius: 12px;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.fields input:focus {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
}

.error {
  color: #ef4444;
  font-size: 13px;
  margin: 10px 0 0;
  text-align: left;
}

.submit {
  width: 100%;
  margin-top: 20px;
  padding: 13px;
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.1s;
}

.submit:hover {
  opacity: 0.9;
}

.submit:active {
  transform: scale(0.98);
}

.forgot-link {
  margin-top: 18px;
  font-size: 13px;
  color: #6366f1;
  cursor: pointer;
}

.forgot-link:hover {
  text-decoration: underline;
}

.mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  z-index: 200;
}

.modal {
  width: 100%;
  max-width: 420px;
  background: #fff;
  border-radius: 20px;
  padding: 28px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.modal h3 {
  margin: 0 0 6px;
  font-size: 20px;
}

.modal-desc {
  color: var(--muted);
  font-size: 13px;
  margin: 0 0 24px;
}

.field {
  margin-bottom: 16px;
  text-align: left;
}

.field label {
  display: block;
  font-size: 13px;
  color: var(--muted);
  margin-bottom: 6px;
}

.field input {
  width: 100%;
  padding: 11px 14px;
  font-size: 14px;
  border: 1px solid var(--border);
  border-radius: 10px;
  outline: none;
  box-sizing: border-box;
}

.field input:focus {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12);
}

.row {
  display: flex;
  gap: 10px;
}

.row input {
  flex: 1;
}

.code-btn {
  flex-shrink: 0;
  padding: 0 16px;
  font-size: 13px;
  color: #6366f1;
  border: 1px solid #6366f1;
  background: #fff;
  border-radius: 10px;
  cursor: pointer;
  white-space: nowrap;
}

.code-btn:hover {
  background: rgba(99, 102, 241, 0.06);
}

.code-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.msg {
  font-size: 13px;
  margin: 0 0 12px;
  text-align: left;
}

.msg.error {
  color: #ef4444;
}

.msg.ok {
  color: #059669;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.ghost {
  padding: 10px 18px;
  font-size: 14px;
  border: 1px solid var(--border);
  background: #fff;
  color: var(--muted);
  border-radius: 10px;
  cursor: pointer;
}

.ghost:hover {
  border-color: #6366f1;
  color: #6366f1;
}

.primary {
  padding: 10px 22px;
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  border-radius: 10px;
  cursor: pointer;
}

.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
