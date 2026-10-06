<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useHunterStore } from '../stores/hunter.js'
import { useUserStore } from '../stores/user.js'

const route = useRoute()
const router = useRouter()

const menuOpen = ref(false)
const unread = ref(false)
const hunter = useHunterStore()
const user = useUserStore()

function toggleMenu() {
  menuOpen.value = !menuOpen.value
}

function userInfo() {
  menuOpen.value = false
  router.push('/profile')
}

function logout() {
  user.logout()
  router.push('/login')
}

async function checkUnread() {
  try {
    const res = await fetch('/api/me/notifications', { headers: user.authHeaders() })
    const data = await res.json()
    if (!res.ok || !data.length) {
      unread.value = false
      return
    }
    const latest = data[0].created_at
    const lastRead = localStorage.getItem('lastNotifAt') || ''
    unread.value = latest > lastRead
  } catch (e) {
    unread.value = false
  }
}

function markRead() {
  unread.value = false
}

let unreadTimer = null

onMounted(() => {
  user.fetchMe()
  checkUnread()
  unreadTimer = setInterval(checkUnread, 15000)
  hunter.load()
})

onBeforeUnmount(() => {
  if (unreadTimer) clearInterval(unreadTimer)
})
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
          @click="markRead"
        >
          消息
          <span v-if="unread" class="dot"></span>
        </router-link>
        <router-link
          v-if="user.isAdmin"
          to="/admin"
          class="topnav-item"
          :class="{ active: route.path.startsWith('/admin') }"
        >
          管理
        </router-link>
      </nav>

      <button
        v-if="hunter.unlocked"
        class="hunter-entry"
        title="Hunter"
        @click="router.push('/hunter')"
      >
        <svg viewBox="0 0 24 24" fill="none">
          <path
            d="M12 2 C6 5 4.5 10 6 14 C7 17 9 18.5 12 20 C15 18.5 17 17 18 14 C19.5 10 18 5 12 2 Z"
            fill="#e5484d"
          />
          <path d="M9.5 20 L10.3 22 M14.5 20 L13.7 22" stroke="#7c5c3a" stroke-width="1" />
          <rect x="8.5" y="20.4" width="7" height="3" rx="0.5" fill="#8a5a2b" />
        </svg>
      </button>

      <div class="spacer"></div>

      <div class="user">
        <div class="avatar" @click="toggleMenu">
          <img v-if="user.avatar" :src="user.avatar" alt="" />
          <span v-else>{{ user.initial }}</span>
        </div>
        <span class="uname">{{ user.username }}</span>
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
  position: relative;
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

.dot {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ef4444;
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

.hunter-entry {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border: none;
  background: transparent;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s;
}

.hunter-entry:hover {
  background: #f4f5fb;
}

.hunter-entry svg {
  width: 22px;
  height: 22px;
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

@media (max-width: 768px) {
  .topbar {
    gap: 10px;
    padding: 0 12px;
    height: 54px;
  }
  .brand {
    font-size: 16px;
  }
  .topnav {
    gap: 2px;
  }
  .topnav-item {
    padding: 6px 9px;
    font-size: 13px;
  }
  .uname {
    display: none;
  }
  .avatar {
    width: 32px;
    height: 32px;
    font-size: 14px;
  }
  .hunter-entry {
    width: 34px;
    height: 34px;
  }
  .hunter-entry svg {
    width: 20px;
    height: 20px;
  }
}
</style>
