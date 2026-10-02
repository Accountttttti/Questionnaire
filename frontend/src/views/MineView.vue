<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import QRCode from 'qrcode'
import html2canvas from 'html2canvas'

const router = useRouter()

const mine = ref([])
const actions = ref([])
const loading = ref(true)

const usageData = ref([])
const usageFilter = ref('all')
const selectedRespId = ref({})
const generating = ref(false)
const dlCard = ref(null)
const dl = ref(null)
const deleteRespTarget = ref(null)
const deletingResp = ref(false)

const activeSection = ref('created')

const sections = [
  { key: 'created', label: '我的问卷' },
  { key: 'usage', label: '我的使用' },
  { key: 'like', label: '喜爱问卷' },
  { key: 'favorite', label: '收藏问卷' },
]

const typeLabel = { test: '测试问卷', relay: '接龙', exam: '考试' }
const statusLabel = { draft: '草稿', published: '已发布', stopped: '已停止' }

const sectionLabel = computed(() => sections.find((s) => s.key === activeSection.value).label)

const currentList = computed(() => {
  if (activeSection.value === 'created') return mine.value
  return actions.value.filter((a) => a.action === activeSection.value)
})

// 筛选：搜索 / 状态 / 时间排序
const searchText = ref('')
const statusFilter = ref('all')
const sortOrder = ref('desc')

const filteredList = computed(() => {
  let list = mine.value.slice()
  if (statusFilter.value === 'published') {
    list = list.filter((q) => q.status === 'published')
  } else if (statusFilter.value === 'unpublished') {
    list = list.filter((q) => q.status !== 'published')
  }
  const kw = searchText.value.trim().toLowerCase()
  if (kw) {
    list = list.filter((q) => (q.title || '').toLowerCase().includes(kw))
  }
  list.sort((a, b) => {
    const ta = a.updated_at || ''
    const tb = b.updated_at || ''
    return sortOrder.value === 'desc' ? tb.localeCompare(ta) : ta.localeCompare(tb)
  })
  return list
})

const usageList = computed(() =>
  usageFilter.value === 'mine' ? usageData.value.filter((q) => q.mine) : usageData.value
)

const shownCount = computed(() => {
  if (activeSection.value === 'created') return filteredList.value.length
  if (activeSection.value === 'usage') return usageList.value.length
  return currentList.value.length
})

const emptyText = computed(() => {
  if (activeSection.value === 'created') {
    return mine.value.length === 0
      ? '还没有创建过问卷，点击左上角「新建」开始'
      : '没有找到符合条件的问卷'
  }
  if (activeSection.value === 'usage') return '还没有作答过任何问卷'
  return '暂无内容'
})

function toggleSort() {
  sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'
}

// 新建问卷
const showCreate = ref(false)
const newType = ref('test')
const newMode = ref('score')
const newTitle = ref('')
const newDesc = ref('')
const creating = ref(false)

const types = [
  { key: 'test', label: '测试问卷', desc: '计分出结果', ready: true },
  { key: 'exam', label: '考试', desc: '出题判分', ready: true },
]

// 分享问卷
const shareTarget = ref(null)
const qrDataUrl = ref('')
const copied = ref(false)

const shareLink = computed(() =>
  shareTarget.value ? window.location.origin + '/fill/' + shareTarget.value.id : ''
)

// 删除问卷
const deleteTarget = ref(null)
const deleting = ref(false)

function authHeaders() {
  return { Authorization: localStorage.getItem('token') || '' }
}

function formatTime(s) {
  if (!s) return '—'
  const [d, t] = s.split(' ')
  if (!d) return s
  const [y, m, day] = d.split('-')
  const time = t ? t.slice(0, 5) : ''
  return `${y}.${Number(m)}.${Number(day)}` + (time ? ` ${time}` : '')
}

