<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '../stores/user.js'

const user = useUserStore()
const list = ref([])
const loading = ref(true)
const view = ref('')

const kindCards = [
  { key: 'submit', label: '提交', desc: '有人填写并提交了你的问卷' },
  { key: 'like', label: '喜爱', desc: '有人给你的问卷点了赞' },
  { key: 'favorite', label: '收藏', desc: '有人收藏了你的问卷' },
]

const verbMap = {
  submit: '提交了你的问卷',
  like: '喜爱了你的问卷',
  favorite: '收藏了你的问卷',
}

const groups = computed(() => {
  const g = { submit: [], like: [], favorite: [] }
  list.value.forEach((m) => {
    if (g[m.kind]) g[m.kind].push(m)
  })
  return g
})

const currentKindLabel = computed(() => {
  const c = kindCards.find((c) => c.key === view.value)
  return c ? c.label : ''
})

function formatTime(s) {
  if (!s) return ''
  const [d, t] = s.split(' ')
  if (!d) return s
  const [y, m, day] = d.split('-')
  return `${y}.${Number(m)}.${Number(day)}` + (t ? ` ${t.slice(0, 5)}` : '')
}

function latestSummary(key) {
  const g = groups.value[key]
  if (!g.length) return '暂无动态'
  const m = g[0]
  return `${m.actor || '匿名用户'} · ${formatTime(m.created_at)}`
}

function openKind(k) {
  view.value = k
}

function back() {
  view.value = ''
}

async function load() {
  const res = await fetch('/api/me/notifications', { headers: user.authHeaders() })
  const data = await res.json()
  loading.value = false
  if (res.ok) {
    list.value = data
    if (data.length) {
      localStorage.setItem('lastNotifAt', data[0].created_at)
    }
  }
}

onMounted(load)
</script>

<template>
  <div class="messages">
    <header class="head">
      <h1>消息</h1>
      <p>你创建的问卷收到的动态</p>
    </header>

    <div v-if="loading" class="hint">加载中...</div>

    <!-- 三张分类卡片 -->
    <div v-else-if="view === ''" class="cards">
      <div v-for="c in kindCards" :key="c.key" class="kind-card" @click="openKind(c.key)">
        <div class="icon" :class="c.key">
          <svg
            v-if="c.key === 'submit'"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <rect x="3" y="4" width="18" height="16" rx="3" />
            <path d="M8 9h8M8 13h5" />
          </svg>
          <svg
            v-else-if="c.key === 'like'"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
          </svg>
          <svg
            v-else
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
          </svg>
        </div>
        <div class="info">
          <div class="line1">
            <span class="name">{{ c.label }}</span>
            <span class="count" :class="c.key">共 {{ groups[c.key].length }} 条</span>
          </div>
          <div class="line2">{{ c.desc }}</div>
          <div class="line3">{{ latestSummary(c.key) }}</div>
        </div>
        <div class="arrow">›</div>
      </div>
    </div>

    <!-- 某一类详情 -->
    <div v-else>
      <div class="detail-head">
        <button class="back" @click="back">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <line x1="19" y1="12" x2="5" y2="12" />
            <polyline points="12 19 5 12 12 5" />
          </svg>
          返回
        </button>
        <h2>{{ currentKindLabel }}</h2>
        <span class="num">共 {{ groups[view].length }} 条</span>
      </div>

      <div v-if="groups[view].length === 0" class="hint">暂无该类消息</div>
      <div v-else class="list">
        <div v-for="(m, i) in groups[view]" :key="i" class="item">
          <div class="avatar">{{ (m.actor || '匿').charAt(0) }}</div>
          <div class="body">
            <div class="row1">{{ m.actor || '匿名用户' }}</div>
            <div class="row2">
              <span class="verb" :class="m.kind">{{ verbMap[m.kind] }}</span>
              <span class="title">《{{ m.title }}》</span>
            </div>
            <div class="row3">{{ formatTime(m.created_at) }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.messages {
  padding: 36px 40px;
  max-width: 860px;
  margin: 0 auto;
}

.head h1 {
  font-size: 24px;
  margin: 0 0 6px;
}

.head p {
  color: var(--muted);
  margin: 0 0 28px;
}

.hint {
  color: var(--muted);
  padding: 40px 0;
  text-align: center;
}

.cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.kind-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: #fff;
  border-radius: 14px;
  padding: 18px 20px;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: transform 0.15s, box-shadow 0.15s;
}

.kind-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
}

.icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.icon svg {
  width: 24px;
  height: 24px;
}

.icon.submit {
  background: rgba(16, 185, 129, 0.12);
  color: #059669;
}

.icon.like {
  background: rgba(244, 63, 94, 0.12);
  color: #e11d48;
}

.icon.favorite {
  background: rgba(245, 158, 11, 0.12);
  color: #d97706;
}

.info {
  flex: 1;
  min-width: 0;
}

.line1 {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 3px;
}

.name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
}

.line2 {
  font-size: 13px;
  color: var(--muted);
  margin-bottom: 3px;
}

.line3 {
  font-size: 12px;
  color: #cbd5e1;
}

.count {
  font-size: 13px;
  font-weight: 600;
}

.count.submit {
  color: #059669;
}

.count.like {
  color: #e11d48;
}

.count.favorite {
  color: #d97706;
}

.arrow {
  color: #cbd5e1;
  font-size: 22px;
  flex-shrink: 0;
}

.detail-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.back {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1px solid var(--border);
  background: #fff;
  color: var(--muted);
  border-radius: 10px;
  font-size: 14px;
  cursor: pointer;
}

.back svg {
  width: 16px;
  height: 16px;
}

.back:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.detail-head h2 {
  font-size: 18px;
  margin: 0;
}

.num {
  color: var(--muted);
  font-size: 13px;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.item {
  display: flex;
  gap: 14px;
  background: #fff;
  border-radius: 14px;
  padding: 16px 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  align-items: center;
}

.avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 600;
  flex-shrink: 0;
}

.body {
  min-width: 0;
}

.row1 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 2px;
}

.row2 {
  font-size: 14px;
  color: var(--muted);
  margin-bottom: 2px;
  line-height: 1.5;
}

.verb {
  margin-right: 4px;
}

.verb.submit {
  color: #059669;
}

.verb.like {
  color: #e11d48;
}

.verb.favorite {
  color: #d97706;
}

.title {
  color: var(--primary);
  font-weight: 500;
}

.row3 {
  font-size: 12px;
  color: #cbd5e1;
}
</style>
