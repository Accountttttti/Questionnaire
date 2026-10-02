<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import QRCode from 'qrcode'
import html2canvas from 'html2canvas'

const route = useRoute()
const router = useRouter()
const qid = route.params.id

const q = ref(null)
const answers = ref([])
const error = ref('')
const loading = ref(true)
const submitting = ref(false)
const result = ref(null)

const current = ref(0)
const history = ref([])
const confirmResult = ref(null)

const typeLabel = { test: '测试问卷', relay: '接龙', exam: '考试' }

const shareOpen = ref(false)
const copied = ref(false)
const qrDataUrl = ref('')
const generating = ref(false)
const shareRef = ref(null)

function isAnswered(qi) {
  const a = answers.value[qi]
  const t = q.value.questions[qi].type
  if (t === 'multiple') return Array.isArray(a) && a.length > 0
  if (t === 'fill') return typeof a === 'string' && a.trim() !== ''
  return a !== null && a !== undefined
}

const answeredCount = computed(() =>
  q.value ? q.value.questions.filter((_, qi) => isAnswered(qi)).length : 0
)
const allAnswered = computed(() => q.value && answeredCount.value === q.value.questions.length)

const isJump = computed(() => q.value && q.value.result_mode === 'jump')
const curQuestion = computed(() => (q.value ? q.value.questions[current.value] : null))

async function load() {
  const res = await fetch(`/api/questionnaires/${qid}/public`, {
    headers: { Authorization: localStorage.getItem('token') || '' },
  })
  const data = await res.json()
  loading.value = false
  if (res.ok) {
    q.value = data
    answers.value = data.questions.map(() => null)
    current.value = 0
    history.value = []
    confirmResult.value = null
  } else {
    error.value = data.error || '加载失败'
  }
}

function pick(qi, oi) {
  answers.value[qi] = oi
}

function isChosen(qi, oi) {
  const a = answers.value[qi]
  return Array.isArray(a) && a.includes(oi)
}

function toggleMultiple(qi, oi) {
  const cur = answers.value[qi]
  const arr = Array.isArray(cur) ? cur.slice() : []
  const idx = arr.indexOf(oi)
  if (idx >= 0) arr.splice(idx, 1)
  else arr.push(oi)
  answers.value[qi] = arr
}

function jumpPick(qi, oi) {
  answers.value[qi] = oi
  const opt = q.value.questions[qi].options[oi]
  const jt = (opt && opt.jump_to) || ''
  if (jt.startsWith('r')) {
    confirmResult.value = jt.slice(1)
  } else if (jt.startsWith('q')) {
    const target = parseInt(jt.slice(1), 10) - 1
    if (target >= 0 && target < q.value.questions.length && target !== qi) {
      history.value.push(qi)
      current.value = target
    }
  } else if (qi < q.value.questions.length - 1) {
    history.value.push(qi)
    current.value = qi + 1
  }
}

function goBack() {
  if (history.value.length) {
    current.value = history.value.pop()
  }
}

function cancelConfirm() {
  confirmResult.value = null
}

async function confirmJumpSubmit() {
  if (!confirmResult.value) return
  submitting.value = true
  const res = await fetch(`/api/questionnaires/${qid}/submit`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: localStorage.getItem('token') || '',
    },
    body: JSON.stringify({ answers: answers.value, result_label: confirmResult.value }),
  })
  const data = await res.json()
  submitting.value = false
  if (res.ok) {
    result.value = data
    confirmResult.value = null
  } else {
    alert(data.error || '提交失败')
  }
}

async function submit() {
  if (!allAnswered.value) {
    alert('还有未作答的题目')
    return
  }
  submitting.value = true
  const res = await fetch(`/api/questionnaires/${qid}/submit`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: localStorage.getItem('token') || '',
    },
    body: JSON.stringify({ answers: answers.value }),
  })
  const data = await res.json()
  submitting.value = false
  if (res.ok) {
    result.value = data
  } else {
    alert(data.error || '提交失败')
  }
}