async function load() {
  const mineRes = await fetch('/api/questionnaires/mine', {
    headers: authHeaders(),
  })
  const mineData = await mineRes.json()
  if (mineRes.ok) mine.value = mineData

  const actionsRes = await fetch('/api/me/actions', {
    headers: authHeaders(),
  })
  const actionsData = await actionsRes.json()
  if (actionsRes.ok) actions.value = actionsData

  const usageRes = await fetch('/api/me/responses', {
    headers: authHeaders(),
  })
  const usageDataRes = await usageRes.json()
  if (usageRes.ok) usageData.value = usageDataRes

  loading.value = false
}

function pickType(t) {
  if (!t.ready) {
    alert('该类型开发中')
    return
  }
  newType.value = t.key
}

async function create() {
  if (!newTitle.value.trim()) {
    alert('请填写问卷名')
    return
  }
  creating.value = true
  const res = await fetch('/api/questionnaires', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({
      type: newType.value,
      title: newTitle.value,
      description: newDesc.value,
      result_mode: newType.value === 'test' ? newMode.value : 'score',
    }),
  })
  const data = await res.json()
  creating.value = false
  if (res.ok) {
    router.push(`/editor/${data.id}`)
  } else {
    alert(data.error || '创建失败')
  }
}

function openCreate() {
  newType.value = 'test'
  newMode.value = 'score'
  newTitle.value = ''
  newDesc.value = ''
  showCreate.value = true
}

function open(q) {
  router.push(`/fill/${q.id}`)
}

function edit(q) {
  router.push(`/editor/${q.id}`)
}

async function openShare(q) {
  shareTarget.value = q
  qrDataUrl.value = ''
  copied.value = false
  try {
    const url = window.location.origin + '/fill/' + q.id
    qrDataUrl.value = await QRCode.toDataURL(url, { width: 180, margin: 1 })
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

function selectedId(q) {
  const stored = selectedRespId.value[q.id]
  if (stored && q.responses.some((r) => r.id === stored)) return stored
  return q.responses[0] && q.responses[0].id
}

function currentResp(q) {
  const id = selectedId(q)
  return q.responses.find((r) => r.id === id) || q.responses[0]
}

function selectAttempt(q, e) {
  selectedRespId.value[q.id] = Number(e.target.value)
}

function askDeleteResp(q, r) {
  deleteRespTarget.value = { q, r }
}

async function confirmDeleteResp() {
  const t = deleteRespTarget.value
  if (!t) return
  deletingResp.value = true
  const res = await fetch(`/api/responses/${t.r.id}`, {
    method: 'DELETE',
    headers: authHeaders(),
  })
  deletingResp.value = false
  if (res.ok) {
    deleteRespTarget.value = null
    load()
  } else {
    alert('删除失败')
  }
}

async function downloadImage(q, r) {
  if (!r) return
  dl.value = {
    title: q.title,
    type: q.type,
    total_score: r.total_score,
    full_score: q.full_score,
    result_text: r.result_text,
    created_at: r.created_at,
  }
  await nextTick()
  const el = dlCard.value
  if (!el) return
  const prevShadow = el.style.boxShadow
  el.style.boxShadow = 'none'
  generating.value = true
  try {
    const canvas = await html2canvas(el, { scale: 2, useCORS: true, backgroundColor: null })
    const link = document.createElement('a')
    link.href = canvas.toDataURL('image/png')
    link.download = '测试结果.png'
    link.click()
  } catch (e) {
    alert('生成图片失败，请重试')
  } finally {
    el.style.boxShadow = prevShadow
    generating.value = false
  }
}

async function toggleStatus(q) {
  const target = q.status === 'published' ? 'stopped' : 'published'
  const res = await fetch(`/api/questionnaires/${q.id}/status`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ status: target }),
  })
  const data = await res.json()
  if (res.ok) {
    load()
  } else {
    alert(data.error || '操作失败')
  }
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
    headers: authHeaders(),
  })
  deleting.value = false
  if (res.ok) {
    deleteTarget.value = null
    load()
  } else {
    alert('删除失败')
  }
}

onMounted(load)
</script>

