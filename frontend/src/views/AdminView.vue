<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '../stores/user.js'

const user = useUserStore()
const ready = ref(false)
const activeSection = ref('')
const users = ref([])
const qs = ref([])
const usersLoading = ref(false)
const contentLoading = ref(false)

const isSuper = computed(() => user.role === 'super')

const sections = computed(() => {
  const list = []
  if (isSuper.value) list.push({ key: 'users', label: '用户管理' })
  list.push({ key: 'content', label: '内容管理' })
  return list
})

const typeLabel = { test: '测试问卷', relay: '接龙', exam: '考试' }
const statusLabel = { draft: '草稿', published: '已发布', stopped: '已下架' }
const roleLabel = { super: '最高管理员', admin: '普通管理员', user: '普通用户' }

function formatTime(s) {
  if (!s) return '—'
  const [d, t] = s.split(' ')
  if (!d) return s
  const [y, m, day] = d.split('-')
  const time = t ? t.slice(0, 5) : ''
  return `${y}.${Number(m)}.${Number(day)}` + (time ? ` ${time}` : '')
}

async function loadUsers() {
  usersLoading.value = true
  const res = await fetch('/api/admin/users', { headers: user.authHeaders() })
  const data = await res.json()
  usersLoading.value = false
  if (res.ok) users.value = data
  else alert(data.error || '加载失败')
}

async function loadContent() {
  contentLoading.value = true
  const res = await fetch('/api/admin/questionnaires', { headers: user.authHeaders() })
  const data = await res.json()
  contentLoading.value = false
  if (res.ok) qs.value = data
  else alert(data.error || '加载失败')
}

function openSection(key) {
  activeSection.value = key
  if (key === 'users') loadUsers()
  else if (key === 'content') loadContent()
}

async function setRole(u, target) {
  const res = await fetch(`/api/admin/users/${u.id}/role`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...user.authHeaders() },
    body: JSON.stringify({ role: target }),
  })
  const data = await res.json()
  if (res.ok) loadUsers()
  else alert(data.error || '操作失败')
}

async function setStatus(q, status) {
  const res = await fetch(`/api/admin/questionnaires/${q.id}/status`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...user.authHeaders() },
    body: JSON.stringify({ status }),
  })
  const data = await res.json()
  if (res.ok) loadContent()
  else alert(data.error || '操作失败')
}

onMounted(async () => {
  await user.fetchMe()
  if (user.role !== 'user') {
    const first = sections.value[0]
    if (first) openSection(first.key)
  }
  ready.value = true
})
</script>

<template>
  <div class="admin">
    <aside class="sidebar">
      <div class="side-title">管理中心</div>
      <nav class="side-nav">
        <button
          v-for="s in sections"
          :key="s.key"
          class="side-item"
          :class="{ active: activeSection === s.key }"
          @click="openSection(s.key)"
        >
          {{ s.label }}
        </button>
      </nav>
    </aside>

    <main class="main">
      <div v-if="!ready" class="hint">加载中...</div>
      <div v-else-if="user.role === 'user'" class="hint">无权限访问该页面</div>

      <template v-else-if="activeSection === 'users'">
        <header class="head">
          <h1>用户管理</h1>
          <span class="count">共 {{ users.length }} 个用户</span>
        </header>

        <div v-if="usersLoading" class="hint">加载中...</div>
        <div v-else class="table">
          <div class="thead">
            <span class="col-id">ID</span>
            <span class="col-user">用户</span>
            <span class="col-role">角色</span>
            <span class="col-time">注册时间</span>
            <span class="col-action">操作</span>
          </div>
          <div v-for="u in users" :key="u.id" class="trow">
            <span class="col-id">{{ u.id }}</span>
            <span class="col-user">
              <span class="avatar">{{ (u.username || '?').charAt(0) }}</span>
              <span class="uname">{{ u.username }}</span>
            </span>
            <span class="col-role">
              <span class="role-badge" :class="'role-' + u.role">{{ roleLabel[u.role] || u.role }}</span>
            </span>
            <span class="col-time">{{ formatTime(u.created_at) }}</span>
            <span class="col-action">
              <span v-if="u.role === 'super'" class="muted">—</span>
              <button v-else-if="u.role === 'user'" class="act" @click="setRole(u, 'admin')">设为管理员</button>
              <button v-else class="act danger" @click="setRole(u, 'user')">取消管理员</button>
            </span>
          </div>
        </div>
      </template>

      <template v-else>
        <header class="head">
          <h1>内容管理</h1>
          <span class="count">共 {{ qs.length }} 份问卷</span>
        </header>

        <div v-if="contentLoading" class="hint">加载中...</div>
        <div v-else-if="qs.length === 0" class="hint">暂无问卷</div>
        <div v-else class="list">
          <div v-for="q in qs" :key="q.id" class="q-item">
            <div class="q-info">
              <div class="q-title-row">
                <span class="q-title">{{ q.title }}</span>
                <span class="type-badge">{{ typeLabel[q.type] || q.type }}</span>
                <span class="status-badge" :class="q.status">{{ statusLabel[q.status] || q.status }}</span>
              </div>
              <div class="q-meta">作者：{{ q.author }} · 答卷 {{ q.response_count }} · {{ formatTime(q.updated_at) }}</div>
            </div>
            <div class="q-action">
              <button v-if="q.status === 'published'" class="act danger" @click="setStatus(q, 'stopped')">下架</button>
              <button v-else-if="q.status === 'stopped'" class="act" @click="setStatus(q, 'published')">上架</button>
              <span v-else class="muted">—</span>
            </div>
          </div>
        </div>
      </template>
    </main>
  </div>
