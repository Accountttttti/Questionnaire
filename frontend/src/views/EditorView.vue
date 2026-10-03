<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const qid = route.params.id

const title = ref('')
const description = ref('')
const questions = ref([])
const result_cards = ref([])
const status = ref('draft')
const qtype = ref('test')
const fullScore = ref(null)
const mode = ref('score')
const resultLabels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
const saving = ref(false)
const saved = ref(false)
const excelInput = ref(null)
const cardRefs = []

function newScaleOptions() {
  const labels = ['完全不符合', '不符合', '中立', '符合', '完全符合']
  return labels.map((text, i) => ({ text, score: i + 1 }))
}

const examTypeLabel = { single: '单选题', multiple: '多选题', judge: '判断题', fill: '填空题' }

function addQuestion(type) {
  if (qtype.value === 'exam') {
    addExamQuestion(type)
  } else if (mode.value === 'jump') {
    questions.value.push({
      type: 'single',
      title: '',
      options: ['', '', '', ''].map(() => ({ text: '', jump_to: '' })),
    })
  } else if (type === 'scale') {
    questions.value.push({ type, title: '', options: newScaleOptions() })
  } else {
    questions.value.push({
      type,
      title: '',
      options: [
        { text: '', score: 0 },
        { text: '', score: 0 },
      ],
    })
  }
}

function addExamQuestion(type) {
  if (type === 'judge') {
    questions.value.push({
      type, title: '', score: 5,
      options: [
        { text: '对', is_correct: true },
        { text: '错', is_correct: false },
      ],
    })
  } else if (type === 'fill') {
    questions.value.push({ type, title: '', score: 5, answer: '' })
  } else {
    questions.value.push({
      type, title: '', score: 5,
      options: [
        { text: '', is_correct: false },
        { text: '', is_correct: false },
        { text: '', is_correct: false },
        { text: '', is_correct: false },
      ],
    })
  }
}

function removeQuestion(i) {
  questions.value.splice(i, 1)
}

function moveQuestion(i, dir) {
  const j = i + dir
  if (j < 0 || j >= questions.value.length) return
  const [item] = questions.value.splice(i, 1)
  questions.value.splice(j, 0, item)
}

function addOption(qi) {
  let opt
  if (qtype.value === 'exam') opt = { text: '', is_correct: false }
  else if (mode.value === 'jump') opt = { text: '', jump_to: '' }
  else opt = { text: '', score: 0 }
  questions.value[qi].options.push(opt)
}

function setCorrect(q, oi) {
  q.options.forEach((o, i) => { o.is_correct = i === oi })
}

const totalQuestionScore = computed(() =>
  questions.value.reduce((s, q) => s + (Number(q.score) || 0), 0)
)

function removeOption(qi, oi) {
  questions.value[qi].options.splice(oi, 1)
}

function toggleReverse(qi) {
  questions.value[qi].options.forEach((o) => {
    o.score = 6 - o.score
  })
}

function uid() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
}

function addCard() {
  if (mode.value === 'jump') {
    result_cards.value.push({ _id: uid(), label: nextResultLabel(), text: '' })
  } else {
    result_cards.value.push({ _id: uid(), min_score: 0, max_score: 0, text: '' })
  }
}

function nextResultLabel() {
  const used = new Set(result_cards.value.map((c) => c.label).filter(Boolean))
  for (let i = 0; i < 26; i++) {
    const ch = String.fromCharCode(65 + i)
    if (!used.has(ch)) return ch
  }
  return 'Z'
}

function resultLabelUsedByOthers(qi, oi, label) {
  for (let i = 0; i < questions.value.length; i++) {
    const opts = questions.value[i].options || []
    for (let j = 0; j < opts.length; j++) {
      if (i === qi && j === oi) continue
      if (opts[j].jump_to === 'r' + label) return true
    }
  }
  return false
}

function jumpType(jt) {
  if (!jt) return 'next'
  if (jt.startsWith('q')) return 'q'
  return 'r'
}

function jumpQTarget(jt) {
  return jt && jt.startsWith('q') ? jt.slice(1) : ''
}