<template>
  <div class="mine">
    <aside class="sidebar">
      <button class="new-btn" @click="openCreate">＋ 新建</button>

      <nav class="side-nav">
        <button
          v-for="s in sections"
          :key="s.key"
          class="side-item"
          :class="{ active: activeSection === s.key }"
          @click="activeSection = s.key"
        >
          {{ s.label }}
        </button>
      </nav>
    </aside>

    <main class="main">
      <header class="head">
        <h1>{{ sectionLabel }}</h1>
        <span class="count">共 {{ shownCount }} 份</span>
      </header>

      <div v-if="loading" class="hint">加载中...</div>

      <template v-else-if="activeSection === 'created'">
        <div class="toolbar">
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
            <input v-model="searchText" placeholder="搜索问卷名" />
          </div>

          <div class="status-filter">
            <button :class="{ active: statusFilter === 'all' }" @click="statusFilter = 'all'">全部</button>
            <button :class="{ active: statusFilter === 'published' }" @click="statusFilter = 'published'">已发布</button>
            <button :class="{ active: statusFilter === 'unpublished' }" @click="statusFilter = 'unpublished'">未发布</button>
          </div>

          <button class="sort-toggle" @click="toggleSort">
            {{ sortOrder === 'desc' ? '时间倒序' : '时间正序' }}
            <span class="arrow">{{ sortOrder === 'desc' ? '↓' : '↑' }}</span>
          </button>
        </div>

        <div v-if="filteredList.length === 0" class="hint">{{ emptyText }}</div>
        <div v-else class="list">
          <div v-for="q in filteredList" :key="q.id" class="item">
            <div class="row1">
              <div class="title-group">
                <span class="title" @click="open(q)">{{ q.title }}</span>
                <span class="type-badge">{{ typeLabel[q.type] || q.type }}</span>
              </div>
              <div class="meta">
                <span>ID：{{ q.id }}</span>
                <span class="sep">|</span>
                <span>{{ statusLabel[q.status] || q.status }}</span>
                <span class="sep">|</span>
                <span>答卷：{{ q.response_count || 0 }}</span>
                <span class="sep">|</span>
                <span>{{ formatTime(q.published_at) }}</span>
              </div>
            </div>

            <div class="row2">
              <div class="actions">
                <button class="act" @click="edit(q)">编辑</button>
                <button class="act" @click="openShare(q)">分享</button>
              </div>
              <div class="right-actions">
                <button
                  class="toggle"
                  :class="{ live: q.status === 'published' }"
                  @click="toggleStatus(q)"
                >
                  {{ q.status === 'published' ? '发布中' : '发布' }}
                </button>
                <button class="del" @click="askDelete(q)">删除</button>
              </div>
            </div>
          </div>
        </div>
      </template>

      <template v-else-if="activeSection === 'usage'">
        <div class="usage-filter">
          <button :class="{ active: usageFilter === 'all' }" @click="usageFilter = 'all'">所有</button>
          <button :class="{ active: usageFilter === 'mine' }" @click="usageFilter = 'mine'">我的</button>
        </div>

        <div v-if="usageList.length === 0" class="hint">{{ emptyText }}</div>
        <div v-else class="list">
          <div v-for="q in usageList" :key="q.id" class="item">
            <div class="row1">
              <div class="title-group">
                <span class="title" @click="open(q)">{{ q.title }}</span>
                <span class="type-badge">{{ typeLabel[q.type] || q.type }}</span>
                <span v-if="q.mine" class="mine-tag">我的</span>
              </div>
              <div class="meta">共答 {{ q.responses.length }} 次</div>
            </div>

            <div class="row2 usage-row">
              <select class="attempt-select" :value="selectedId(q)" @change="selectAttempt(q, $event)">
                <option v-for="(r, ri) in q.responses" :key="r.id" :value="r.id">
                  第 {{ q.responses.length - ri }} 次 · {{ r.total_score }} 分 · {{ formatTime(r.created_at) }}
                </option>
              </select>
              <div class="actions">
                <button class="act" :disabled="generating" @click="downloadImage(q, currentResp(q))">
                  {{ generating ? '生成中...' : '下载图片' }}
                </button>
                <button class="act danger" @click="askDeleteResp(q, currentResp(q))">删除</button>
              </div>
            </div>
          </div>
        </div>
      </template>

      <template v-else>
        <div v-if="currentList.length === 0" class="hint">暂无内容</div>
        <div v-else class="list">
          <div v-for="q in currentList" :key="q.id" class="item" @click="open(q)">
            <div class="row1">
              <div class="title-group">
                <span class="title">{{ q.title }}</span>
                <span class="type-badge">{{ typeLabel[q.type] || q.type }}</span>
              </div>
              <div class="meta">
                <span>{{ statusLabel[q.status] || q.status }}</span>
                <span class="sep">|</span>
                <span>{{ formatTime(q.updated_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </template>
    </main>

    <!-- 新建弹窗 -->
    <div v-if="showCreate" class="mask" @click.self="showCreate = false">
      <div class="modal">
        <h2>新建问卷</h2>

        <div class="type-list">
          <div
            v-for="t in types"
            :key="t.key"
            class="type-item"
            :class="{ active: newType === t.key && t.ready }"
            @click="pickType(t)"
          >
            <div class="type-label">{{ t.label }}</div>
            <div class="type-desc">{{ t.desc }}</div>
          </div>
        </div>

        <div v-if="newType === 'test'" class="mode-row">
          <span class="mode-label">结果方式</span>
          <div class="mode-options">
            <button :class="{ active: newMode === 'score' }" @click="newMode = 'score'">计分出结果</button>
            <button :class="{ active: newMode === 'jump' }" @click="newMode = 'jump'">跳转出结果</button>
          </div>
        </div>

        <input v-model="newTitle" class="title-input" placeholder="问卷名称" @keyup.enter="create" />
        <textarea v-model="newDesc" class="desc-input" placeholder="问卷介绍（选填）" rows="3"></textarea>

        <div class="modal-actions">
          <button class="ghost" @click="showCreate = false">取消</button>
          <button class="primary" :disabled="creating" @click="create">
            {{ creating ? '创建中...' : '创建' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 分享弹窗 -->
    <div v-if="shareTarget" class="mask" @click.self="shareTarget = null">
      <div class="share-modal">
        <h3>分享问卷</h3>
        <p class="share-title">{{ shareTarget.title }}</p>

        <div class="share-row">
          <span class="share-label">链接</span>
          <span class="share-url">{{ shareLink }}</span>
          <button class="copy-btn" @click="copyLink">{{ copied ? '已复制' : '复制' }}</button>
        </div>

        <div class="share-row qr-row">
          <span class="share-label">二维码</span>
          <div class="qr-box">
            <img v-if="qrDataUrl" :src="qrDataUrl" alt="二维码" />
            <span v-else class="qr-loading">生成中...</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 删除弹窗 -->
    <div v-if="deleteTarget" class="mask" @click.self="deleteTarget = null">
      <div class="confirm-modal">
        <h3>删除问卷</h3>
        <p class="confirm-text">确定要删除「{{ deleteTarget.title }}」吗？删除后无法恢复。</p>
        <div class="modal-actions">
          <button class="ghost" @click="deleteTarget = null">取消</button>
          <button class="danger-btn" :disabled="deleting" @click="confirmDelete">
            {{ deleting ? '删除中...' : '删除' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 删除作答记录弹窗 -->
    <div v-if="deleteRespTarget" class="mask" @click.self="deleteRespTarget = null">
      <div class="confirm-modal">
        <h3>删除作答记录</h3>
        <p class="confirm-text">
          确定删除「{{ deleteRespTarget.q.title }}」的这条记录吗？（{{ deleteRespTarget.r.total_score }} 分 · {{ formatTime(deleteRespTarget.r.created_at) }}）
        </p>
        <div class="modal-actions">
          <button class="ghost" @click="deleteRespTarget = null">取消</button>
          <button class="danger-btn" :disabled="deletingResp" @click="confirmDeleteResp">
            {{ deletingResp ? '删除中...' : '删除' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 离屏渲染：下载结果图 -->
    <div class="dl-offstage" aria-hidden="true">
      <div v-if="dl" ref="dlCard" class="dl-card">
        <div class="dl-head">
          <span class="dl-type">{{ typeLabel[dl.type] || dl.type }}</span>
          <div class="dl-title">{{ dl.title }}</div>
        </div>
        <div class="dl-body">
          <div class="dl-score-circle">
            <span class="dl-num">{{ dl.total_score }}</span>
            <span class="dl-label">{{ dl.type === 'exam' ? '得分' : '总分' }}</span>
          </div>
          <div v-if="dl.type === 'exam'" class="dl-result">满分 {{ dl.full_score }} 分</div>
          <div v-else class="dl-result" v-html="dl.result_text"></div>
          <div class="dl-time">{{ formatTime(dl.created_at) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mine {
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
  gap: 20px;
}

.new-btn {
  padding: 13px;
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  border-radius: 12px;
  cursor: pointer;
}

.new-btn:hover {
  opacity: 0.92;
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

.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.search-box {
  position: relative;
  flex: 1;
  max-width: 260px;
  min-width: 180px;
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
  padding: 9px 14px 9px 36px;
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

.status-filter {
  display: flex;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 3px;
  gap: 2px;
}

.status-filter button {
  padding: 6px 14px;
  border: none;
  background: transparent;
  font-size: 13px;
  color: var(--muted);
  border-radius: 8px;
  cursor: pointer;
  white-space: nowrap;
}

.status-filter button.active {
  background: rgba(99, 102, 241, 0.08);
  color: var(--primary);
  font-weight: 600;
}

.sort-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 9px 14px;
  border: 1px solid var(--border);
  background: #fff;
  color: var(--muted);
  border-radius: 10px;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
}

.sort-toggle:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.sort-toggle .arrow {
  font-size: 12px;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.item {
  background: #fff;
  border-radius: 14px;
  padding: 18px 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: transform 0.15s, box-shadow 0.15s;
}

.item:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
}

.row1 {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.title-group {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 360px;
}

.title:hover {
  color: var(--primary);
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

.meta {
  flex-shrink: 0;
  font-size: 12px;
  color: var(--muted);
  white-space: nowrap;
}

.meta .sep {
  margin: 0 8px;
  color: #e5e7eb;
}

.row2 {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.actions {
  display: flex;
  gap: 8px;
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

.right-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

.toggle {
  padding: 0;
  font-size: 13px;
  border: none;
  background: none;
  color: var(--primary);
  cursor: pointer;
  font-weight: 500;
}

.toggle:hover {
  text-decoration: underline;
}

.toggle.live {
  color: #059669;
}

.del {
  padding: 0;
  font-size: 13px;
  border: none;
  background: none;
  color: #cbd5e1;
  cursor: pointer;
}

.del:hover {
  color: var(--danger);
}

.hint {
  color: var(--muted);
  padding: 60px 0;
  text-align: center;
}

.mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  z-index: 200;
}

.modal {
  width: 100%;
  max-width: 440px;
  background: #fff;
  border-radius: 20px;
  padding: 28px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.modal h2 {
  margin: 0 0 20px;
  font-size: 20px;
}

.type-list {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.type-item {
  flex: 1;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px 12px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.type-item.active {
  border-color: var(--primary);
  background: rgba(99, 102, 241, 0.06);
}

.type-label {
  font-weight: 600;
  margin-bottom: 4px;
}

.type-desc {
  font-size: 12px;
  color: #94a3b8;
}

.mode-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.mode-label {
  flex-shrink: 0;
  font-size: 14px;
  color: var(--muted);
}

.mode-options {
  display: flex;
  gap: 8px;
  flex: 1;
}

.mode-options button {
  flex: 1;
  padding: 9px 12px;
  border: 1px solid var(--border);
  background: #fff;
  color: var(--muted);
  border-radius: 10px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.15s;
}

.mode-options button.active {
  border-color: var(--primary);
  background: rgba(99, 102, 241, 0.06);
  color: var(--primary);
  font-weight: 600;
}

.title-input {
  width: 100%;
  padding: 12px 16px;
  font-size: 15px;
  border: 1px solid var(--border);
  border-radius: 12px;
  outline: none;
  margin-bottom: 12px;
  box-sizing: border-box;
}

.title-input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
}

.desc-input {
  width: 100%;
  padding: 12px 16px;
  font-size: 14px;
  font-family: inherit;
  border: 1px solid var(--border);
  border-radius: 12px;
  outline: none;
  resize: vertical;
  margin-bottom: 20px;
  box-sizing: border-box;
}

.desc-input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.ghost {
  padding: 10px 18px;
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

.share-modal {
  width: 100%;
  max-width: 460px;
  background: #fff;
  border-radius: 20px;
  padding: 28px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.share-modal h3 {
  margin: 0 0 6px;
  font-size: 20px;
}

.share-title {
  color: var(--muted);
  font-size: 14px;
  margin: 0 0 24px;
}

.share-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.share-label {
  width: 52px;
  flex-shrink: 0;
  font-size: 14px;
  color: var(--muted);
}

.share-url {
  flex: 1;
  min-width: 0;
  font-size: 13px;
  color: var(--text);
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.copy-btn {
  flex-shrink: 0;
  padding: 9px 18px;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  border-radius: 9px;
  cursor: pointer;
}

.copy-btn:hover {
  opacity: 0.92;
}

.qr-row {
  align-items: flex-start;
}

.qr-box {
  width: 180px;
  height: 180px;
  border: 1px solid var(--border);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
}

.qr-box img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 14px;
}

.qr-loading {
  color: var(--muted);
  font-size: 13px;
}

.confirm-modal {
  width: 100%;
  max-width: 400px;
  background: #fff;
  border-radius: 18px;
  padding: 28px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.confirm-modal h3 {
  margin: 0 0 12px;
  font-size: 18px;
}

.confirm-text {
  color: var(--muted);
  font-size: 14px;
  line-height: 1.6;
  margin: 0 0 24px;
}

.usage-filter {
  display: inline-flex;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 3px;
  gap: 2px;
  margin-bottom: 16px;
}

.usage-filter button {
  padding: 6px 16px;
  border: none;
  background: transparent;
  font-size: 13px;
  color: var(--muted);
  border-radius: 8px;
  cursor: pointer;
  white-space: nowrap;
}

.usage-filter button.active {
  background: rgba(99, 102, 241, 0.08);
  color: var(--primary);
  font-weight: 600;
}

.mine-tag {
  flex-shrink: 0;
  font-size: 12px;
  color: #059669;
  background: rgba(16, 185, 129, 0.1);
  padding: 3px 10px;
  border-radius: 20px;
  font-weight: 600;
}

.usage-row {
  align-items: center;
}

.attempt-select {
  flex: 1;
  max-width: 320px;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: #fff;
  font-size: 13px;
  color: var(--text);
  outline: none;
  cursor: pointer;
}

.attempt-select:focus {
  border-color: var(--primary);
}

.act.danger:hover {
  border-color: var(--danger);
  color: var(--danger);
}

.act:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.dl-offstage {
  position: fixed;
  top: 0;
  left: -10000px;
}

.dl-card {
  width: 320px;
  border-radius: 20px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.dl-head {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  padding: 28px 24px 36px;
  text-align: center;
  color: #fff;
}

.dl-type {
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.22);
  padding: 4px 12px;
  border-radius: 20px;
  margin-bottom: 12px;
}

.dl-title {
  font-size: 18px;
  font-weight: 700;
  line-height: 1.4;
}

.dl-body {
  padding: 24px 24px 28px;
  text-align: center;
}

.dl-score-circle {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}

.dl-num {
  font-size: 40px;
  font-weight: 700;
  line-height: 1;
}

.dl-label {
  font-size: 12px;
  opacity: 0.85;
  margin-top: 4px;
}

.dl-result {
  font-size: 14px;
  line-height: 1.7;
  color: #1f2937;
  margin-bottom: 16px;
}

.dl-result img {
  max-width: 100%;
}

.dl-time {
  font-size: 12px;
  color: #9ca3af;
}
</style>