</template>

<style scoped>
.admin {
  display: flex;
  min-height: calc(100vh - 60px);
}

.sidebar {
  width: 220px;
  flex-shrink: 0;
  padding: 24px 16px;
  background: #fff;
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.side-title {
  font-size: 13px;
  font-weight: 600;
  color: #94a3b8;
  letter-spacing: 1px;
  padding: 0 6px;
}

.side-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.side-item {
  padding: 11px 14px;
  border: none;
  background: transparent;
  text-align: left;
  font-size: 14px;
  font-weight: 500;
  color: var(--muted);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s;
}

.side-item:hover {
  background: #f4f5fb;
  color: var(--text);
}

.side-item.active {
  background: rgba(99, 102, 241, 0.08);
  color: var(--primary);
  font-weight: 600;
}

.main {
  flex: 1;
  min-width: 0;
  padding: 32px 40px;
}

.head {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 24px;
}

.head h1 {
  font-size: 22px;
  margin: 0;
}

.count {
  color: var(--muted);
  font-size: 14px;
}

.hint {
  color: var(--muted);
  padding: 60px 0;
  text-align: center;
}

.table {
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.thead,
.trow {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 20px;
}

.thead {
  height: 46px;
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
  background: #f8fafc;
  border-bottom: 1px solid var(--border);
}

.trow {
  min-height: 60px;
  border-bottom: 1px solid #f1f5f9;
  font-size: 14px;
}

.trow:last-child {
  border-bottom: none;
}

.col-id {
  width: 56px;
  flex-shrink: 0;
  color: #94a3b8;
}

.col-role {
  width: 120px;
  flex-shrink: 0;
}

.col-user {
  flex: 1 1 0;
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 500;
  color: var(--text);
  min-width: 0;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
}

.uname {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.col-time {
  width: 140px;
  flex-shrink: 0;
  color: var(--muted);
  font-size: 13px;
}

.col-action {
  width: 120px;
  flex-shrink: 0;
}

.role-badge {
  display: inline-block;
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 20px;
  white-space: nowrap;
}

.role-badge.role-super {
  color: #7c3aed;
  background: rgba(124, 58, 237, 0.1);
}

.role-badge.role-admin {
  color: var(--primary);
  background: rgba(99, 102, 241, 0.1);
}

.role-badge.role-user {
  color: #64748b;
  background: #f1f5f9;
}

.act {
  padding: 5px 12px;
  font-size: 13px;
  border: 1px solid var(--border);
  background: #fff;
  color: #4b5563;
  border-radius: 8px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s;
}

.act:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.act.danger:hover {
  border-color: var(--danger);
  color: var(--danger);
}

.muted {
  color: #cbd5e1;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.q-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: #fff;
  border-radius: 14px;
  padding: 18px 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.q-info {
  min-width: 0;
}

.q-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.q-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 420px;
}

.type-badge {
  flex-shrink: 0;
  font-size: 12px;
  color: var(--primary);
  background: rgba(99, 102, 241, 0.08);
  padding: 3px 10px;
  border-radius: 20px;
  font-weight: 600;
}

.status-badge {
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 20px;
}

.status-badge.published {
  color: #059669;
  background: rgba(16, 185, 129, 0.1);
}

.status-badge.stopped {
  color: #e11d48;
  background: rgba(244, 63, 94, 0.1);
}

.status-badge.draft {
  color: #64748b;
  background: #f1f5f9;
}

.q-meta {
  font-size: 12px;
  color: var(--muted);
}

.q-action {
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .admin {
    flex-direction: column;
  }
  .sidebar {
    width: 100%;
    flex-shrink: 0;
    flex-direction: column;
    gap: 10px;
    padding: 12px 16px;
    border-right: none;
    border-bottom: 1px solid var(--border);
  }
  .side-nav {
    flex-direction: row;
    gap: 6px;
    overflow-x: auto;
  }
  .side-item {
    flex-shrink: 0;
    white-space: nowrap;
    padding: 9px 14px;
  }
  .main {
    padding: 20px 16px;
  }
  .table {
    overflow-x: auto;
  }
  .thead,
  .trow {
    min-width: 620px;
  }
  .q-title-row {
    flex-wrap: wrap;
  }
}
</style>
