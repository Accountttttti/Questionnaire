<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/user.js'

const route = useRoute()
const router = useRouter()
const qid = route.params.id
const user = useUserStore()

const q = ref(null)
const error = ref('')
const loading = ref(true)

const typeLabel = { test: '测试问卷', relay: '接龙', exam: '考试' }

async function load() {
  const res = await fetch(`/api/questionnaires/${qid}/public`, {
    headers: user.authHeaders(),
  })
  const data = await res.json()
  loading.value = false
  if (res.ok) {
    q.value = data
  } else {
    error.value = data.error || '加载失败'
  }
}

function start() {
  router.push(`/fill/${qid}/answer`)
}

function edit() {
  router.push(`/editor/${qid}`)
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div v-if="loading" class="hint">加载中...</div>

    <div v-else-if="error" class="error-card">
      <div class="error-title">无法打开</div>
      <div class="error-desc">{{ error }}</div>
    </div>

    <div v-else class="card">
      <span class="badge">{{ typeLabel[q.type] || q.type }}</span>
      <h1>{{ q.title }}</h1>
      <div class="author">发布者 · {{ q.author }}</div>
      <div v-if="q.description" class="desc">{{ q.description }}</div>
      <div class="meta">
        共 {{ q.questions.length }} 题
        <span v-if="q.status === 'draft'" class="draft-tag">草稿</span>
      </div>

      <div class="actions">
        <button v-if="q.is_owner" class="edit-btn" @click="edit">编辑</button>
        <button class="start" @click="start">开始测试</button>
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
  max-width: 480px;
  background: #fff;
  border-radius: 24px;
  box-shadow: 0 20px 60px rgba(99, 102, 241, 0.15);
  padding: 48px 40px;
  text-align: center;
}

.badge {
  display: inline-block;
  font-size: 13px;
  color: var(--primary);
  background: rgba(99, 102, 241, 0.08);
  padding: 5px 14px;
  border-radius: 20px;
  font-weight: 600;
  margin-bottom: 20px;
}

h1 {
  font-size: 26px;
  margin: 0 0 14px;
  line-height: 1.4;
}

.author {
  color: var(--muted);
  font-size: 14px;
  margin-bottom: 6px;
}

.desc {
  color: var(--text);
  font-size: 14px;
  line-height: 1.7;
  background: #f8fafc;
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 18px;
  text-align: left;
  white-space: pre-wrap;
}

.meta {
  color: #94a3b8;
  font-size: 13px;
  margin-bottom: 36px;
}

.actions {
  display: flex;
  gap: 12px;
}

.edit-btn {
  flex-shrink: 0;
  padding: 15px 22px;
  font-size: 16px;
  font-weight: 600;
  color: var(--primary);
  background: #fff;
  border: 1px solid var(--primary);
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.15s;
}

.edit-btn:hover {
  background: rgba(99, 102, 241, 0.06);
}

.start {
  flex: 1;
  padding: 15px;
  font-size: 17px;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  border-radius: 14px;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.1s;
}

.start:hover {
  opacity: 0.9;
}

.start:active {
  transform: scale(0.98);
}

.draft-tag {
  display: inline-block;
  margin-left: 8px;
  padding: 2px 10px;
  font-size: 12px;
  color: #64748b;
  background: #f1f5f9;
  border-radius: 20px;
}

.hint {
  color: var(--muted);
  font-size: 15px;
}

.error-card {
  background: #fff;
  border-radius: 20px;
  padding: 40px;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
}

.error-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
}

.error-desc {
  color: var(--muted);
}
</style>
