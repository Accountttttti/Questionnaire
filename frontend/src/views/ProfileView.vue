<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const user = ref({ username: '', avatar: '', email: '' })

const editUsername = ref('')
const editAvatar = ref('')
const savingProfile = ref(false)
const profileMsg = ref('')
const profileError = ref('')

const emailInput = ref('')
const codeInput = ref('')
const codeSent = ref(false)
const sendingCode = ref(false)
const verifying = ref(false)
const cooldown = ref(0)
const emailMsg = ref('')
const emailError = ref('')
let timer = null

const oldPassword = ref('')
const newPassword = ref('')
const savingPwd = ref(false)
const pwdMsg = ref('')
const pwdError = ref('')

function authHeaders() {
  return { Authorization: localStorage.getItem('token') || '' }
}

async function load() {
  const res = await fetch('/api/me', { headers: authHeaders() })
  const data = await res.json()
  if (res.ok) {
    user.value = data
    editUsername.value = data.username
    editAvatar.value = data.avatar || ''
  }
}

async function onPickAvatar(e) {
  const file = e.target.files && e.target.files[0]
  if (!file) return
  const fd = new FormData()
  fd.append('file', file)
  const res = await fetch('/api/upload', {
    method: 'POST',
    headers: { Authorization: localStorage.getItem('token') || '' },
    body: fd,
  })
  const data = await res.json()
  if (res.ok) {
    editAvatar.value = data.url
  } else {
    profileError.value = data.error || '上传失败'
  }
}

async function saveProfile() {
  savingProfile.value = true
  profileMsg.value = ''
  profileError.value = ''
  const res = await fetch('/api/me', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ username: editUsername.value, avatar: editAvatar.value }),
  })
  const data = await res.json()
  savingProfile.value = false
  if (res.ok) {
    user.value = { ...user.value, ...data }
    localStorage.setItem('username', data.username)
    profileMsg.value = '保存成功'
  } else {
    profileError.value = data.error || '保存失败'
  }
}

async function sendCode() {
  if (sendingCode.value || cooldown.value > 0) return
  if (!emailInput.value.trim()) {
    emailError.value = '请输入邮箱地址'
    return
  }
  sendingCode.value = true
  emailMsg.value = ''
  emailError.value = ''
  const res = await fetch('/api/me/email/send-code', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ email: emailInput.value.trim() }),
  })
  const data = await res.json()
  sendingCode.value = false
  if (res.ok) {
    codeSent.value = true
    codeInput.value = ''
    emailMsg.value = '验证码已发送，请查收邮件'
    cooldown.value = 60
    timer = setInterval(() => {
      cooldown.value -= 1
      if (cooldown.value <= 0) clearInterval(timer)
    }, 1000)
  } else {
    emailError.value = data.error || '发送失败'
  }
}

async function verifyEmail() {
  if (!codeInput.value.trim()) {
    emailError.value = '请输入验证码'
    return
  }
  verifying.value = true
  emailMsg.value = ''
  emailError.value = ''
  const res = await fetch('/api/me/email/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ email: emailInput.value.trim(), code: codeInput.value.trim() }),
  })
  const data = await res.json()
  verifying.value = false
  if (res.ok) {
    user.value.email = data.email
    codeSent.value = false
    codeInput.value = ''
    emailMsg.value = '邮箱绑定成功'
  } else {
    emailError.value = data.error || '绑定失败'
  }
}

async function savePassword() {
  if (!oldPassword.value || !newPassword.value) {
    pwdError.value = '请填写旧密码和新密码'
    return
  }
  savingPwd.value = true
  pwdMsg.value = ''
  pwdError.value = ''
  const res = await fetch('/api/me', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ old_password: oldPassword.value, new_password: newPassword.value }),
  })
  const data = await res.json()
  savingPwd.value = false
  if (res.ok) {
    oldPassword.value = ''
    newPassword.value = ''
    pwdMsg.value = '密码修改成功'
  } else {
    pwdError.value = data.error || '修改失败'
  }
}