function restart() {
  answers.value = q.value.questions.map(() => null)
  result.value = null
  current.value = 0
  history.value = []
  confirmResult.value = null
}

async function openShare() {
  shareOpen.value = true
  try {
    const url = window.location.origin + '/fill/' + qid
    qrDataUrl.value = await QRCode.toDataURL(url, { width: 200, margin: 1 })
  } catch (e) {
    qrDataUrl.value = ''
  }
}

async function copyLink() {
  const url = window.location.origin + '/fill/' + qid
  try {
    await navigator.clipboard.writeText(url)
    copied.value = true
    setTimeout(() => (copied.value = false), 2000)
  } catch (e) {
    alert('复制失败，请手动复制：' + url)
  }
}

async function saveImage() {
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
    link.download = '结果分享.png'
    link.click()
  } catch (e) {
    alert('生成图片失败，请重试')
  } finally {
    el.style.boxShadow = prevShadow
    generating.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="fill">
    <div v-if="loading" class="hint">加载中...</div>

    <div v-else-if="error" class="hint">{{ error }}</div>

    <div v-else-if="result" class="result">
      <div v-if="q.type === 'exam'" class="exam-result">
        <div class="exam-score">{{ result.total_score }}<span class="exam-total"> / {{ result.full_score }} 分</span></div>
        <div class="exam-label">考试成绩</div>
      </div>
      <template v-else-if="isJump">
        <div class="jump-result">
          <div class="jump-badge">结果 {{ result.label }}</div>
          <div class="result-text" v-html="result.result_text"></div>
        </div>
      </template>
      <template v-else>
        <div class="score-circle">
          <span class="score-num">{{ result.total_score }}</span>
          <span class="score-label">总分</span>
        </div>
        <div class="result-text" v-html="result.result_text"></div>
      </template>
      <div class="result-actions">
        <button class="ghost" @click="restart">再答一次</button>
        <button class="ghost" @click="copyLink">{{ copied ? '已复制链接' : '复制分享链接' }}</button>
        <button class="primary" @click="openShare">分享图片</button>
        <button class="ghost" @click="router.push('/')">返回首页</button>
      </div>
    </div>

    <div v-else-if="isJump" class="form">
      <header class="head">
        <h1>{{ q.title }}</h1>
        <div class="progress">第 {{ current + 1 }} 题 / 共 {{ q.questions.length }} 题</div>
      </header>

      <div class="question">
        <div class="q-title">
          <span class="q-num">{{ current + 1 }}</span>
          {{ curQuestion.title }}
        </div>
        <div class="options">
          <div
            v-for="(o, oi) in curQuestion.options"
            :key="oi"
            class="option"
            :class="{ selected: answers[current] === oi }"
            @click="jumpPick(current, oi)"
          >
            <span class="radio" :class="{ on: answers[current] === oi }"></span>
            <span class="opt-text">{{ o.text }}</span>
          </div>
        </div>
      </div>

      <div class="nav-row">
        <button class="ghost" :disabled="!history.length" @click="goBack">上一题</button>
      </div>
    </div>

    <div v-else class="form">
      <header class="head">
        <h1>{{ q.title }}</h1>
        <div class="progress">已答 {{ answeredCount }} / {{ q.questions.length }} 题</div>
      </header>

      <div v-for="(question, qi) in q.questions" :key="qi" class="question">
        <div class="q-title">
          <span class="q-num">{{ qi + 1 }}</span>
          {{ question.title }}
        </div>
        <div v-if="question.type === 'multiple'" class="options">
          <div
            v-for="(o, oi) in question.options"
            :key="oi"
            class="option"
            :class="{ selected: isChosen(qi, oi) }"
            @click="toggleMultiple(qi, oi)"
          >
            <span class="checkbox" :class="{ on: isChosen(qi, oi) }"></span>
            <span class="opt-text">{{ o.text }}</span>
          </div>
        </div>

        <div v-else-if="question.type === 'fill'" class="options">
          <input v-model="answers[qi]" class="fill-input" placeholder="请输入你的答案" />
        </div>

        <div v-else class="options">
          <div
            v-for="(o, oi) in question.options"
            :key="oi"
            class="option"
            :class="{ selected: answers[qi] === oi }"
            @click="pick(qi, oi)"
          >
            <span class="radio" :class="{ on: answers[qi] === oi }"></span>
            <span class="opt-text">{{ o.text }}</span>
          </div>
        </div>
      </div>

      <button class="submit" :disabled="submitting" @click="submit">
        {{ submitting ? '提交中...' : '提交' }}
      </button>
    </div>

    <div v-if="confirmResult" class="share-mask" @click.self="cancelConfirm">
      <div class="confirm-panel">
        <div class="cp-title">已选到结果 {{ confirmResult }}</div>
        <div class="cp-desc">该选项会直接得出结果，是否提交问卷？</div>
        <div class="cp-actions">
          <button class="ghost" @click="cancelConfirm">返回答题</button>
          <button class="primary" :disabled="submitting" @click="confirmJumpSubmit">
            {{ submitting ? '提交中...' : '确认提交' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="shareOpen" class="share-mask" @click.self="shareOpen = false">
      <div class="share-panel">
        <div ref="shareRef" class="share-card">
          <div class="sc-head">
            <span class="sc-type">{{ typeLabel[q.type] || q.type }}</span>
            <div class="sc-title">{{ q.title }}</div>
            <div v-if="q.description" class="sc-desc">{{ q.description }}</div>
          </div>
          <div class="sc-body">
            <div v-if="isJump" class="jump-badge">结果 {{ result.label }}</div>
            <div v-else class="sc-score-circle">
              <span class="sc-score-num">{{ result.total_score }}</span>
              <span class="sc-score-label">{{ q.type === 'exam' ? '得分' : '总分' }}</span>
            </div>
            <div v-if="q.type === 'exam'" class="sc-result">满分 {{ result.full_score }} 分</div>
            <div v-else class="sc-result" v-html="result.result_text"></div>
            <div class="sc-qr">
              <img v-if="qrDataUrl" :src="qrDataUrl" alt="二维码" />
            </div>
            <div class="sc-tip">扫一扫，测测你的结果</div>
          </div>
        </div>

        <div class="share-actions">
          <button class="share-close" @click="shareOpen = false">关闭</button>
          <button class="primary" :disabled="generating" @click="saveImage">
            {{ generating ? '生成中...' : '保存图片' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fill {
  min-height: 100vh;
  padding: 32px 20px 80px;
  background: linear-gradient(135deg, #eef2ff 0%, #faf5ff 50%, #fdf2f8 100%);
}

.form {
  max-width: 640px;
  margin: 0 auto;
}

.head {
  text-align: center;
  margin-bottom: 28px;
}

.head h1 {
  font-size: 24px;
  margin: 0 0 10px;
}

.progress {
  color: var(--muted);
  font-size: 14px;
}

.question {
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.q-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 14px;
  line-height: 1.5;
}

.q-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 8px;
  background: rgba(99, 102, 241, 0.1);
  color: var(--primary);
  font-size: 13px;
  margin-right: 8px;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.option {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border: 1px solid var(--border);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.15s;
}

.option:hover {
  border-color: var(--primary);
}

.option.selected {
  border-color: var(--primary);
  background: rgba(99, 102, 241, 0.05);
}

.radio {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid #cbd5e1;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}

.radio.on {
  border-color: var(--primary);
}

.radio.on::after {
  content: '';
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--primary);
}

.opt-text {
  font-size: 14px;
  color: var(--text);
}

.submit {
  width: 100%;
  margin-top: 12px;
  padding: 15px;
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  border-radius: 14px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.submit:hover {
  opacity: 0.9;
}

.submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.result {
  max-width: 480px;
  margin: 40px auto;
  text-align: center;
  background: #fff;
  border-radius: 20px;
  padding: 48px 40px;
  box-shadow: 0 20px 60px rgba(99, 102, 241, 0.15);
}

.score-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin: 0 auto 24px;
}

.score-num {
  font-size: 44px;
  font-weight: 700;
  line-height: 1;
}

.score-label {
  font-size: 13px;
  opacity: 0.85;
  margin-top: 4px;
}

.result-text {
  font-size: 16px;
  line-height: 1.7;
  color: var(--text);
  margin: 0 0 28px;
}

.result-text img {
  max-width: 100%;
}

.primary {
  padding: 12px 28px;
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

.hint {
  text-align: center;
  color: var(--muted);
  padding: 80px 20px;
}

.result-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-actions button {
  width: 100%;
}

.ghost {
  padding: 12px 28px;
  font-size: 15px;
  font-weight: 600;
  color: var(--muted);
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 12px;
  cursor: pointer;
}

.ghost:hover {
  color: var(--primary);
  border-color: var(--primary);
}

.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.share-mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  z-index: 200;
  overflow-y: auto;
}

.share-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.share-card {
  width: 320px;
  max-width: 100%;
  border-radius: 20px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.sc-head {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  padding: 28px 24px 36px;
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

.sc-desc {
  font-size: 12px;
  line-height: 1.5;
  opacity: 0.92;
  margin-top: 8px;
  white-space: pre-wrap;
}

.sc-body {
  padding: 24px 24px 28px;
  text-align: center;
}

.sc-score-circle {
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

.sc-score-num {
  font-size: 40px;
  font-weight: 700;
  line-height: 1;
}

.sc-score-label {
  font-size: 12px;
  opacity: 0.85;
  margin-top: 4px;
}

.sc-result {
  font-size: 14px;
  line-height: 1.7;
  color: #1f2937;
  margin-bottom: 20px;
}

.sc-result img {
  max-width: 100%;
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
  margin-top: 12px;
}

.share-actions {
  display: flex;
  gap: 12px;
}

.share-close {
  padding: 10px 22px;
  font-size: 14px;
  font-weight: 500;
  color: #fff;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 12px;
  cursor: pointer;
}

.share-close:hover {
  background: rgba(255, 255, 255, 0.1);
}

.checkbox {
  width: 18px;
  height: 18px;
  border-radius: 5px;
  border: 2px solid #cbd5e1;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}

.checkbox.on {
  border-color: var(--primary);
  background: var(--primary);
}

.checkbox.on::after {
  content: '';
  width: 9px;
  height: 5px;
  border-left: 2px solid #fff;
  border-bottom: 2px solid #fff;
  transform: rotate(-45deg) translate(1px, -1px);
}

.fill-input {
  width: 100%;
  padding: 12px 16px;
  font-size: 14px;
  border: 1px solid var(--border);
  border-radius: 12px;
  outline: none;
  box-sizing: border-box;
}

.fill-input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12);
}

.exam-result {
  text-align: center;
  padding: 24px 0 28px;
}

.exam-score {
  font-size: 52px;
  font-weight: 700;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  line-height: 1;
}

.exam-total {
  font-size: 22px;
  font-weight: 600;
  color: var(--muted);
}

.exam-label {
  margin-top: 12px;
  color: var(--muted);
  font-size: 14px;
}

.jump-result {
  text-align: center;
  padding: 8px 0 4px;
}

.jump-badge {
  display: inline-block;
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  padding: 6px 18px;
  border-radius: 20px;
  margin-bottom: 20px;
}

.nav-row {
  max-width: 640px;
  margin: 0 auto;
  display: flex;
  justify-content: flex-start;
}

.ghost:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.confirm-panel {
  width: 320px;
  max-width: 100%;
  background: #fff;
  border-radius: 20px;
  padding: 28px 24px;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.cp-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 10px;
}

.cp-desc {
  font-size: 14px;
  color: var(--muted);
  line-height: 1.6;
  margin-bottom: 24px;
}

.cp-actions {
  display: flex;
  gap: 12px;
}

.cp-actions button {
  flex: 1;
}
</style>
