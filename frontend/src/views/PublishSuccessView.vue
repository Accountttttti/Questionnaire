<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const qid = route.params.id

const title = ref('')
const copied = ref(false)
const shareUrl = window.location.origin + '/fill/' + qid

async function load() {
  const res = await fetch(`/api/questionnaires/${qid}`, {
    headers: { Authorization: localStorage.getItem('token') || '' },
  })
  const data = await res.json()
  if (res.ok) title.value = data.title
}

async function copyLink() {
  try {
    await navigator.clipboard.writeText(shareUrl)
    copied.value = true
    setTimeout(() => (copied.value = false), 2000)
  } catch {
    alert('复制失败，请手动复制：' + shareUrl)
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="card">
      <div class="check">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M20 6 9 17l-5-5" />
        </svg>
      </div>

      <h1>发布成功</h1>
      <p class="sub">「{{ title }}」已发布到公开广场</p>

      <div class="actions">
        <button class="primary" @click="router.push(`/fill/${qid}`)">查看测试</button>
        <button class="ghost" @click="router.push('/')">返回首页</button>
      </div>

      <div class="share">
        <div class="share-label">分享链接</div>
        <div class="share-row">
          <input :value="shareUrl" readonly />
          <button class="copy" @click="copyLink">{{ copied ? '已复制' : '复制' }}</button>
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
  max-width: 440px;
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(99, 102, 241, 0.15);
  padding: 44px 36px;
  text-align: center;
}

.check {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #10b981, #059669);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
}

.check svg {
  width: 32px;
  height: 32px;
}

h1 {
  font-size: 24px;
  margin: 0 0 8px;
}

.sub {
  color: var(--muted);
  margin: 0 0 28px;
  font-size: 14px;
}

.actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-bottom: 28px;
}

.primary {
  padding: 12px 26px;
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  border-radius: 12px;
  cursor: pointer;
}

.primary:hover {
  opacity: 0.9;
}

.ghost {
  padding: 12px 22px;
  border: 1px solid var(--border);
  background: #fff;
  color: var(--muted);
  border-radius: 12px;
  cursor: pointer;
  font-size: 15px;
}

.ghost:hover {
  color: var(--primary);
  border-color: var(--primary);
}

.share {
  text-align: left;
  border-top: 1px solid var(--border);
  padding-top: 20px;
}

.share-label {
  font-size: 13px;
  color: var(--muted);
  margin-bottom: 10px;
}

.share-row {
  display: flex;
  gap: 8px;
}

.share-row input {
  flex: 1;
  padding: 10px 12px;
  font-size: 13px;
  color: var(--muted);
  border: 1px solid var(--border);
  border-radius: 10px;
  background: #f8fafc;
  outline: none;
}

.copy {
  padding: 0 16px;
  border: 1px solid var(--primary);
  background: rgba(99, 102, 241, 0.06);
  color: var(--primary);
  border-radius: 10px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.copy:hover {
  background: rgba(99, 102, 241, 0.12);
}
</style>