onMounted(load)
onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <div class="profile">
    <header class="head">
      <h1>用户信息</h1>
      <p class="sub">查看和修改你的个人资料</p>
    </header>

    <div class="card">
      <h2 class="card-title">基本资料</h2>

      <div class="avatar-row">
        <div class="avatar-lg">
          <img v-if="editAvatar" :src="editAvatar" alt="头像" />
          <span v-else>{{ (editUsername || '?').charAt(0) }}</span>
        </div>
        <label class="upload-btn">
          上传头像
          <input type="file" accept="image/*" @change="onPickAvatar" hidden />
        </label>
      </div>

      <div class="field">
        <label>昵称</label>
        <input v-model="editUsername" placeholder="昵称" />
      </div>

      <div class="field">
        <label>邮箱</label>
        <div class="email-display">
          {{ user.email || '未绑定' }}
          <span v-if="user.email" class="verified">已绑定</span>
        </div>
      </div>

      <p v-if="profileError" class="msg error">{{ profileError }}</p>
      <p v-if="profileMsg" class="msg ok">{{ profileMsg }}</p>

      <button class="save-btn" :disabled="savingProfile" @click="saveProfile">
        {{ savingProfile ? '保存中...' : '保存资料' }}
      </button>
    </div>

    <div class="card">
      <h2 class="card-title">绑定邮箱</h2>
      <p class="desc">
        {{ user.email ? `当前已绑定 ${user.email}，输入新邮箱可换绑` : '绑定邮箱后可用于找回密码等' }}
      </p>

      <div class="field">
        <label>邮箱地址</label>
        <div class="email-row">
          <input v-model="emailInput" placeholder="输入要绑定的邮箱" />
          <button class="code-btn" :disabled="sendingCode || cooldown > 0" @click="sendCode">
            {{ sendingCode ? '发送中...' : cooldown > 0 ? cooldown + 's' : '发送验证码' }}
          </button>
        </div>
      </div>

      <div v-if="codeSent" class="field">
        <label>验证码</label>
        <input v-model="codeInput" placeholder="输入邮件中的 6 位验证码" />
      </div>

      <p v-if="emailError" class="msg error">{{ emailError }}</p>
      <p v-if="emailMsg" class="msg ok">{{ emailMsg }}</p>

      <button v-if="codeSent" class="save-btn" :disabled="verifying" @click="verifyEmail">
        {{ verifying ? '绑定中...' : '确认绑定' }}
      </button>
    </div>

    <div class="card">
      <h2 class="card-title">修改密码</h2>

      <div class="field">
        <label>旧密码</label>
        <input v-model="oldPassword" type="password" placeholder="旧密码" />
      </div>

      <div class="field">
        <label>新密码</label>
        <input v-model="newPassword" type="password" placeholder="新密码" />
      </div>

      <p v-if="pwdError" class="msg error">{{ pwdError }}</p>
      <p v-if="pwdMsg" class="msg ok">{{ pwdMsg }}</p>

      <button class="save-btn" :disabled="savingPwd" @click="savePassword">
        {{ savingPwd ? '修改中...' : '修改密码' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.profile {
  max-width: 560px;
  margin: 0 auto;
  padding: 32px 24px 60px;
}

.head {
  margin-bottom: 24px;
}

.head h1 {
  font-size: 24px;
  margin: 0 0 4px;
}

.sub {
  color: var(--muted);
  margin: 0;
  font-size: 14px;
}

.card {
  background: #fff;
  border-radius: 16px;
  padding: 28px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  margin-bottom: 20px;
}

.card-title {
  font-size: 17px;
  margin: 0 0 20px;
}

.desc {
  color: var(--muted);
  font-size: 13px;
  margin: -12px 0 20px;
}

.avatar-row {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
}

.avatar-lg {
  width: 88px;
  height: 88px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  font-weight: 600;
  flex-shrink: 0;
  overflow: hidden;
}

.avatar-lg img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.upload-btn {
  padding: 8px 16px;
  font-size: 14px;
  color: var(--primary);
  border: 1px solid var(--primary);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s;
}

.upload-btn:hover {
  background: rgba(99, 102, 241, 0.06);
}

.field {
  margin-bottom: 16px;
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
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12);
}

.email-display {
  font-size: 14px;
  color: var(--text);
  display: flex;
  align-items: center;
  gap: 10px;
}

.verified {
  font-size: 12px;
  color: #059669;
  background: rgba(16, 185, 129, 0.1);
  padding: 2px 10px;
  border-radius: 20px;
}

.email-row {
  display: flex;
  gap: 10px;
}

.email-row input {
  flex: 1;
}

.code-btn {
  flex-shrink: 0;
  padding: 0 18px;
  font-size: 14px;
  color: var(--primary);
  border: 1px solid var(--primary);
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
}

.msg.error {
  color: var(--danger);
}

.msg.ok {
  color: #059669;
}

.save-btn {
  padding: 12px 28px;
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  border-radius: 12px;
  cursor: pointer;
}

.save-btn:hover {
  opacity: 0.92;
}

.save-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
