<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user.js'

const router = useRouter()
const user = useUserStore()
const username = ref('')
const password = ref('')
const error = ref('')
const mode = ref('login')
const rememberUser = ref(false)
const rememberPwd = ref(false)

const usernameError = ref('')
const passwordError = ref('')

const USERNAME_RE = /^[一-龥A-Za-z0-9]{2,20}$/

function usernameRule(v) {
  const s = (v || '').trim()
  if (!USERNAME_RE.test(s)) return '用户名需为 2-20 个汉字、字母或数字'
  return ''
}

function passwordRule(v) {
  const s = v || ''
  if (s.length < 6 || s.length > 32) return '密码需为 6-32 个字符'
  if (!/[A-Za-z]/.test(s) || !/\d/.test(s)) return '密码需同时包含字母和数字'
  return ''
}

watch(username, (v) => {
  if (mode.value !== 'register') return
  usernameError.value = v.trim() ? usernameRule(v) : ''
})

watch(password, (v) => {
  if (mode.value !== 'register') return
  passwordError.value = v ? passwordRule(v) : ''
})

watch(mode, () => {
  usernameError.value = ''
  passwordError.value = ''
  error.value = ''
})

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
const forgotPwdError = ref('')
let forgotTimer = null

watch(newPassword, (v) => {
  forgotPwdError.value = v ? passwordRule(v) : ''
})

function saveRemember() {
  localStorage.setItem('remember_user', rememberUser.value ? '1' : '0')
  localStorage.setItem('remember_pwd', rememberPwd.value ? '1' : '0')
  if (rememberUser.value || rememberPwd.value) {
    localStorage.setItem('saved_username', username.value)
  } else {
    localStorage.removeItem('saved_username')
  }
  if (rememberPwd.value) {
    localStorage.setItem('saved_password', password.value)
  } else {
    localStorage.removeItem('saved_password')
  }
}

function restoreRemember() {
  if (localStorage.getItem('remember_user') === '1') {
    rememberUser.value = true
    username.value = localStorage.getItem('saved_username') || ''
  }
  if (localStorage.getItem('remember_pwd') === '1') {
    rememberPwd.value = true
    rememberUser.value = true
    username.value = localStorage.getItem('saved_username') || ''
    password.value = localStorage.getItem('saved_password') || ''
  }
}

onMounted(restoreRemember)

async function submit() {
  error.value = ''
  if (mode.value === 'register') {
    if (!username.value.trim()) {
      usernameError.value = '请输入用户名'
      return
    }
    if (!password.value) {
      passwordError.value = '请输入密码'
      return
    }
    usernameError.value = usernameRule(username.value)
    passwordError.value = passwordRule(password.value)
    if (usernameError.value || passwordError.value) return
  }
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
  user.setAuth(data.token, data.username)
  if (mode.value === 'login') saveRemember()
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
  forgotPwdError.value = passwordRule(newPassword.value)
  if (forgotPwdError.value) {
    forgotError.value = forgotPwdError.value
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
        <div class="field-box">
          <input
            v-model="username"
            placeholder="用户名"
            :class="{ invalid: usernameError }"
          />
          <p v-if="usernameError" class="field-error">{{ usernameError }}</p>
        </div>
        <div class="field-box">
          <input
            v-model="password"
            type="password"
            placeholder="密码"
            :class="{ invalid: passwordError }"
            @keyup.enter="submit"
          />
          <p v-if="passwordError" class="field-error">{{ passwordError }}</p>
        </div>
      </div>

      <div v-if="mode === 'login'" class="remember">
        <label class="remember-item">
          <input type="checkbox" v-model="rememberUser" />
          <span>记住用户名</span>
        </label>
        <label class="remember-item">
          <input type="checkbox" v-model="rememberPwd" />
          <span>记住密码</span>
        </label>
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
          <input
            v-model="newPassword"
            type="password"
            placeholder="6-32 位，含字母和数字"
            :class="{ invalid: forgotPwdError }"
          />
          <p v-if="forgotPwdError" class="field-error">{{ forgotPwdError }}</p>
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

.field-box {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.fields input.invalid,
.field input.invalid {
  border-color: #ef4444;
}

.fields input.invalid:focus,
.field input.invalid:focus {
  border-color: #ef4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.15);
}

.field-error {
  color: #ef4444;
  font-size: 12px;
  margin: 0;
  text-align: left;
}

.error {
  color: #ef4444;
  font-size: 13px;
  margin: 10px 0 0;
  text-align: left;
}

.remember {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-top: 16px;
  text-align: left;
}

.remember-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--muted);
  cursor: pointer;
  user-select: none;
}

.remember-item input {
  width: 15px;
  height: 15px;
  margin: 0;
  accent-color: #6366f1;
  cursor: pointer;
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
