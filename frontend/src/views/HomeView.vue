<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import QRCode from 'qrcode'
import html2canvas from 'html2canvas'
import { useHunterStore } from '../stores/hunter.js'
import { useUserStore } from '../stores/user.js'

const router = useRouter()
const route = useRoute()
const user = useUserStore()
const list = ref([])
const loading = ref(true)
const loadError = ref('')

const typeLabel = { test: '测试问卷', exam: '考试' }

const typeTabs = [
  { key: '', label: '全部' },
  { key: 'test', label: '测试问卷' },
  { key: 'exam', label: '考试' },
]

const currentType = computed(() => (route.query.type || '').toString())

const searchText = ref('')

const currentLabel = computed(() =>
  currentType.value ? typeLabel[currentType.value] : '全部问卷'
)

function setType(t) {
  router.replace({ query: t ? { type: t } : {} })
}

const filteredList = computed(() => {
  let arr = list.value
  if (currentType.value) {
    arr = arr.filter((q) => q.type === currentType.value)
  }
  const kw = searchText.value.trim().toLowerCase()
  if (kw) {
    arr = arr.filter((q) => (q.title || '').toLowerCase().includes(kw))
  }
  return arr
})

const deleteTarget = ref(null)
const deleting = ref(false)

const shareTarget = ref(null)
const qrDataUrl = ref('')
const copied = ref(false)
const generating = ref(false)
const shareRef = ref(null)

async function load() {
  try {
    const res = await fetch('/api/questionnaires/public', {
      headers: user.authHeaders(),
    })
    const data = await res.json()
    if (res.ok) list.value = data
  } catch (e) {
    loadError.value = '连接后端失败，请确认已启动 backend/dev.bat'
  } finally {
    loading.value = false
  }
}

async function toggle(q, action) {
  const res = await fetch(`/api/questionnaires/${q.id}/action`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...user.authHeaders() },
    body: JSON.stringify({ action }),
  })
  const data = await res.json()
  if (!res.ok) return
  if (action === 'favorite') {
    q.favorited = data.active
    q.favorite_count += data.active ? 1 : -1
  } else if (action === 'like') {
    q.liked = data.active
    q.like_count += data.active ? 1 : -1
  }
}

async function browse(q) {
  await fetch(`/api/questionnaires/${q.id}/action`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...user.authHeaders() },
    body: JSON.stringify({ action: 'browse' }),
  })
  router.push(`/fill/${q.id}`)
}

function edit(q) {
  router.push(`/editor/${q.id}`)
}

function askDelete(q) {
  deleteTarget.value = q
}

async function confirmDelete() {
  const q = deleteTarget.value
  if (!q) return
  deleting.value = true
  const res = await fetch(`/api/questionnaires/${q.id}`, {
    method: 'DELETE',
    headers: user.authHeaders(),
  })
  deleting.value = false
  if (res.ok) {
    deleteTarget.value = null
    load()
  } else {
    alert('删除失败')
  }
}

async function openShare(q) {
  shareTarget.value = q
  qrDataUrl.value = ''
  try {
    const url = window.location.origin + '/fill/' + q.id
    qrDataUrl.value = await QRCode.toDataURL(url, { width: 200, margin: 1 })
  } catch (e) {
    qrDataUrl.value = ''
  }
}

async function copyLink() {
  const url = window.location.origin + '/fill/' + shareTarget.value.id
  try {
    await navigator.clipboard.writeText(url)
    copied.value = true
    setTimeout(() => (copied.value = false), 2000)
  } catch (e) {
    alert('复制失败，请手动复制：' + url)
  }
}

async function downloadImage() {
  if (!shareRef.value || generating.value) return
  generating.value = true
  await nextTick()
  const el = shareRef.value
  const prevShadow = el.style.boxShadow
  el.style.boxShadow = 'none'
  try {
    const canvas = await html2canvas(el, {
      scale: 2,
      useCORS: true,
      backgroundColor: null,
    })
    const link = document.createElement('a')
    link.href = canvas.toDataURL('image/png')
    link.download = '问卷分享.png'
    link.click()
  } catch (e) {
    alert('生成图片失败，请重试')
  } finally {
    el.style.boxShadow = prevShadow
    generating.value = false
  }
}