function jumpRTarget(jt) {
  return jt && jt.startsWith('r') ? jt.slice(1) : ''
}

function setJumpType(qi, oi, type) {
  const opt = questions.value[qi].options[oi]
  if (type === 'next') {
    opt.jump_to = ''
  } else if (type === 'q') {
    const target = questions.value.findIndex((_, i) => i !== qi)
    opt.jump_to = 'q' + (target >= 0 ? target + 1 : qi + 1)
  } else if (type === 'r') {
    const c = result_cards.value.find((cc) => !resultLabelUsedByOthers(qi, oi, cc.label))
    opt.jump_to = 'r' + (c ? c.label : '')
  }
}

function setJumpQTarget(qi, oi, target) {
  questions.value[qi].options[oi].jump_to = 'q' + target
}

function setJumpRTarget(qi, oi, label) {
  questions.value[qi].options[oi].jump_to = 'r' + label
}

function questionBadge(qi) {
  if (qtype.value === 'exam') return examTypeLabel[questions.value[qi].type] || questions.value[qi].type
  if (mode.value === 'jump') return '第 ' + (qi + 1) + ' 题'
  return questions.value[qi].type === 'scale' ? '量表题' : '单选题'
}

function navToQuestion(e) {
  const num = parseInt(e.target.value, 10)
  e.target.value = ''
  if (!num || num < 1) return
  const target = num - 1
  while (questions.value.length <= target) {
    questions.value.push({
      type: 'single',
      title: '',
      options: ['', '', '', ''].map(() => ({ text: '', jump_to: '' })),
    })
  }
  nextTick(() => {
    const el = cardRefs[target]
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}

function removeCard(i) {
  result_cards.value.splice(i, 1)
}

const cardEditors = ref([])
let savedRange = null

function setCardEditor(ci, el) {
  if (!el) return
  cardEditors.value[ci] = el
  if (!el.dataset.rtfInit) {
    el.innerHTML = result_cards.value[ci]?.text || ''
    el.dataset.rtfInit = '1'
  }
}

function saveCardRange() {
  const sel = window.getSelection()
  if (sel && sel.rangeCount > 0) savedRange = sel.getRangeAt(0)
}

function focusCard(ci) {
  const el = cardEditors.value[ci]
  if (!el) return
  el.focus()
  if (savedRange) {
    const sel = window.getSelection()
    sel.removeAllRanges()
    sel.addRange(savedRange)
  }
}

function exec(ci, command, value = null) {
  focusCard(ci)
  document.execCommand(command, false, value)
}

const presetColors = ['#000000', '#6b7280', '#ef4444', '#f97316', '#f59e0b', '#10b981', '#3b82f6', '#6366f1', '#8b5cf6', '#ec4899']

const fontSizeOptions = [
  { label: '小', value: '3' },
  { label: '中', value: '4' },
  { label: '大', value: '5' },
  { label: '特大', value: '6' },
  { label: '超大', value: '7' },
]

function setFontSize(ci, value) {
  if (!value) return
  focusCard(ci)
  document.execCommand('styleWithCSS', false, true)
  document.execCommand('fontSize', false, value)
}

function onRtfInput(ci, e) {
  const c = result_cards.value[ci]
  if (c) c.text = e.target.innerHTML
}

async function insertImage(ci) {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.onchange = async () => {
    const file = input.files && input.files[0]
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
      exec(ci, 'insertImage', data.url)
    } else {
      alert(data.error || '上传失败')
    }
  }
  input.click()
}

async function load() {
  const res = await fetch(`/api/questionnaires/${qid}`, {
    headers: { Authorization: localStorage.getItem('token') || '' },
  })
  const data = await res.json()
  if (res.ok) {
    title.value = data.title
    description.value = data.description || ''
    qtype.value = data.type || 'test'
    fullScore.value = data.full_score ?? null
    mode.value = data.result_mode || 'score'
    questions.value = data.questions || []
    result_cards.value = (data.result_cards || []).map((c) => ({ ...c, _id: uid() }))
    status.value = data.status || 'draft'
  }
}

async function save(statusToSet = null) {
  saving.value = true
  saved.value = false
  const body = {
    title: title.value,
    description: description.value,
    questions: questions.value,
    result_cards: result_cards.value,
  }
  if (qtype.value === 'exam') {
    body.full_score = fullScore.value === '' || fullScore.value === null ? null : Number(fullScore.value)
  }
  if (qtype.value === 'test') {
    body.result_mode = mode.value
  }
  if (statusToSet) body.status = statusToSet

  const res = await fetch(`/api/questionnaires/${qid}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: localStorage.getItem('token') || '',
    },
    body: JSON.stringify(body),
  })
  saving.value = false
  if (res.ok) {
    if (statusToSet === 'published') status.value = 'published'
    saved.value = true
    setTimeout(() => (saved.value = false), 2000)
    return true
  } else {
    let msg = '保存失败'
    try {
      const data = await res.json()
      msg = data.error || msg
    } catch (e) {
      msg = `请求失败（HTTP ${res.status}）`
    }
    alert(msg)
    return false
  }
}

function examReady() {
  if (qtype.value !== 'exam') return ''
  if (!questions.value.length) return '请先添加题目'
  for (let i = 0; i < questions.value.length; i++) {
    const q = questions.value[i]
    if (!(Number(q.score) > 0)) {
      return `第 ${i + 1} 题（${examTypeLabel[q.type] || q.type}）还未设置分值`
    }
  }
  return ''
}

function jumpReady() {
  if (qtype.value !== 'test' || mode.value !== 'jump') return ''
  if (!questions.value.length) return '请先添加题目'
  const n = questions.value.length
  const letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
  for (let qi = 0; qi < n; qi++) {
    const opts = questions.value[qi].options || []
    for (let oi = 0; oi < opts.length; oi++) {
      const jt = opts[oi].jump_to || ''
      if (!jt.startsWith('q')) continue
      const target = parseInt(jt.slice(1), 10)
      if (!target || target < 1 || target > n) {
        return `第 ${qi + 1} 题选项 ${letters[oi] || (oi + 1)} 跳转到了第 ${target} 题，但问卷只有 ${n} 题，题号不连贯`
      }
    }
  }
  return ''
}

async function publish() {
  if (qtype.value === 'exam') {
    const err = examReady()
    if (err) {
      alert(err + '，请完成分值布置后再发布')
      return
    }
  }
  if (qtype.value === 'test' && mode.value === 'jump') {
    const err = jumpReady()
    if (err) {
      alert(err + '，请修正后再发布')
      return
    }
  }
  const ok = await save('published')
  if (ok) router.push(`/fill/${qid}`)
}

function pickExcel() {
  excelInput.value && excelInput.value.click()
}

async function downloadTemplate() {
  const res = await fetch('/api/exam/template', {
    headers: { Authorization: localStorage.getItem('token') || '' },
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    alert(data.error || '下载失败')
    return
  }
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '考试试卷模板.xlsx'
  a.click()
  URL.revokeObjectURL(url)
}

async function onExcel(e) {
  const file = e.target.files && e.target.files[0]
  e.target.value = ''
  if (!file) return
  const fd = new FormData()
  fd.append('file', file)
  const res = await fetch('/api/exam/parse', {
    method: 'POST',
    headers: { Authorization: localStorage.getItem('token') || '' },
    body: fd,
  })
  const data = await res.json()
  if (!res.ok) {
    alert(data.error || '解析失败')
    return
  }
  questions.value = data.questions || []
  if (data.warnings && data.warnings.length) {
    alert(`已导入 ${questions.value.length} 道题，但有提示：\n${data.warnings.join('\n')}`)
  } else {
    alert(`已导入 ${questions.value.length} 道题`)
  }
}

onMounted(load)
</script>

<template>
  <div class="editor">
    <header class="topbar">
      <button class="ghost" @click="router.push('/')">← 返回</button>
      <input v-model="title" class="title" placeholder="问卷名称" />
      <button class="primary" :disabled="saving" @click="save">
        {{ saved ? '已保存 ✓' : saving ? '保存中...' : '保存' }}
      </button>
      <button class="publish" :disabled="saving || status === 'published'" @click="publish">
        {{ status === 'published' ? '已发布' : '发布' }}
      </button>
    </header>

    <main class="body">
      <section class="section">
        <h2>问卷介绍</h2>
        <textarea
          v-model="description"
          class="desc-input"
          placeholder="介绍一下这份问卷（选填）"
        ></textarea>
      </section>

      <section class="section">
        <h2>题目（{{ questions.length }}）</h2>

        <div v-if="qtype === 'exam'" class="fullscore-row">
          <label class="fs-label">试卷总分</label>
          <input v-model="fullScore" type="number" class="fs-input" placeholder="留空则自动求和" />
          <span class="fs-hint">当前各题合计 {{ totalQuestionScore }} 分</span>
        </div>

        <div v-if="qtype === 'exam'" class="import-row">
          <button class="mini add" @click="downloadTemplate">下载模板</button>
          <button class="mini add" @click="pickExcel">上传试卷</button>
          <input ref="excelInput" type="file" accept=".xlsx" class="hidden-input" @change="onExcel" />
          <span class="fs-hint">一行一题：题型 / 题干 / 选项（支持多个）/ 正确答案 / 分值</span>
        </div>

        <div v-for="(q, qi) in questions" :key="qi" class="card" :ref="el => (cardRefs[qi] = el)">
          <div class="card-head">
            <div v-if="qtype === 'test' && mode === 'jump'" class="head-left">
              <span class="badge">第 {{ qi + 1 }} 题</span>
              <input type="number" class="q-nav" placeholder="跳至题号" min="1" @change="navToQuestion" />
            </div>
            <span v-else class="badge">{{ questionBadge(qi) }}</span>
            <div class="ops">
              <button class="mini" @click="moveQuestion(qi, -1)">↑</button>
              <button class="mini" @click="moveQuestion(qi, 1)">↓</button>
              <button class="mini danger" @click="removeQuestion(qi)">删除</button>
            </div>
          </div>

          <input v-model="q.title" class="q-title" :placeholder="`第 ${qi + 1} 题的题干`" />

          <div v-if="qtype === 'exam'" class="q-score-row">
            <label>分值</label>
            <input v-model.number="q.score" type="number" class="q-score-input" />
          </div>

          <!-- 考试：单选 / 多选 -->
          <div v-if="qtype === 'exam' && (q.type === 'single' || q.type === 'multiple')" class="options">
            <div v-for="(o, oi) in q.options" :key="oi" class="option-row">
              <input
                :type="q.type === 'single' ? 'radio' : 'checkbox'"
                :name="'correct-' + qi"
                :checked="o.is_correct"
                :class="q.type === 'single' ? 'correct-radio' : 'correct-check'"
                title="设为正确答案"
                @change="q.type === 'single' ? setCorrect(q, oi) : (o.is_correct = $event.target.checked)"
              />
              <input v-model="o.text" class="opt-text" placeholder="选项文字" />
              <button class="mini danger" @click="removeOption(qi, oi)">✕</button>
            </div>
          </div>

          <!-- 考试：判断 -->
          <div v-else-if="qtype === 'exam' && q.type === 'judge'" class="options judge-options">
            <label
              v-for="(o, oi) in q.options"
              :key="oi"
              class="judge-option"
              :class="{ on: o.is_correct }"
            >
              <input type="radio" :name="'judge-' + qi" :checked="o.is_correct" @change="setCorrect(q, oi)" />
              <span>{{ o.text }}</span>
            </label>
          </div>

          <!-- 考试：填空 -->
          <div v-else-if="qtype === 'exam' && q.type === 'fill'" class="options">
            <input v-model="q.answer" class="opt-text" placeholder="参考答案，多个用 | 分隔" />
          </div>

          <!-- 跳转：单选选项 -->
          <div v-else-if="qtype === 'test' && mode === 'jump'" class="options">
            <div v-for="(o, oi) in q.options" :key="oi" class="option-row jump-option-row">
              <span class="opt-letter">{{ ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'][oi] }}</span>
              <input v-model="o.text" class="opt-text" placeholder="选项文字" />
              <select class="jump-type" :value="jumpType(o.jump_to)" @change="setJumpType(qi, oi, $event.target.value)">
                <option value="next">下一题</option>
                <option value="q">跳转到题目</option>
                <option value="r">跳转到结果</option>
              </select>
              <select v-if="jumpType(o.jump_to) === 'q'" class="jump-select" :value="jumpQTarget(o.jump_to)" @change="setJumpQTarget(qi, oi, $event.target.value)">
                <option v-for="(qq, qi2) in questions" :key="'q' + qi2" :value="String(qi2 + 1)" :disabled="qi2 === qi">
                  第 {{ qi2 + 1 }} 题
                </option>
              </select>
              <select v-else-if="jumpType(o.jump_to) === 'r'" class="jump-select" :value="jumpRTarget(o.jump_to)" @change="setJumpRTarget(qi, oi, $event.target.value)">
                <option v-for="c in result_cards" :key="c._id" :value="c.label" :disabled="resultLabelUsedByOthers(qi, oi, c.label)">
                  结果 {{ c.label }}{{ resultLabelUsedByOthers(qi, oi, c.label) ? '（已用）' : '' }}
                </option>
              </select>
              <button class="mini danger" @click="removeOption(qi, oi)">✕</button>
            </div>
          </div>

          <!-- 测试问卷：选项 -->
          <div v-else class="options">
            <div v-for="(o, oi) in q.options" :key="oi" class="option-row">
              <input v-model="o.text" class="opt-text" placeholder="选项文字" />
              <input v-model.number="o.score" type="number" class="opt-score" placeholder="分值" />
              <button class="mini danger" @click="removeOption(qi, oi)">✕</button>
            </div>
          </div>

          <div v-if="qtype === 'exam'" class="card-foot">
            <button v-if="q.type === 'single' || q.type === 'multiple'" class="mini add" @click="addOption(qi)">＋ 添加选项</button>
          </div>
          <div v-else class="card-foot">
            <button v-if="q.type === 'single'" class="mini add" @click="addOption(qi)">＋ 添加选项</button>
            <button v-else class="mini add" @click="toggleReverse(qi)">反向计分</button>
          </div>
        </div>

        <div class="add-btns">
          <template v-if="qtype === 'exam'">
            <button class="add-question" @click="addQuestion('single')">＋ 单选题</button>
            <button class="add-question" @click="addQuestion('multiple')">＋ 多选题</button>
            <button class="add-question" @click="addQuestion('judge')">＋ 判断题</button>
            <button class="add-question" @click="addQuestion('fill')">＋ 填空题</button>
          </template>
          <template v-else>
            <button class="add-question" @click="addQuestion('single')">＋ 单选题</button>
            <button v-if="mode !== 'jump'" class="add-question" @click="addQuestion('scale')">＋ 量表题</button>
          </template>
        </div>
      </section>

      <section class="section" v-if="qtype !== 'exam'">
        <h2>结果卡片（{{ result_cards.length }}）</h2>

        <div v-for="(c, ci) in result_cards" :key="c._id" class="card">
          <div class="card-head">
            <label v-if="mode === 'jump'" class="badge result-badge">
              结果
              <select v-model="c.label" class="label-select">
                <option v-for="ch in resultLabels" :key="ch" :value="ch">{{ ch }}</option>
              </select>
            </label>
            <span v-else class="badge">分数区间</span>
            <button class="mini danger" @click="removeCard(ci)">删除</button>
          </div>
          <div v-if="mode !== 'jump'" class="range">
            <input v-model.number="c.min_score" type="number" placeholder="最低分" />
            <span>～</span>
            <input v-model.number="c.max_score" type="number" placeholder="最高分" />
          </div>
          <div class="rtf">
            <div class="rtf-toolbar">
              <button type="button" class="tb" @mousedown.prevent @click="exec(ci, 'bold')" title="加粗"><b>B</b></button>
              <button type="button" class="tb" @mousedown.prevent @click="exec(ci, 'italic')" title="斜体"><i>I</i></button>
              <button type="button" class="tb" @mousedown.prevent @click="exec(ci, 'underline')" title="下划线"><u>U</u></button>
              <select class="tb-select" @change="exec(ci, 'fontName', $event.target.value)">
                <option value="">字体</option>
                <option value="宋体">宋体</option>
                <option value="黑体">黑体</option>
                <option value="楷体">楷体</option>
                <option value="微软雅黑">微软雅黑</option>
                <option value="Arial">Arial</option>
              </select>
              <select class="tb-select" title="字号" @change="setFontSize(ci, $event.target.value)">
                <option value="">字号</option>
                <option v-for="s in fontSizeOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
              </select>
              <select class="tb-select" title="字体颜色" @change="exec(ci, 'foreColor', $event.target.value)">
                <option value="">A</option>
                <option
                  v-for="c in presetColors"
                  :key="c"
                  :value="c"
                  :style="{ color: c }"
                >A</option>
              </select>
              <button type="button" class="tb" @mousedown.prevent @click="insertImage(ci)" title="插入图片">图片</button>
            </div>
            <div
              class="rtf-area"
              :ref="(el) => setCardEditor(ci, el)"
              contenteditable="true"
              @input="onRtfInput(ci, $event)"
              @mouseup="saveCardRange"
              @keyup="saveCardRange"
              data-placeholder="这段分数区间对应的结果文案"
            ></div>
          </div>
        </div>

        <button class="add-question" @click="addCard">＋ 添加结果卡片</button>
      </section>
    </main>
  </div>
</template>

<style scoped>
.editor {
  min-height: 100vh;
  background: var(--bg);
}

.topbar {
  position: sticky;
  top: 0;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 24px;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  z-index: 10;
}

.title {
  flex: 1;
  padding: 10px 16px;
  font-size: 16px;
  font-weight: 600;
  border: 1px solid transparent;
  border-radius: 10px;
  outline: none;
}

.title:focus {
  border-color: #6366f1;
  background: #f8faff;
}

.primary {
  padding: 10px 22px;
  font-size: 15px;
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

.publish {
  padding: 10px 22px;
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #10b981, #059669);
  border: none;
  border-radius: 10px;
  cursor: pointer;
}

.publish:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.ghost {
  padding: 9px 14px;
  border: 1px solid var(--border);
  background: #fff;
  color: #6b7280;
  border-radius: 10px;
  cursor: pointer;
}

.body {
  max-width: 720px;
  margin: 0 auto;
  padding: 28px 20px 60px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.section h2 {
  font-size: 17px;
  margin: 0 0 16px;
}

.desc-input {
  width: 100%;
  padding: 12px 14px;
  font-size: 14px;
  font-family: inherit;
  border: 1px solid var(--border);
  border-radius: 10px;
  outline: none;
  resize: vertical;
  min-height: 80px;
}

.desc-input:focus {
  border-color: #6366f1;
}

.card {
  background: #fff;
  border-radius: 14px;
  padding: 18px;
  margin-bottom: 14px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.badge {
  font-size: 12px;
  color: #6366f1;
  background: rgba(99, 102, 241, 0.1);
  padding: 3px 10px;
  border-radius: 20px;
  font-weight: 600;
}

.head-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.q-nav {
  width: 92px;
  font-size: 12px;
  font-weight: 600;
  color: #6366f1;
  background: rgba(99, 102, 241, 0.1);
  border: none;
  border-radius: 20px;
  padding: 4px 10px;
  outline: none;
}

.q-nav:focus {
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

.ops {
  display: flex;
  gap: 6px;
}

.mini {
  padding: 4px 9px;
  font-size: 13px;
  border: 1px solid var(--border);
  background: #fff;
  color: #6b7280;
  border-radius: 8px;
  cursor: pointer;
}

.mini:hover {
  border-color: #6366f1;
  color: #6366f1;
}

.mini.danger:hover {
  border-color: #ef4444;
  color: #ef4444;
}

.mini.add {
  color: #6366f1;
  border-color: #c7d2fe;
}

.q-title {
  width: 100%;
  padding: 10px 12px;
  font-size: 15px;
  border: 1px solid var(--border);
  border-radius: 10px;
  outline: none;
  margin-bottom: 12px;
}

.q-title:focus {
  border-color: #6366f1;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.option-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.opt-text {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  outline: none;
  font-size: 14px;
}

.opt-score {
  width: 70px;
  padding: 8px;
  border: 1px solid var(--border);
  border-radius: 8px;
  outline: none;
  font-size: 14px;
}

.opt-text:focus,
.opt-score:focus {
  border-color: #6366f1;
}

.card-foot {
  margin-top: 12px;
}

.add-btns {
  display: flex;
  gap: 12px;
}

.add-question {
  flex: 1;
  padding: 12px;
  border: 1px dashed #c7d2fe;
  background: #f8faff;
  color: #6366f1;
  border-radius: 12px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
}

.add-question:hover {
  background: #eef2ff;
}

.range {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.range input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  outline: none;
}

.range input:focus {
  border-color: #6366f1;
}

.rtf {
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}

.rtf-toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 8px;
  border-bottom: 1px solid var(--border);
  background: #f8fafc;
  flex-wrap: wrap;
}

.tb {
  min-width: 30px;
  height: 30px;
  padding: 0 8px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  color: #334155;
}

.tb:hover {
  background: #eef2ff;
  color: #6366f1;
}

.tb-select {
  height: 30px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: #fff;
  font-size: 13px;
  color: #334155;
  cursor: pointer;
  padding: 0 4px;
}

.rtf-area {
  min-height: 80px;
  padding: 10px 12px;
  font-size: 14px;
  outline: none;
  line-height: 1.6;
}

.rtf-area:empty:before {
  content: attr(data-placeholder);
  color: #94a3b8;
}

.rtf-area img {
  max-width: 100%;
}

.fullscore-row {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f8faff;
  border: 1px dashed #c7d2fe;
  border-radius: 12px;
  padding: 12px 16px;
  margin-bottom: 16px;
}

.fs-label {
  font-size: 14px;
  font-weight: 600;
  color: #334155;
}

.fs-input {
  width: 120px;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  outline: none;
  font-size: 14px;
}

.fs-input:focus {
  border-color: #6366f1;
}

.fs-hint {
  font-size: 13px;
  color: var(--muted);
}

.import-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.import-row .fs-hint {
  flex: 1;
}

.hidden-input {
  display: none;
}

.q-score-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.q-score-row label {
  font-size: 13px;
  color: var(--muted);
}

.q-score-input {
  width: 80px;
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  outline: none;
  font-size: 14px;
}

.q-score-input:focus {
  border-color: #6366f1;
}

.correct-radio,
.correct-check {
  width: 18px;
  height: 18px;
  accent-color: #6366f1;
  cursor: pointer;
  flex-shrink: 0;
}

.judge-options {
  flex-direction: row;
}

.judge-option {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 10px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.15s;
}

.judge-option.on {
  border-color: #10b981;
  background: rgba(16, 185, 129, 0.06);
  color: #059669;
}

.judge-option input {
  accent-color: #10b981;
}

.opt-letter {
  width: 22px;
  flex-shrink: 0;
  text-align: center;
  font-size: 13px;
  font-weight: 600;
  color: #94a3b8;
}

.jump-option-row {
  align-items: center;
}

.jump-type {
  width: 112px;
  flex-shrink: 0;
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  outline: none;
  font-size: 13px;
  color: var(--text);
  background: #fff;
  cursor: pointer;
}

.jump-select {
  width: 132px;
  flex-shrink: 0;
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  outline: none;
  font-size: 13px;
  color: var(--text);
  background: #fff;
  cursor: pointer;
}

.jump-select:focus {
  border-color: #6366f1;
}

.result-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.label-select {
  padding: 2px 4px;
  border: none;
  background: rgba(99, 102, 241, 0.12);
  border-radius: 6px;
  color: #6366f1;
  font-weight: 600;
  font-size: 12px;
  cursor: pointer;
  outline: none;
}
</style>
