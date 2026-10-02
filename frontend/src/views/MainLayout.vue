<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const username = ref(localStorage.getItem('username') || '')
const avatar = ref('')
const menuOpen = ref(false)

const initial = computed(() => (username.value || '?').charAt(0))

function authHeaders() {
  return { Authorization: localStorage.getItem('token') || '' }
}

async function loadMe() {
  try {
    const res = await fetch('/api/me', { headers: authHeaders() })
    const data = await res.json()
    if (res.ok) {
      username.value = data.username
      avatar.value = data.avatar || ''
      localStorage.setItem('username', data.username)
    }
  } catch (e) {
    // ignore
  }
}

function toggleMenu() {
  menuOpen.value = !menuOpen.value
}

function userInfo() {
  menuOpen.value = false
  router.push('/profile')
}

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  router.push('/login')
}

onMounted(loadMe)
</script>

<template>
  <div class="layout">
    <header class="topbar">
      <div class="brand" @click="router.push('/')">问卷系统</div>

      <nav class="topnav">
        <router-link
          to="/mine"
          class="topnav-item"
          :class="{ active: route.path.startsWith('/mine') }"
        >
          我的问卷
        </router-link>
        <router-link
          to="/messages"
          class="topnav-item"
          :class="{ active: route.path.startsWith('/messages') }"
        >
          消息
        </router-link>
      </nav>

      <div class="spacer"></div>

      <div class="user">
        <div class="avatar" @click="toggleMenu">
          <img v-if="avatar" :src="avatar" alt="" />
          <span v-else>{{ initial }}</span>
        </div>
        <span class="uname">{{ username }}</span>
        <div v-if="menuOpen" class="dropdown">
          <button class="dd-item" @click="userInfo">用户信息</button>
          <button class="dd-item danger" @click="logout">退出登录</button>
        </div>
      </div>
    </header>

    <main class="content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.layout {
  min-height: 100vh;
  background: var(--bg);
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 100;
  height: 60px;
  display: flex;
  align-items: center;
  gap: 28px;
  padding: 0 24px;
  background: #fff;
  border-bottom: 1px solid var(--border);
}

.brand {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  cursor: pointer;
  white-space: nowrap;
}

.topnav {
  display: flex;
  align-items: center;
  gap: 6px;
}

.topnav-item {
  padding: 8px 16px;
  border: none;
  background: transparent;
  color: var(--muted);
  font-size: 15px;
  font-weight: 500;
  border-radius: 10px;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.15s;
}

.topnav-item:hover {
  background: #f4f5fb;
  color: var(--text);
}

.topnav-item.active {
  background: rgba(99, 102, 241, 0.08);
  color: var(--primary);
  font-weight: 600;
}

.topnav-item.plain {
  background: transparent;
}

.spacer {
  flex: 1;
}

.user {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 16px;
  overflow: hidden;
  flex-shrink: 0;
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.uname {
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
}

.dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 140px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  padding: 6px;
  display: flex;
  flex-direction: column;
}

.dd-item {
  padding: 10px 14px;
  border: none;
  background: transparent;
  text-align: left;
  font-size: 14px;
  color: var(--text);
  border-radius: 8px;
  cursor: pointer;
}

.dd-item:hover {
  background: #f4f5fb;
}

.dd-item.danger {
  color: var(--danger);
}

.dd-item.danger:hover {
  background: rgba(239, 68, 68, 0.06);
}

.content {
  min-width: 0;
}
</style>