// —— 猎人彩蛋：热气球 ——
const hunter = useHunterStore()
const hunterReady = ref(false)
const hunterSeq = ref([])
const hunterProgress = ref(0)
const balloons = ref([
  { char: '恭', num: 1, color: '#e5484d', flown: false },
  { char: '喜', num: 2, color: '#f59e0b', flown: false },
  { char: '发', num: 3, color: '#10b981', flown: false },
  { char: '布', num: 4, color: '#3b82f6', flown: false },
  { char: '！', num: 5, color: '#8b5cf6', flown: false },
])

function initHunter() {
  hunter.load()
  if (hunter.hasValidSeq && !hunter.solved) {
    hunterSeq.value = hunter.seq.split('').map(Number)
    hunterReady.value = true
  }
}

function clickBalloon(i) {
  const expected = hunterSeq.value[hunterProgress.value]
  if (balloons.value[i].num === expected) {
    balloons.value[i].flown = true
    hunterProgress.value++
    if (hunterProgress.value === 5) {
      hunter.setSolved()
      startHunterTransition()
      setTimeout(() => router.push('/hunter'), 800)
    }
  } else {
    hunterProgress.value = 0
    balloons.value.forEach((b) => (b.flown = false))
  }
}

// —— 进入猎人协会的转场动画（碎裂 + 粒子爆发 + 淡入）——
const burstCanvas = ref(null)
const hunterLeaving = ref(false)
let bctx = null
let bparticles = []
let bW = 0
let bH = 0
let burstRaf = null

function burstResize() {
  const cvs = burstCanvas.value
  if (!cvs) return
  bW = cvs.width = window.innerWidth
  bH = cvs.height = window.innerHeight
}

function spawnShards() {
  const cx = bW / 2
  const cy = bH / 2
  const palette = ['#e8c878', '#c9a961', '#fff0c0', '#f7d774']
  for (let i = 0; i < 180; i++) {
    const angle = Math.random() * Math.PI * 2
    const speed = 2 + Math.random() * 10
    const color = palette[Math.floor(Math.random() * palette.length)]
    bparticles.push({
      x: cx, y: cy,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed,
      r: 1.5 + Math.random() * 3.5,
      life: 1,
      decay: 0.014 + Math.random() * 0.02,
      color,
      rot: Math.random() * Math.PI * 2,
      spin: (Math.random() - 0.5) * 0.4,
    })
  }
}

function burstTick() {
  if (!bctx) return
  bctx.clearRect(0, 0, bW, bH)
  bctx.globalCompositeOperation = 'lighter'
  for (let i = bparticles.length - 1; i >= 0; i--) {
    const p = bparticles[i]
    p.x += p.vx
    p.y += p.vy
    p.rot += p.spin
    p.life -= p.decay
    if (p.life <= 0) {
      bparticles.splice(i, 1)
      continue
    }
    const s = p.r * 3
    bctx.globalAlpha = Math.max(0, p.life)
    bctx.fillStyle = p.color
    bctx.save()
    bctx.translate(p.x, p.y)
    bctx.rotate(p.rot)
    bctx.beginPath()
    bctx.moveTo(0, -s)
    bctx.lineTo(s * 0.65, s * 0.55)
    bctx.lineTo(-s * 0.65, s * 0.55)
    bctx.closePath()
    bctx.fill()
    bctx.restore()
  }
  bctx.globalAlpha = 1
  bctx.globalCompositeOperation = 'source-over'
  burstRaf = requestAnimationFrame(burstTick)
}

function startHunterTransition() {
  hunterLeaving.value = true
  nextTick(() => {
    burstResize()
    bctx = burstCanvas.value.getContext('2d')
    bparticles = []
    spawnShards()
    burstRaf = requestAnimationFrame(burstTick)
  })
}

onMounted(() => {
  load()
  initHunter()
})

onBeforeUnmount(() => {
  if (burstRaf) cancelAnimationFrame(burstRaf)
})
</script>

<template>
  <div class="home">
    <!-- 进入猎人协会的转场动画 -->
    <div v-if="hunterLeaving" class="hunter-transition">
      <canvas ref="burstCanvas" class="burst-canvas"></canvas>
      <div class="burst-flash"></div>
    </div>

    <header class="head">
      <div class="head-title">
        <h1>公开问卷广场</h1>
        <p>浏览并填写大家发布的公开问卷</p>
      </div>

      <div v-if="hunterReady" class="balloons">
        <div
          v-for="(b, i) in balloons"
          :key="i"
          class="balloon"
          :class="{ flown: b.flown }"
          @click="clickBalloon(i)"
        >
          <svg class="balloon-svg" viewBox="0 0 60 100" :style="{ animationDelay: (i * 0.45) + 's' }">
            <path class="b-str" d="M24 72 L26 82 M36 72 L34 82" />
            <ellipse class="b-hi" cx="21" cy="24" rx="9" ry="14" transform="rotate(-18 21 24)" />
            <path
              class="b-env"
              :fill="b.color"
              d="M30 2 C11 15 6 38 14 55 C19 67 26 73 30 77 C34 73 41 67 46 55 C54 38 49 15 30 2 Z"
            />
            <path class="b-basket" d="M22 84 h16 l-2.5 12 h-11 Z" />
            <text class="b-char" x="30" y="47" text-anchor="middle">{{ b.char }}</text>
          </svg>
        </div>
      </div>
    </header>

    <div class="search-box">
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <circle cx="11" cy="11" r="7" />
        <path d="M21 21l-4.3-4.3" />
      </svg>
      <input v-model="searchText" placeholder="搜索问卷题目" />
    </div>

    <div class="type-tabs">
      <button
        v-for="t in typeTabs"
        :key="t.key"
        class="type-tab"
        :class="{ active: currentType === t.key }"
        @click="setType(t.key)"
      >
        {{ t.label }}
      </button>
    </div>

    <div class="list-head">
      <h2>{{ currentLabel }}</h2>
      <span class="list-count">共 {{ filteredList.length }} 份</span>
    </div>

    <div v-if="loading" class="hint">加载中...</div>
    <div v-else-if="loadError" class="hint error">{{ loadError }}</div>

    <div v-else-if="list.length === 0" class="empty">
      <div class="empty-mark">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <rect x="3" y="4" width="18" height="16" rx="3" />
          <path d="M8 9h8M8 13h5" />
        </svg>
      </div>
      <div class="empty-title">暂无公开问卷</div>
      <div class="empty-desc">问卷发布后会展现在这里</div>
    </div>

    <div v-else-if="filteredList.length === 0" class="empty">
      <div class="empty-mark">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <circle cx="11" cy="11" r="7" />
          <path d="M21 21l-4.3-4.3" />
        </svg>
      </div>
      <div class="empty-title">没有找到符合条件的问卷</div>
      <div class="empty-desc">试试换个类型或关键词</div>
    </div>

    <div v-else class="grid">
      <div v-for="q in filteredList" :key="q.id" class="card" @click="browse(q)">
        <div class="card-top">
          <div class="author">
            <div class="avatar">{{ (q.author || '?').charAt(0) }}</div>
            <span class="author-name">{{ q.author }}</span>
            <span v-if="q.is_owner" class="mine-tag">我的</span>
          </div>
          <span class="badge">{{ typeLabel[q.type] || q.type }}</span>
        </div>

        <div class="title">{{ q.title }}</div>

        <div class="card-foot">
          <button class="action" :class="{ on: q.favorited }" @click.stop="toggle(q, 'favorite')">
            收藏 {{ q.favorite_count }}
          </button>
          <button class="action" :class="{ on: q.liked }" @click.stop="toggle(q, 'like')">
            点赞 {{ q.like_count }}
          </button>
          <button class="action" @click.stop="openShare(q)">分享</button>
          <span class="date">{{ (q.updated_at || '').slice(0, 10) }}</span>
        </div>

        <div v-if="q.is_owner" class="owner-actions">
          <button class="owner-btn" @click.stop="edit(q)">编辑</button>
          <button class="owner-btn danger" @click.stop="askDelete(q)">删除</button>
        </div>
      </div>
    </div>

    <div v-if="deleteTarget" class="mask" @click.self="deleteTarget = null">
      <div class="modal">
        <h3>删除问卷</h3>
        <p class="modal-text">确定要删除「{{ deleteTarget.title }}」吗？删除后无法恢复。</p>
        <div class="modal-actions">
          <button class="ghost" @click="deleteTarget = null">取消</button>
          <button class="danger-btn" :disabled="deleting" @click="confirmDelete">
            {{ deleting ? '删除中...' : '删除' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="shareTarget" class="mask" @click.self="shareTarget = null">
      <div class="share-modal">
        <div ref="shareRef" class="share-card">
          <div class="sc-head">
            <span class="sc-type">{{ typeLabel[shareTarget.type] || shareTarget.type }}</span>
            <div class="sc-title">{{ shareTarget.title }}</div>
          </div>
          <div class="sc-body">
            <div v-if="shareTarget.description" class="sc-desc">{{ shareTarget.description }}</div>
            <div class="sc-qr">
              <img v-if="qrDataUrl" :src="qrDataUrl" alt="二维码" />
            </div>
            <div class="sc-tip">扫一扫，立即参与</div>
          </div>
        </div>
        <div class="share-actions">
          <button class="ghost" @click="copyLink">{{ copied ? '已复制' : '复制链接' }}</button>
          <button class="primary" :disabled="generating" @click="downloadImage">
            {{ generating ? '生成中...' : '下载图片' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home {
  padding: 36px 40px;
  max-width: 1080px;
  margin: 0 auto;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 18px;
}

.head-title h1 {
  font-size: 24px;
  margin: 0 0 6px;
}

.head-title p {
  color: var(--muted);
  margin: 0;
}

.search-box {
  position: relative;
  width: 100%;
  margin-bottom: 22px;
}

.search-box svg {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  color: #94a3b8;
  pointer-events: none;
}

.search-box input {
  width: 100%;
  padding: 10px 14px 10px 36px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: #fff;
  font-size: 14px;
  outline: none;
  box-sizing: border-box;
}

.search-box input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12);
}

.type-tabs {
  display: flex;
  gap: 28px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 24px;
}

.type-tab {
  position: relative;
  padding: 10px 4px;
  border: none;
  background: transparent;
  font-size: 15px;
  font-weight: 500;
  color: var(--muted);
  cursor: pointer;
}

.type-tab:hover {
  color: var(--text);
}

.type-tab.active {
  color: var(--primary);
  font-weight: 600;
}

.type-tab.active::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: -1px;
  height: 2px;
  background: var(--primary);
  border-radius: 2px;
}

.list-head {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 16px;
}

.list-head h2 {
  font-size: 18px;
  margin: 0;
}

.list-count {
  color: var(--muted);
  font-size: 13px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.card {
  background: #fff;
  border-radius: 14px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
}

.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.author {
  display: flex;
  align-items: center;
  gap: 8px;
}

.avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
}

.author-name {
  font-size: 13px;
  color: var(--muted);
  font-weight: 500;
}

.badge {
  font-size: 12px;
  color: var(--primary);
  background: rgba(99, 102, 241, 0.08);
  padding: 3px 10px;
  border-radius: 20px;
  font-weight: 600;
}

.title {
  font-size: 17px;
  font-weight: 600;
  color: var(--text);
  line-height: 1.4;
}

.card-foot {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action {
  border: 1px solid var(--border);
  background: #fff;
  color: var(--muted);
  border-radius: 20px;
  padding: 6px 14px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}

.action:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.action.on {
  background: rgba(99, 102, 241, 0.08);
  border-color: var(--primary);
  color: var(--primary);
}

.date {
  margin-left: auto;
  font-size: 12px;
  color: #cbd5e1;
}

.empty {
  text-align: center;
  padding: 80px 0;
}

.empty-mark {
  color: #c7d2fe;
  width: 56px;
  height: 56px;
  margin: 0 auto 16px;
}

.empty-title {
  font-size: 16px;
  font-weight: 600;
}

.empty-desc {
  color: var(--muted);
  font-size: 14px;
  margin-top: 6px;
}

.hint {
  color: var(--muted);
  padding: 40px 0;
  text-align: center;
}

.hint.error {
  color: var(--danger);
}

.mine-tag {
  font-size: 11px;
  color: var(--primary);
  background: rgba(99, 102, 241, 0.1);
  padding: 2px 8px;
  border-radius: 20px;
  font-weight: 600;
}

.owner-actions {
  display: flex;
  gap: 8px;
  padding-top: 12px;
  margin-top: 4px;
  border-top: 1px solid var(--border);
}

.owner-btn {
  padding: 6px 16px;
  font-size: 13px;
  border: 1px solid var(--border);
  background: #fff;
  color: var(--muted);
  border-radius: 10px;
  cursor: pointer;
}

.owner-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.owner-btn.danger:hover {
  border-color: var(--danger);
  color: var(--danger);
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
  max-width: 400px;
  background: #fff;
  border-radius: 18px;
  padding: 28px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.modal h3 {
  margin: 0 0 12px;
  font-size: 18px;
}

.modal-text {
  color: var(--muted);
  font-size: 14px;
  line-height: 1.6;
  margin: 0 0 24px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.ghost {
  padding: 10px 20px;
  font-size: 14px;
  border: 1px solid var(--border);
  background: #fff;
  color: var(--muted);
  border-radius: 10px;
  cursor: pointer;
}

.ghost:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.danger-btn {
  padding: 10px 22px;
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  background: #ef4444;
  border: none;
  border-radius: 10px;
  cursor: pointer;
}

.danger-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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

.share-modal {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.share-card {
  width: 300px;
  max-width: 100%;
  border-radius: 20px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.sc-head {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  padding: 24px 24px 32px;
  text-align: center;
  color: #fff;
}

.sc-type {
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.22);
  padding: 4px 12px;
  border-radius: 20px;
  margin-bottom: 12px;
}

.sc-title {
  font-size: 18px;
  font-weight: 700;
  line-height: 1.4;
}

.sc-body {
  padding: 28px 24px;
  text-align: center;
}

.sc-desc {
  font-size: 13px;
  line-height: 1.6;
  color: #4b5563;
  text-align: left;
  background: #f8fafc;
  border-radius: 10px;
  padding: 10px 12px;
  margin-bottom: 16px;
  white-space: pre-wrap;
}

.sc-qr {
  width: 150px;
  margin: 0 auto;
  padding: 10px;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  background: #fff;
}

.sc-qr img {
  width: 100%;
  height: auto;
  display: block;
}

.sc-tip {
  font-size: 12px;
  color: #6b7280;
  margin-top: 14px;
}

.share-actions {
  display: flex;
  gap: 12px;
}

/* —— 猎人彩蛋：热气球 —— */
.balloons {
  display: flex;
  align-items: flex-end;
  gap: 10px;
}

.balloon {
  width: 46px;
  cursor: pointer;
  transition: transform 0.7s ease, opacity 0.7s ease;
}

.balloon:hover {
  filter: brightness(1.08);
}

.balloon-svg {
  width: 100%;
  height: auto;
  display: block;
  animation: balloon-float 3s ease-in-out infinite;
}

.b-str {
  stroke: #7c5c3a;
  stroke-width: 1.5;
  fill: none;
}

.b-hi {
  fill: #ffffff;
  opacity: 0.35;
}

.b-basket {
  fill: #8a5a2b;
}

.b-char {
  fill: #fff;
  font-size: 16px;
  font-weight: 700;
  font-family: 'KaiTi', 'STKaiti', 'Segoe Print', cursive;
}

.balloon.flown {
  transform: translateY(-160px);
  opacity: 0;
  pointer-events: none;
}

.balloon.flown .balloon-svg {
  animation: none;
}

@keyframes balloon-float {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-8px);
  }
}

/* —— 进入猎人协会的转场动画 —— */
.hunter-transition {
  position: fixed;
  inset: 0;
  z-index: 9999;
  pointer-events: none;
  background: #0a0705;
  animation: hunter-overlay-in 0.35s ease-out both;
}
@keyframes hunter-overlay-in {
  from { opacity: 0; }
  to { opacity: 1; }
}
.hunter-transition .burst-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}
.hunter-transition .burst-flash {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 50% 50%, #fff8e0 0%, #e8c878 28%, transparent 70%);
  animation: burst-flash 0.7s ease-out forwards;
}
@keyframes burst-flash {
  0% { opacity: 0; transform: scale(0.5); }
  35% { opacity: 1; transform: scale(1.1); }
  100% { opacity: 1; transform: scale(1.7); }
}

@media (max-width: 768px) {
  .home {
    padding: 20px 16px;
  }
  .head-title h1 {
    font-size: 20px;
  }
  .type-tabs {
    gap: 20px;
  }
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
