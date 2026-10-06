<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useHunterStore } from '../stores/hunter.js'

const router = useRouter()
const hunter = useHunterStore()

// ============ 入场加载页 ============
const bootLines = ref([])
const bootProgress = ref(0)
const bootStatus = ref('INITIALIZING...')
const bootDone = ref(false)
const bootReady = ref(false)
const bootMessages = [
  { t: 'CONNECTING TO H.A. MAINFRAME...', s: 200 },
  { t: 'AUTHENTICATING CRYPTOGRAPHIC KEY...', s: 300 },
  { t: 'LOADING ZODIAC PROTOCOL...', s: 300 },
  { t: 'DECRYPTING CLASSIFIED ARCHIVES...', s: 350 },
  { t: 'ACCESS GRANTED. WELCOME, HUNTER.', s: 400 },
]
let bootTimers = []

function runBoot() {
  let idx = 0
  function step() {
    if (idx >= bootMessages.length) {
      bootProgress.value = 100
      bootStatus.value = 'COMPLETE · READY'
      bootTimers.push(setTimeout(() => { bootReady.value = true }, 400))
      return
    }
    const msg = bootMessages[idx]
    bootLines.value = [...bootLines.value.slice(-2), msg.t]
    bootProgress.value = Math.min(100, ((idx + 1) / bootMessages.length) * 95)
    bootStatus.value = msg.t
    idx++
    bootTimers.push(setTimeout(step, msg.s))
  }
  bootTimers.push(setTimeout(step, 400))
}

// ============ 入场粒子 + 鼠标跟随 ============
const bootCanvas = ref(null)
let pctx = null
let particles = []
let pmouseX = -1
let pmouseY = -1
let pW = 0
let pH = 0
let rafId = null

function resizeCanvas() {
  const cvs = bootCanvas.value
  if (!cvs) return
  pW = cvs.width = window.innerWidth
  pH = cvs.height = window.innerHeight
}

function spawnAmbient(n) {
  for (let i = 0; i < n; i++) {
    particles.push({
      x: Math.random() * pW,
      y: Math.random() * pH,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      r: Math.random() * 1.8 + 0.6,
      a: Math.random() * 0.5 + 0.15,
      trail: false,
      life: 0,
    })
  }
}

function spawnTrail(x, y) {
  for (let i = 0; i < 2; i++) {
    particles.push({
      x: x + (Math.random() - 0.5) * 10,
      y: y + (Math.random() - 0.5) * 10,
      vx: (Math.random() - 0.5) * 1.4,
      vy: (Math.random() - 0.5) * 1.4,
      r: Math.random() * 2.4 + 0.8,
      a: Math.random() * 0.6 + 0.3,
      trail: true,
      life: 1,
    })
  }
}

function tick() {
  if (!pctx) return
  pctx.clearRect(0, 0, pW, pH)
  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i]
    if (p.trail) {
      p.life -= 0.03
      p.x += p.vx
      p.y += p.vy
      p.a = Math.max(0, p.life)
      if (p.life <= 0) {
        particles.splice(i, 1)
        continue
      }
    } else {
      if (pmouseX >= 0) {
        const dx = pmouseX - p.x
        const dy = pmouseY - p.y
        const d = Math.hypot(dx, dy)
        if (d > 0 && d < 260) {
          const f = ((260 - d) / 260) * 0.08
          p.vx += (dx / d) * f
          p.vy += (dy / d) * f
        }
        if (d < 14) {
          p.x = Math.random() * pW
          p.y = Math.random() * pH
          p.vx = 0
          p.vy = 0
        }
      }
      p.x += p.vx
      p.y += p.vy
      p.vx *= 0.98
      p.vy *= 0.98
      if (p.x < 0 || p.x > pW) p.vx *= -1
      if (p.y < 0 || p.y > pH) p.vy *= -1
    }
    pctx.beginPath()
    pctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
    pctx.fillStyle = `rgba(232, 200, 120, ${p.a})`
    pctx.fill()
  }
  rafId = requestAnimationFrame(tick)
}

function onPointerMove(e) {
  pmouseX = e.clientX
  pmouseY = e.clientY
  spawnTrail(pmouseX, pmouseY)
}

function initParticles() {
  resizeCanvas()
  pctx = bootCanvas.value.getContext('2d')
  particles = []
  spawnAmbient(90)
  window.addEventListener('pointermove', onPointerMove)
  window.addEventListener('resize', resizeCanvas)
  tick()
}

function enterHunter() {
  if (bootDone.value) return
  bootDone.value = true
  if (rafId) cancelAnimationFrame(rafId)
}

// ============ 倒计时 ============
const cdDays = ref('000')
const cdHours = ref('00')
const cdMins = ref('00')
const cdSecs = ref('00')
let countdownTimer = null

function updateCountdown() {
  const examDate = new Date()
  examDate.setDate(examDate.getDate() + 87)
  examDate.setHours(0, 0, 0, 0)
  const diff = examDate - new Date()
  if (diff <= 0) return
  cdDays.value = String(Math.floor(diff / 86400000)).padStart(3, '0')
  cdHours.value = String(Math.floor((diff % 86400000) / 3600000)).padStart(2, '0')
  cdMins.value = String(Math.floor((diff % 3600000) / 60000)).padStart(2, '0')
  cdSecs.value = String(Math.floor((diff % 60000) / 1000)).padStart(2, '0')
}

// ============ 导航 ============
const menuOpen = ref(false)
function scrollTo(id) {
  menuOpen.value = false
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth' })
}

// ============ 公告滚动 ============
const announcements = [
  '第289届猎人资格考试报名通道现已开放',
  '幻影旅团成员等级警戒提升至 A 级',
  '嵌合蚁讨伐任务正式结案，授予参战猎人特别贡献勋章',
  '暗黑大陆探索申请已向十二支递交',
  '天空竞技场新增 200 层挑战权限',
]

// ============ 核心成员 ============
const members = [
  { key: 'netero', nameCn: '尼特罗', nameEn: 'ISAAC NETERO', title: '猎人协会第十二代会长', role: 'CHAIRMAN · 会长', stars: '★★★', rank: '三星猎人', nen: '强化系', affiliation: '协会本部', bio: '猎人协会第十二代会长，被誉为"百式观音"的传说级强化系念能力者。年轻时曾独自登上"贪婪之岛"，亦曾独力压制黑帮总部。年迈之时仍能与最强存在抗衡，是协会精神象征。', battle: '嵌合蚁讨伐战 · 主帅；天空竞技场创立顾问；幻影旅团早期接触者。', quote: '感谢你让我享受了这一切。' },
  { key: 'ging', nameCn: '金·富力士', nameEn: 'GING FREECSS', title: '前十二支 · 亥之星 · 双星考古猎人', role: 'FORMER ZODIAC · 前十二支', stars: '★★', rank: '双星猎人', nen: '未公开', affiliation: '前十二支「亥」 · 已退出', bio: '现代世界最受瞩目的考古学者与遗迹探索者。原十二支「亥」之星持有者，于第十三届会长选举后主动退出。被尼特罗评价为"世界前五的念能力者"，但其具体念系属性至今未公开。已获得申请三星资格，但未提交申请。', battle: '废都「鲁因」首位踏入者；多枚 NGL 自治区古文物发现者；暗黑大陆探险队核心成员。', quote: '与目标相比，过程之中遇见的事物才是真正的宝物。' },
  { key: 'kite', nameCn: '凯特', nameEn: 'KITE', title: '稀种调查员 · 金的徒弟', role: 'INVESTIGATOR · 调查员', stars: '★★', rank: '双星猎人', nen: '具现化系', affiliation: '稀种保护部', bio: '金·富力士唯一公开承认的徒弟，亦是稀种生物保护领域的顶尖调查员。能以"幸运卷轴"具现化九种不同形态的武器，曾于嵌合蚁事件中首先发现蚁王存在并发出最高级别警报。', battle: 'NGL 嵌合蚁先遣调查 · 任务指挥；多次主导北部山脉稀种调查。', quote: '所谓运气，是技术不可分割的一部分。' },
  { key: 'leorio', nameCn: '雷欧力·帕拉迪奈特', nameEn: 'LEORIO PARADINIGHT', title: '十二支 · 亥之星（继任） · 公共形象', role: 'ZODIAC · 十二支', stars: '★', rank: '单星猎人', nen: '放出系', affiliation: '十二支「亥」 · 继金之后接任', bio: '原本以成为医生为人生目标的青年，因第287届猎人资格考试结识金·富力士之子。在第十三届会长选举中表现亮眼，金退出十二支后由他接任「亥」之星。能以远距离放出念之拳头，是协会近年最受民众支持的公众面孔。', battle: '会长选举公开击打前会长之子；协会医疗体系改革推动者。', quote: '不管钱赚多少，能救的人还是有限。' },
  { key: 'morel', nameCn: '莫老五·麦肯锡', nameEn: 'MOREL MACKERNASEY', title: '双星猎人 · 战术部首脑', role: 'TOP HUNTER · 顶级猎人', stars: '★★', rank: '双星猎人', nen: '操作系', affiliation: '战术部 · 协会顶级猎人之一', bio: '协会战术部首脑，虽非十二支成员，却被公认为协会顶级战力之一。以"深海烟斗"释出可自由操纵的烟雾兵团，是协会内最具代表性的操作系猎人。嵌合蚁讨伐战副指挥，向以稳重沉着、布局严谨著称，麾下培养出多名顶尖后辈。', battle: 'NGL 嵌合蚁讨伐 · 副指挥；多项跨国境追缉任务总指挥。', quote: '我们的工作不是逞英雄，而是把每个伙伴都带回来。' },
  { key: 'biscuit', nameCn: '比斯吉·库尔卡', nameEn: 'BISCUIT KRUEGER', title: '念能力首席导师', role: 'MASTER · 导师', stars: '★★★', rank: '三星猎人', nen: '变化系', affiliation: '念修行院', bio: '协会内部公认的最强念能力导师之一，年逾五十却以少女形象示人。其真实战斗形态拥有压倒性的物理破坏力。培养无数顶尖猎人，包括两位曾通过"贪婪之岛"的少年。', battle: '贪婪之岛通关者；天空竞技场前 200 层挑战者；多次担任新人指导。', quote: '在这世上，连一个能让你专心的对手都遇不到，那才是最寂寞的事。' },
  { key: 'cheadle', nameCn: '绮多·约克郡', nameEn: 'CHEADLE YORKSHIRE', title: '十二支 · 戌之星 · 现任会长', role: 'CHAIRWOMAN · 第十三代会长', stars: '★★★', rank: '三星猎人', nen: '具现化系', affiliation: '十二支「戌」', bio: '医学博士，专精病理学与传染病学，被尼特罗会长亲自钦点为下任会长的候选人之一。在第十三代会长选举中胜出，正式接掌协会本部。冷静、严谨，是协会近代历史上极少数同时具备学术、行政与战斗实力的核心人物。', battle: '尼特罗会长指定继任者；第十三代会长选举胜出；嵌合蚁讨伐战医疗顾问。', quote: '一个组织要存活下去，靠的不是英雄，而是无数个肯做事的普通人。' },
  { key: 'mizai', nameCn: '米哉斯顿·南奈', nameEn: 'MIZAISTOM NANA', title: '十二支 · 丑之星 · 司法部首脑', role: 'ZODIAC · 司法部', stars: '★★★', rank: '三星猎人', nen: '具现化系', affiliation: '十二支「丑」', bio: '协会司法部门首脑，被誉为"绝对中立"的化身。负责协会内部一切违规与犯罪调查，立场不偏不倚，连面对副会长帕利斯顿亦不假辞色。具现化系，能将巨大斧形念能力作为执法之具。', battle: '主导协会内部多起腐败案件；继承战中实际担任秩序维持者；多次跨国境恶性犯罪追缉指挥官。', quote: '法律不一定永远公正，但执法者必须永远公正。' },
  { key: 'pariston', nameCn: '帕利斯顿·希尔', nameEn: 'PARISTON HILL', title: '前十二支 · 子之星 · 前副会长', role: 'FORMER ZODIAC · 前副会长', stars: '★★★', rank: '三星猎人', nen: '未公开', affiliation: '前十二支「子」 · 已退出 · 警戒对象', bio: '原十二支「子」之星持有者，尼特罗时代的协会副会长。被尼特罗本人亲口评价为"协会内部最危险的男人"。第十三届会长选举中数度操纵局势，胜出后却立即主动辞职，并自十二支退出。其真实意图、念能力、立场至今为谜，是协会公开档案中级别最高的"灰色人物"。', battle: '第十三代会长选举操盘；前副会长任内多起争议决策；与暗黑大陆探索深度关联。', quote: '我喜欢看人困扰、愤怒、绝望——那是最美的表情。' },
]
const activeMember = ref(null)

// ============ 十二支罗盘 ============
const zodiac = [
  { zi: '子', pinyin: 'ZI · 鼠', angle: -90, name: '酷拉皮卡（继任）', en: 'KURAPIKA', role: '十二支 · 子之星 · 现任', desc: '原帕利斯顿退出后接任的子之星。窟卢塔族最后的幸存者，绯之眼具现化系念能力者，因复仇追猎幻影旅团而加入猎人协会。', successor: true },
  { zi: '丑', pinyin: 'CHOU · 牛', angle: -60, name: '米哉斯顿', en: 'MIZAISTOM', role: '十二支 · 丑之星 · 司法猎人', desc: '牛头帽、牛斑纹大衣，"丑"对应牛。协会司法部门首脑，立场绝对中立。' },
  { zi: '寅', pinyin: 'YIN · 虎', angle: -30, name: '柯岛', en: 'KANZAI', role: '十二支 · 寅之星 · 财宝猎人', desc: '虎之猎人，性格急躁直接，是十二支中最具战斗本能的存在之一。' },
  { zi: '卯', pinyin: 'MAO · 兔', angle: 0, name: '皮羊魔', en: 'PYON', role: '十二支 · 卯之星 · 古文字猎人', desc: '兔耳少女造型，年轻有为的古文字猎人，第十三届会长选举主持人之一。' },
  { zi: '辰', pinyin: 'CHEN · 龙', angle: 30, name: '柏特奥诺夫', en: 'BOTOBAI', role: '十二支 · 辰之星 · 反恐猎人', desc: '十二支中最年长的成员，三星反恐猎人，被称为"最强生物"，能力深不可测。' },
  { zi: '巳', pinyin: 'SI · 蛇', angle: 60, name: '葛尔', en: 'GEL', role: '十二支 · 巳之星 · 毒物猎人', desc: '冷静沉着的蛇之猎人，专精各类毒物与药学研究。能将手臂变为蛇形。' },
  { zi: '午', pinyin: 'WU · 马', angle: 90, name: '萨切莫诺·小早川', en: 'SACCHO', role: '十二支 · 午之星 · 调查猎人', desc: '武士装束的双星调查猎人，是十二支中最理智沉稳的人物之一。' },
  { zi: '未', pinyin: 'WEI · 羊', angle: 120, name: '银仓', en: 'GINTA', role: '十二支 · 未之星 · 反盗猎猎人', desc: '羊之猎人，性格感性易动情，被西索评价为战力远超柯岛与皮羊魔。' },
  { zi: '申', pinyin: 'SHEN · 猴', angle: 150, name: '萨优', en: 'SAIYU', role: '十二支 · 申之星 · 赏金猎人', desc: '猴之猎人，使用如意金箍棒般的法杖，常处于战斗状态的赏金猎人。' },
  { zi: '酉', pinyin: 'YOU · 鸡', angle: 180, name: '茉妲莎', en: 'CLUCK', role: '十二支 · 酉之星 · 植物猎人', desc: '鸡羽装束的植物猎人，能同时操控 600 只以上的鸽群传讯。' },
  { zi: '戌', pinyin: 'XU · 狗', angle: 210, name: '绮多·约克郡', en: 'CHEADLE', role: '十二支 · 戌之星 · 第十三代会长', desc: '医学博士兼疾病猎人，狗耳造型贴合"戌"。继任尼特罗后正式接掌协会。' },
  { zi: '亥', pinyin: 'HAI · 猪', angle: 240, name: '雷欧力·帕拉迪奈特（继任）', en: 'LEORIO', role: '十二支 · 亥之星 · 现任', desc: '原金·富力士退出后接任的亥之星。立志成为医生的青年，协会近年最受欢迎的年轻面孔。', successor: true },
]
const activeZodiac = ref(null)
function zodiacPos(z) {
  const rad = (z.angle * Math.PI) / 180
  const x = 50 + Math.cos(rad) * 38.3
  const y = 50 + Math.sin(rad) * 38.3
  return { left: x + '%', top: y + '%' }
}

// ============ 通缉令 ============
const wanted = [
  { name: '库洛洛·鲁西鲁', alias: 'CHROLLO LUCILFER · SPIDER #0', bounty: '¥ 10,000,000,000', threat: 'EX', cls: 'A 级窃盗团 · 团长', lastSeen: '流星街 / 不明', ability: '具现化系 · 盗贼的极意「SKILL HUNTER」', danger: '可"偷取"他人念能力为己用。禁止单独接触，仅协会总部直属机动队可执行追缉。', icon: '×' },
  { name: '幻影旅团 · 成员', alias: 'PHANTOM TROUPE', bounty: '¥ 1,000,000,000 / 人', threat: 'S', cls: 'A 级窃盗团 · 旅团成员', lastSeen: '约克新市 / 流动', ability: '各异 · 旅团编号一至十三', danger: '已确认成员均为高位念能力者，部分个体战力达单星至双星猎人水准。建议组队行动。', icon: '蛛' },
  { name: '西索·摩罗', alias: 'HISOKA MOROW', bounty: '¥ 800,000,000', threat: 'S', cls: '前持证猎人 · 已主动注销执照', lastSeen: '天空竞技场 200 层附近 / 流动', ability: '变化系 · 伸缩自如之爱 / 薄如轻纱之嘘', danger: '因追杀幻影旅团而主动注销猎人执照。喜好挑衅强者并将其击杀，行为难以预测，警告勿单独迎击。', icon: '♠' },
  { name: 'NGL 残党', alias: 'NGL REMNANTS', bounty: '¥ 250,000,000', threat: 'A', cls: '前嵌合蚁残党 · 数名', lastSeen: 'NGL 自治区遗迹 / 东冈国边境', ability: '蚁兵残余 · 部分掌握念能力', danger: '嵌合蚁讨伐战后逃逸的高位个体，可能仍保有人形伪装能力。', icon: '蚁' },
  { name: '暗黑大陆相关人员', alias: 'DC AGITATORS', bounty: '协会档案封存', threat: 'EX', cls: '机密 · 仅会长权限', lastSeen: '档案封存', ability: '档案封存', danger: '一切与暗黑大陆相关之信息泄露者，均列于本协会最高警戒名单。', icon: '?' },
  { name: '不明念能力袭击者', alias: 'UNKNOWN ENTITY', bounty: '¥ 100,000,000', threat: 'A', cls: '调查中 · 身份未明', lastSeen: '约克新市 / 共和都市群', ability: '操作系（疑） · 利用平民为载体', danger: '受害目击者全部失忆。若在城市中遇异常事件请即刻撤离并上报。', icon: '?' },
]

// ============ 考试报名 ============
const showSuccess = ref(false)
const hunterEmail = ref('')
const hunterClass = ref('')
const submitting = ref(false)

async function submitForm() {
  const email = hunterEmail.value.trim()
  const classification = hunterClass.value
  if (!email || !classification) return
  submitting.value = true
  try {
    const res = await fetch('/api/hunter/key', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, classification }),
    })
    const data = await res.json()
    if (!res.ok) {
      alert(data.error || '提交失败，请稍后重试')
      return
    }
    showSuccess.value = true
  } catch (e) {
    alert('网络错误，请稍后重试')
  } finally {
    submitting.value = false
  }
}

// ============ 训练密钥入口 ============
const keyModalOpen = ref(false)
const keyStage = ref('key') // 'key' = 输入密钥，'class' = 确认专精方向
const keyInput = ref('')
const keyError = ref('')
const keyChecking = ref(false)
const trainClass = ref('')
const nenType = ref('')

const trainClasses = [
  { code: 'gourmet', cn: '美食猎人', en: 'GOURMET HUNTER' },
  { code: 'bounty', cn: '赏金猎人', en: 'BLACKLIST HUNTER' },
  { code: 'ruins', cn: '遗迹猎人', en: 'RUINS HUNTER' },
  { code: 'rare', cn: '稀种猎人', en: 'RARE BEAST HUNTER' },
  { code: 'archaeologist', cn: '考古猎人', en: 'ARCHAEOLOGICAL HUNTER' },
  { code: 'sacred', cn: '圣物猎人', en: 'SACRED TREASURE HUNTER' },
  { code: 'dark', cn: '暗黑大陆探索', en: 'DARK CONTINENT EXPEDITION' },
  { code: 'other', cn: '其他', en: 'OTHER' },
]

const nenTypes = [
  { code: 'enhancement', cn: '强化系', en: 'ENHANCEMENT' },
  { code: 'emission', cn: '放出系', en: 'EMISSION' },
  { code: 'transmutation', cn: '变化系', en: 'TRANSMUTATION' },
  { code: 'conjuration', cn: '具现化系', en: 'CONJURATION' },
  { code: 'manipulation', cn: '操作系', en: 'MANIPULATION' },
  { code: 'specialization', cn: '特质系', en: 'SPECIALIZATION' },
]

function openKeyModal() {
  keyInput.value = ''
  keyError.value = ''
  keyStage.value = 'key'
  trainClass.value = ''
  nenType.value = ''
  keyModalOpen.value = true
}

function closeKeyModal() {
  keyModalOpen.value = false
  keyStage.value = 'key'
}

async function verifyKey() {
  const key = keyInput.value.trim()
  if (!key) {
    keyError.value = '请输入密钥'
    return
  }
  keyChecking.value = true
  keyError.value = ''
  try {
    const res = await fetch('/api/hunter/train/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key }),
    })
    const data = await res.json()
    if (!res.ok) {
      keyError.value = data.error || '密钥无效'
      return
    }
    // 密钥验证通过后，进入第二步：由用户重新确认本次训练的专精方向。
    trainClass.value = data.classification || ''
    keyStage.value = 'class'
  } catch (e) {
    keyError.value = '网络错误，请稍后重试'
  } finally {
    keyChecking.value = false
  }
}

function confirmTraining() {
  if (!trainClass.value || !nenType.value) return
  hunter.unlockTraining(trainClass.value, nenType.value)
  keyModalOpen.value = false
  router.push('/hunter/training')
}

// ============ 水见式测试 ============
const nenQuestions = [
  { q: '你在森林深处发现一座废弃古迹，第一反应是？', options: [
    { text: '正面冲撞封印的石门', s: 'enhancement' },
    { text: '远距离投掷物体试探陷阱', s: 'emission' },
    { text: '观察石门构造，分析破解机关', s: 'conjuration' },
    { text: '诱使附近野兽撞开石门', s: 'manipulation' },
    { text: '感觉古迹"叫"自己，相信直觉', s: 'specialization' },
    { text: '改变自身形态，从缝隙渗入', s: 'transmutation' },
  ] },
  { q: '一场不可避免的战斗中，你倾向于？', options: [
    { text: '迎面冲上去，以肉身格斗压制', s: 'enhancement' },
    { text: '保持距离，远程消耗对方', s: 'emission' },
    { text: '设置道具或陷阱锁定对方', s: 'conjuration' },
    { text: '在对方未察觉时控制其行动', s: 'manipulation' },
    { text: '使用旁人无法理解的方式取胜', s: 'specialization' },
    { text: '随机应变，让自己的念变成所需形态', s: 'transmutation' },
  ] },
  { q: '别人形容你的性格通常是？', options: [
    { text: '直率热血，绝不藏着掖着', s: 'enhancement' },
    { text: '坦荡急躁，说话不绕弯子', s: 'emission' },
    { text: '神经质，对细节斤斤计较', s: 'conjuration' },
    { text: '理智冷静，不轻易改变想法', s: 'manipulation' },
    { text: '不合群，自有一套人生哲学', s: 'specialization' },
    { text: '情绪多变，让人捉摸不透', s: 'transmutation' },
  ] },
  { q: '若你有一种独特的念能力，最希望它能？', options: [
    { text: '让自己变得更强、更耐打', s: 'enhancement' },
    { text: '将力量投射到很远的地方', s: 'emission' },
    { text: '创造一件世上没有的东西', s: 'conjuration' },
    { text: '让别人按自己的意愿行事', s: 'manipulation' },
    { text: '拥有专属于自己的特殊规则', s: 'specialization' },
    { text: '改变物质的属性，比如让水变成酸', s: 'transmutation' },
  ] },
  { q: '你最珍视的座右铭接近哪一句？', options: [
    { text: '"努力到最后一刻，绝不放弃"', s: 'enhancement' },
    { text: '"我说一就是一，没有商量"', s: 'emission' },
    { text: '"把每件事做到无懈可击"', s: 'conjuration' },
    { text: '"成事在谋，不在勇"', s: 'manipulation' },
    { text: '"我就是我，与众不同"', s: 'specialization' },
    { text: '"灵活才是真正的力量"', s: 'transmutation' },
  ] },
  { q: '把杯子放在树叶上集中精神，你认为水会？', options: [
    { text: '水量增加，溢出杯沿', s: 'enhancement' },
    { text: '水的颜色发生改变', s: 'transmutation' },
    { text: '水中出现某种杂质或物体', s: 'conjuration' },
    { text: '水开始无故震荡或飞起', s: 'emission' },
    { text: '水的味道发生变化', s: 'manipulation' },
    { text: '出现无法用以上任何方式描述的现象', s: 'specialization' },
  ] },
]
const nenResults = {
  enhancement: { emblem: '●', color: '#d97842', cn: '强化系', en: 'ENHANCEMENT', desc: '你是天生的强化系念能力者。强化系将念用于强化物体本身的能力与机能，是六系中最为均衡也最为直接的系属。强化系的天赋者性格单纯热血，行动力强，是六系中战斗中最不需要思考的存在。', traits: ['热血', '直率', '执着', '韧性'] },
  emission: { emblem: '◆', color: '#5aa6c4', cn: '放出系', en: 'EMISSION', desc: '你是放出系的天赋者。放出系念能力者擅长将念分离于身体之外，独立操控。放出系性格急躁、不拘小节，思维直接，长于远距离作战。', traits: ['果敢', '急躁', '不羁', '远见'] },
  transmutation: { emblem: '▲', color: '#c4a05a', cn: '变化系', en: 'TRANSMUTATION', desc: '你是变化系念能力者。变化系将念改变为不同的性质，可化为电、火、橡胶等等。变化系的人性格反复无常，看似随性其实工于心计，是六系中最容易让人误解的存在。', traits: ['多变', '灵巧', '难测', '机敏'] },
  conjuration: { emblem: '■', color: '#7eb37e', cn: '具现化系', en: 'CONJURATION', desc: '你是具现化系念能力者。具现化系可将念具现化为实际存在的物体。具现化系天赋者性格神经质而严谨，思维细密，对细节有近乎偏执的追求。', traits: ['严谨', '细腻', '执着', '深沉'] },
  manipulation: { emblem: '★', color: '#b27ec4', cn: '操作系', en: 'MANIPULATION', desc: '你是操作系念能力者。操作系可操控物体或生物。操作系的天赋者理性、顽固，一旦认定的事极少改变，是六系中最具战术家气质的系属。', traits: ['理智', '冷静', '顽固', '深谋'] },
  specialization: { emblem: '✦', color: '#9a3a3a', cn: '特质系', en: 'SPECIALIZATION', desc: '你是极为罕见的特质系念能力者。特质系拥有独一无二、不属于任何其他五系的特殊能力。特质系天赋者通常个人主义强烈，性格难以捉摸，是命运钦点的"异数"。', traits: ['独特', '神秘', '孤傲', '宿命'] },
}
const nenStage = ref('intro')
const currentQ = ref(0)
const shuffledOptions = ref([])
const nenResult = ref(null)
const nenAnswers = {}

function startNenTest() {
  for (const k in nenAnswers) delete nenAnswers[k]
  currentQ.value = 0
  nenStage.value = 'question'
  showQuestion()
}
function showQuestion() {
  const q = nenQuestions[currentQ.value]
  shuffledOptions.value = [...q.options].sort(() => Math.random() - 0.5)
}
function answerNen(s) {
  nenAnswers[s] = (nenAnswers[s] || 0) + 1
  currentQ.value++
  if (currentQ.value >= nenQuestions.length) showNenResult()
  else showQuestion()
}
function showNenResult() {
  let max = 0
  let winner = 'enhancement'
  for (const k in nenAnswers) {
    if (nenAnswers[k] > max) { max = nenAnswers[k]; winner = k }
  }
  nenResult.value = nenResults[winner]
  nenStage.value = 'result'
}
function resetNenTest() {
  nenStage.value = 'intro'
}

onMounted(() => {
  runBoot()
  initParticles()
  updateCountdown()
  countdownTimer = setInterval(updateCountdown, 1000)
})

onBeforeUnmount(() => {
  bootTimers.forEach((t) => clearTimeout(t))
  if (countdownTimer) clearInterval(countdownTimer)
  if (rafId) cancelAnimationFrame(rafId)
  window.removeEventListener('pointermove', onPointerMove)
  window.removeEventListener('resize', resizeCanvas)
})
</script>

<template>
  <div class="hunter-page">
    <!-- SVG 徽章定义 -->
    <svg width="0" height="0" style="position:absolute">
      <defs>
        <symbol id="crest" viewBox="0 0 260 200">
          <g fill="currentColor">
            <rect x="14" y="14" width="20" height="172"/>
            <rect x="4" y="14" width="40" height="8"/>
            <rect x="4" y="178" width="40" height="8"/>
            <polygon points="34,80 130,100 34,120"/>
          </g>
          <g fill="currentColor">
            <rect x="226" y="14" width="20" height="172"/>
            <rect x="216" y="14" width="40" height="8"/>
            <rect x="216" y="178" width="40" height="8"/>
            <polygon points="226,80 130,100 226,120"/>
          </g>
          <polygon points="130,14 178,100 130,186 82,100" fill="#c41e1e"/>
          <polygon points="130,14 178,100 130,186 82,100" fill="none" stroke="#7a1010" stroke-width="2"/>
        </symbol>
      </defs>
    </svg>

    <!-- ===================== 入场加载页 ===================== -->
    <div class="boot-loader" :class="{ done: bootDone }" @click="enterHunter">
      <canvas ref="bootCanvas" class="boot-canvas"></canvas>
      <div class="boot-content">
        <div class="boot-emblem" style="color:var(--gold-bright)">
          <svg width="220" height="170" viewBox="0 0 260 200"><use href="#crest"/></svg>
        </div>
        <div class="boot-title">HUNTER ASSOCIATION</div>
        <div class="boot-title-cn">猎 人 协 会</div>
        <div class="boot-divider"></div>
        <div class="boot-typing">
          <div v-for="(l, i) in bootLines" :key="i" class="ok">&gt; {{ l }}</div>
          <span class="cursor"></span>
        </div>
        <div class="boot-progress">
          <div class="boot-progress-bar" :style="{ width: bootProgress + '%' }"></div>
        </div>
        <div class="boot-status">{{ bootStatus }}</div>
        <div v-if="bootReady" class="boot-enter">点击任意处进入协会</div>
      </div>
    </div>

    <!-- ===================== 顶部导航 ===================== -->
    <nav class="nav">
      <div class="nav-brand">
        <svg style="color:var(--gold)"><use href="#crest"/></svg>
        <span>HUNTER · ASSOCIATION</span>
      </div>
      <ul class="nav-links" :class="{ open: menuOpen }">
        <li><a href="#home" @click.prevent="scrollTo('home')">首页 Home</a></li>
        <li><a href="#about" @click.prevent="scrollTo('about')">协会 About</a></li>
        <li><a href="#members" @click.prevent="scrollTo('members')">成员 Members</a></li>
        <li><a href="#wanted" @click.prevent="scrollTo('wanted')">通缉 Wanted</a></li>
        <li><a href="#exam" @click.prevent="scrollTo('exam')">考试 Exam</a></li>
        <li><a href="#test" @click.prevent="scrollTo('test')">占卜 Divination</a></li>
      </ul>
      <div class="nav-actions">
        <button class="nav-back" @click="router.push('/')">返回问卷系统</button>
        <button class="nav-mobile-toggle" @click="menuOpen = !menuOpen">MENU</button>
      </div>
    </nav>

    <!-- ===================== 第一页：首页 ===================== -->
    <section id="home">
      <div class="hero-content">
        <div class="hero-emblem" style="color:var(--gold-bright)" @click="openKeyModal" title="点击中央红色菱形 · 输入训练密钥">
          <svg width="320" height="246"><use href="#crest"/></svg>
        </div>
        <div class="hero-eyebrow">EST · ANNO · MMCMXLVII</div>
        <h1 class="hero-title">HUNTER ASSOCIATION</h1>
        <div class="hero-subtitle-cn">猎 人 协 会</div>
        <p class="hero-motto">探索未知 · 直面险境 · 超越人之极限</p>

        <div class="countdown-block">
          <div class="countdown-label">距第 289 届猎人资格考试开始</div>
          <div class="countdown-grid">
            <div class="countdown-cell"><span>{{ cdDays }}</span><em>DAYS · 日</em></div>
            <div class="countdown-cell"><span>{{ cdHours }}</span><em>HOURS · 时</em></div>
            <div class="countdown-cell"><span>{{ cdMins }}</span><em>MINS · 分</em></div>
            <div class="countdown-cell"><span>{{ cdSecs }}</span><em>SECS · 秒</em></div>
          </div>
        </div>

        <div class="hero-cta">
          <a href="#about" class="btn" @click.prevent="scrollTo('about')">了解协会 EXPLORE</a>
          <a href="#exam" class="btn btn-primary" @click.prevent="scrollTo('exam')">报名考试 ENROLL</a>
        </div>
      </div>

      <div class="announcement-bar">
        <div class="announcement-bar-label">EMERGENCY · 公告</div>
        <div class="ticker">
          <template v-for="n in 2" :key="n">
            <div v-for="(a, i) in announcements" :key="n + '-' + i" class="ticker-item">{{ a }}</div>
          </template>
        </div>
      </div>
    </section>

    <!-- ===================== 协会简介 ===================== -->
    <section id="about" class="intro-section">
      <div class="section-frame">
        <div class="intro-grid">
          <div class="intro-left">
            <div class="intro-eyebrow">◆ ABOUT THE ASSOCIATION ◆</div>
            <h2 class="section-title">承袭古老誓约</h2>
            <div class="section-title-cn">协 会 简 介</div>
            <div class="divider-flourish">
              <div class="line"></div>
              <div class="diamond"></div>
              <div class="line"></div>
            </div>
            <div class="intro-text">
              <p>
                猎人协会，全称 <strong>HUNTER ASSOCIATION</strong>，是一个由各方专业人才组成的、
                横跨六大洲的国际性独立组织。协会下辖十二支首脑，向<strong>会长</strong>直接负责，
                掌管包括赏金追缉、文物寻访、稀种保护、未知大陆探索等数十种业务。
              </p>
              <p>
                自成立以来，本协会奉行<strong>"自由、克制、传承"</strong>三大誓约。
                持证猎人享有 95% 国家与地区的特殊通行权、对部分国宝级资源的优先获取权
                以及独立调查权。每年仅有不超过 <strong>30 人</strong>能成为正式持证猎人。
              </p>
              <p>
                协会同时是<strong>"念能力"</strong>这一神秘力量体系的最高研究与认证机构。
                凡通过资格考试者，皆有资格接受念之传授，迈入更高的可能性。
              </p>
            </div>
            <div class="intro-stats">
              <div class="stat"><div class="stat-number">∞</div><div class="stat-label">无限挑战 · 无限疆界</div></div>
              <div class="stat"><div class="stat-number">.0001<span style="font-size:18px;">%</span></div><div class="stat-label">资格考试通过率</div></div>
              <div class="stat"><div class="stat-number">12</div><div class="stat-label">十二支 · 协会枢机</div></div>
              <div class="stat"><div class="stat-number">6</div><div class="stat-label">念能力体系分支</div></div>
            </div>
          </div>

          <div class="intro-right">
            <div class="intro-right-content">
              <div class="seal-wrap">
                <svg class="seal-ring" viewBox="0 0 400 400" style="color:var(--gold)">
                  <defs>
                    <path id="circleTop" d="M 200,200 m -160,0 a 160,160 0 1,1 320,0" />
                    <path id="circleBot" d="M 200,200 m -160,0 a 160,160 0 1,0 320,0" />
                  </defs>
                  <circle cx="200" cy="200" r="190" fill="none" stroke="currentColor" stroke-width="1"/>
                  <circle cx="200" cy="200" r="184" fill="none" stroke="currentColor" stroke-width="0.5" opacity="0.5"/>
                  <circle cx="200" cy="200" r="160" fill="none" stroke="currentColor" stroke-width="0.8"/>
                  <circle cx="200" cy="200" r="155" fill="none" stroke="currentColor" stroke-width="0.5" opacity="0.5"/>
                  <text fill="currentColor" font-family="Cinzel, serif" font-size="16" letter-spacing="4" font-weight="600">
                    <textPath href="#circleTop" startOffset="50%" text-anchor="middle">★ HUNTER ASSOCIATION ★</textPath>
                  </text>
                  <text fill="currentColor" font-family="Cinzel, serif" font-size="13" letter-spacing="5" font-weight="500">
                    <textPath href="#circleBot" startOffset="50%" text-anchor="middle">EST · ANNO · MMCMXLVII</textPath>
                  </text>
                  <text x="20" y="208" fill="currentColor" font-size="20">✦</text>
                  <text x="370" y="208" fill="currentColor" font-size="20">✦</text>
                </svg>
                <div class="seal-center" style="color:var(--gold-bright)">
                  <svg viewBox="0 0 260 200" width="100%"><use href="#crest"/></svg>
                </div>
              </div>
              <div class="crest-text">
                <div class="crest-text-lat">Per aspera ad astra</div>
                <div class="crest-text-est">通过艰辛 · 抵达星辰</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ===================== 核心成员 ===================== -->
    <section id="members" class="members-section">
      <div class="section-frame">
        <div class="members-header">
          <div class="intro-eyebrow" style="color:var(--crimson-bright)">◆ CORE MEMBERS ◆</div>
          <h2 class="section-title">协会核心成员</h2>
          <div class="section-title-cn">名 录 · 卷 之 一</div>
          <p>下列九位为猎人协会现任核心，皆为持证三星级别以上之顶尖存在。
             其名号被记入协会百年名册，亦被记入历史。</p>
        </div>

        <div class="zodiac-wrap">
          <div class="zodiac-title">
            <div class="intro-eyebrow" style="color:var(--gold)">◆ THE ZODIAC TWELVE ◆</div>
            <h3 style="font-family:'Cinzel',serif;font-size:32px;color:var(--gold-bright);letter-spacing:0.08em;margin:8px 0">十 二 支</h3>
            <p style="color:var(--text-dim);font-style:italic;max-width:560px;margin:12px auto">由前会长尼特罗钦点的十二位顶级猎人，对应十二地支，是协会真正的决策核心。点击下方任一生肖以查阅档案。</p>
          </div>

          <div class="zodiac-compass">
            <svg class="zodiac-bg" viewBox="0 0 600 600">
              <circle cx="300" cy="300" r="280" fill="none" stroke="var(--gold-dim)" stroke-width="1" opacity="0.4"/>
              <circle cx="300" cy="300" r="260" fill="none" stroke="var(--gold-dim)" stroke-width="0.5" opacity="0.3"/>
              <circle cx="300" cy="300" r="180" fill="none" stroke="var(--gold-dim)" stroke-width="0.5" opacity="0.3"/>
              <circle cx="300" cy="300" r="120" fill="none" stroke="var(--gold)" stroke-width="0.5" opacity="0.5"/>
              <g stroke="var(--gold-dim)" stroke-width="0.5" opacity="0.3">
                <line x1="300" y1="20" x2="300" y2="580"/>
                <line x1="20" y1="300" x2="580" y2="300"/>
                <line x1="100" y1="100" x2="500" y2="500"/>
                <line x1="500" y1="100" x2="100" y2="500"/>
              </g>
            </svg>
            <div class="zodiac-center">
              <svg viewBox="0 0 260 200" width="100%" style="color:var(--gold-bright)"><use href="#crest"/></svg>
              <div class="zodiac-center-text">HUNTER<br><span>十二支</span></div>
            </div>
            <div
              v-for="z in zodiac"
              :key="z.zi"
              class="zodiac-node"
              :class="{ active: activeZodiac === z }"
              :style="zodiacPos(z)"
              @click="activeZodiac = z"
            >
              <div class="zodiac-node-inner">
                <div class="zodiac-node-zi">{{ z.zi }}</div>
                <div class="zodiac-node-pinyin">{{ z.pinyin }}</div>
              </div>
            </div>
          </div>

          <div class="zodiac-card-display">
            <div v-if="!activeZodiac" class="zodiac-card-empty">◇ 请于罗盘上选择生肖以查阅档案 ◇</div>
            <div v-else class="zodiac-card">
              <div class="zodiac-card-inner">
                <div class="zodiac-card-zi">{{ activeZodiac.zi }}</div>
                <div>
                  <div class="zodiac-card-name">{{ activeZodiac.en }}</div>
                  <div class="zodiac-card-name-cn">{{ activeZodiac.name }}</div>
                  <div class="zodiac-card-role">{{ activeZodiac.role }}</div>
                  <div class="zodiac-card-desc">{{ activeZodiac.desc }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="members-grid">
          <div v-for="m in members" :key="m.key" class="member-card" @click="activeMember = m">
            <div class="member-card-inner">
              <div class="member-image">
                <span class="member-ph">{{ m.nameCn.charAt(0) }}</span>
                <div class="member-rank-badge"><span class="stars">{{ m.stars }}</span>{{ m.rank }}</div>
              </div>
              <div class="member-info">
                <div class="member-name-en">{{ m.nameEn }}</div>
                <div class="member-name-cn">{{ m.nameCn }}</div>
                <div class="member-title">{{ m.title }}</div>
                <div class="member-meta">
                  <div class="meta-item">
                    <div class="meta-label">NEN · 念系</div>
                    <div class="meta-value"><span class="nen-tag">{{ m.nen }}</span></div>
                  </div>
                  <div class="meta-item">
                    <div class="meta-label">DIVISION · 所属</div>
                    <div class="meta-value">{{ m.affiliation }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ===================== 考试报名页 ===================== -->
    <section id="exam" class="exam-section">
      <div class="exam-frame">
        <div class="exam-inner">
          <div class="exam-watermark">CLASSIFIED · 机密</div>

          <div class="exam-title-block">
            <div class="stamp">FORM · NO.HX-289 · OFFICIAL</div>
            <h2 class="section-title">猎人资格考试</h2>
            <div class="section-title-cn">第 二 八 九 届 报 名 申 请</div>
            <div class="divider-flourish" style="max-width:300px;margin:30px auto 0">
              <div class="line"></div>
              <div class="diamond"></div>
              <div class="line"></div>
            </div>
          </div>

          <div class="exam-warning">
            <div class="exam-warning-title">⚠ 重要警示 · IMPORTANT NOTICE</div>
            <p>
              猎人资格考试历来包含<strong>极高的死亡与伤残风险</strong>。
              往届考试中最低死亡率为 <strong>78%</strong>，最高一届
              参考人员仅有 <strong>1 人</strong>幸存。本协会不对考生在考试期间发生的
              任何身体伤害、精神损伤或<strong>失踪死亡事件</strong>承担法律责任。
              请<strong>充分评估自身意愿</strong>后再行提交。
            </p>
          </div>

          <div class="exam-stats-row">
            <div class="exam-stat"><div class="exam-stat-num">289</div><div class="exam-stat-label">届数</div></div>
            <div class="exam-stat"><div class="exam-stat-num">~30</div><div class="exam-stat-label">预计录取</div></div>
            <div class="exam-stat"><div class="exam-stat-num">5</div><div class="exam-stat-label">阶段考核</div></div>
            <div class="exam-stat"><div class="exam-stat-num">∞</div><div class="exam-stat-label">未知变数</div></div>
          </div>

          <form @submit.prevent="submitForm">
            <div class="form-group">
              <label>Name <span class="label-cn">姓名</span><span class="req">*</span></label>
              <input type="text" required placeholder="请输入您的真实姓名 / Full Name" />
            </div>
            <div class="form-group">
              <label>Age <span class="label-cn">年龄</span><span class="req">*</span></label>
              <input type="number" required min="10" max="120" placeholder="12 岁及以上方可报名" />
            </div>
            <div class="form-group">
              <label>Nationality <span class="label-cn">国籍</span><span class="req">*</span></label>
              <input type="text" required placeholder="请填写所属国家或地区" />
            </div>
            <div class="form-group">
              <label>Referrer <span class="label-cn">推荐人</span></label>
              <input type="text" placeholder="持证猎人姓名（可选）" />
            </div>
            <div class="form-group">
              <label>Emergency Contact <span class="label-cn">紧急联系人</span><span class="req">*</span></label>
              <input type="text" required placeholder="姓名" />
            </div>
            <div class="form-group">
              <label>Contact Number <span class="label-cn">联系方式</span><span class="req">*</span></label>
              <input type="text" required placeholder="电话 / 邮箱 / 通讯地址" />
            </div>
            <div class="form-group">
              <label>Email <span class="label-cn">邮箱</span><span class="req">*</span></label>
              <input v-model="hunterEmail" type="email" required placeholder="用于接收考前训练密钥" />
            </div>
            <div class="form-group full">
              <label>Hunter Classification <span class="label-cn">志愿猎人类别</span><span class="req">*</span></label>
              <select v-model="hunterClass" required>
                <option value="">-- 请选择您希望专精的方向 --</option>
                <option value="gourmet">美食猎人 Gourmet Hunter</option>
                <option value="bounty">赏金猎人 Blacklist Hunter</option>
                <option value="ruins">遗迹猎人 Ruins Hunter</option>
                <option value="rare">稀种猎人 Rare Beast Hunter</option>
                <option value="archaeologist">考古猎人 Archaeological Hunter</option>
                <option value="sacred">圣物猎人 Sacred Treasure Hunter</option>
                <option value="dark">暗黑大陆探索 Dark Continent Expedition</option>
                <option value="other">其他 / Other</option>
              </select>
            </div>
            <div class="form-group full">
              <label>Statement of Purpose <span class="label-cn">申请理由</span><span class="req">*</span></label>
              <textarea required placeholder="请陈述您报考猎人协会的真实理由（500 字以内）"></textarea>
            </div>

            <label class="form-checkbox">
              <input type="checkbox" required />
              <span class="check-box"></span>
              <span>
                本人已阅读并完全理解上述风险警示。本人自愿承担考试过程中可能发生的
                一切伤害、损失或死亡之后果，并放弃就此追究猎人协会及相关人员任何法律责任之权利。
                <br><em style="color:var(--gold-dim);font-size:12px">I have read and understood the risks. I waive all liability of the Hunter Association.</em>
              </span>
            </label>

            <div class="form-submit-row">
              <button type="submit" class="btn-submit" :disabled="submitting">{{ submitting ? '受理中…' : '提交申请 · SUBMIT' }}</button>
            </div>
          </form>
        </div>
      </div>
    </section>

    <!-- ===================== 通缉令 / 赏金榜 ===================== -->
    <section id="wanted" class="wanted-section">
      <div class="section-frame">
        <div style="text-align:center;margin-bottom:60px">
          <div class="intro-eyebrow" style="color:var(--crimson-bright)">◆ MOST WANTED · 通缉名录 ◆</div>
          <h2 class="section-title" style="color:#d97070">赏 金 榜</h2>
          <div class="section-title-cn">名 录 · 卷 之 二</div>
          <p style="color:var(--text-dim);font-style:italic;max-width:680px;margin:24px auto;line-height:1.8">
            协会本部对外公开通缉之危险目标。如有持证猎人捕获或击杀名单上人物，
            请第一时间向最近协会驻点上报，赏金将于核实后 48 小时内全额支付。
            <br><strong style="color:#d97070">禁止单独行动 · 务必组队 · 详阅警示</strong>
          </p>
        </div>

        <div class="wanted-grid">
          <div v-for="(w, i) in wanted" :key="i" class="wanted-poster">
            <div class="wanted-inner">
              <div class="wanted-stamp">WANTED</div>
              <div class="wanted-sub">通 缉 · 第 {{ 100 + i * 137 }} 号令</div>
              <div class="wanted-portrait"><div class="silhouette">{{ w.icon }}</div></div>
              <div class="wanted-name">{{ w.name }}</div>
              <div class="wanted-alias">{{ w.alias }}</div>
              <div class="wanted-bounty">
                <div class="wanted-bounty-label">REWARD · 悬赏</div>
                <div class="wanted-bounty-amount">{{ w.bounty }}</div>
              </div>
              <div class="wanted-info">
                <div class="row"><span class="l">THREAT · 威胁</span><span class="r" :class="'threat-' + w.threat">★ {{ w.threat }} 级</span></div>
                <div class="row"><span class="l">CLASS · 分类</span><span class="r">{{ w.cls }}</span></div>
                <div class="row"><span class="l">SEEN · 出没</span><span class="r">{{ w.lastSeen }}</span></div>
                <div class="row"><span class="l">NEN · 念系</span><span class="r">{{ w.ability }}</span></div>
                <div class="wanted-danger">⚠ {{ w.danger }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ===================== 念能力体系 ===================== -->
    <section id="system" class="intro-section" style="background:var(--bg-dark)">
      <div class="section-frame">
        <div style="text-align:center;margin-bottom:60px">
          <div class="intro-eyebrow">◆ THE SIX CATEGORIES OF NEN ◆</div>
          <h2 class="section-title">念之六系</h2>
          <div class="section-title-cn">能 力 体 系</div>
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:24px;max-width:1100px;margin:0 auto">
          <div class="nen-card"><div class="nen-symbol">●</div><div class="nen-name-cn">强化系</div><div class="nen-name-en">ENHANCEMENT</div><div class="nen-desc">强化物体本身的能力与机能。<br>性格单纯而热血。</div></div>
          <div class="nen-card"><div class="nen-symbol">◆</div><div class="nen-name-cn">放出系</div><div class="nen-name-en">EMISSION</div><div class="nen-desc">将念分离于身体之外。<br>性格急躁果敢。</div></div>
          <div class="nen-card"><div class="nen-symbol">▲</div><div class="nen-name-cn">变化系</div><div class="nen-name-en">TRANSMUTATION</div><div class="nen-desc">改变念的性质。<br>性格反复无常。</div></div>
          <div class="nen-card"><div class="nen-symbol">■</div><div class="nen-name-cn">具现化系</div><div class="nen-name-en">CONJURATION</div><div class="nen-desc">将念具现为实体。<br>性格神经质而严谨。</div></div>
          <div class="nen-card"><div class="nen-symbol">★</div><div class="nen-name-cn">操作系</div><div class="nen-name-en">MANIPULATION</div><div class="nen-desc">操控物体或生物。<br>性格理性顽固。</div></div>
          <div class="nen-card"><div class="nen-symbol">✦</div><div class="nen-name-cn">特质系</div><div class="nen-name-en">SPECIALIZATION</div><div class="nen-desc">独一无二的特殊能力。<br>性格个人主义。</div></div>
        </div>
      </div>
    </section>

    <!-- ===================== 念之水见式测试 ===================== -->
    <section id="test" class="test-section">
      <div class="section-frame">
        <div style="text-align:center;margin-bottom:60px">
          <div class="intro-eyebrow" style="color:var(--gold)">◆ WATER DIVINATION · 水 见 式 ◆</div>
          <h2 class="section-title">念之系属测验</h2>
          <div class="section-title-cn">古 老 占 卜 · 系 属 觉 醒</div>
          <p style="color:var(--text-dim);font-style:italic;max-width:680px;margin:24px auto;line-height:1.8">
            水见式乃念能力者最古老的觉醒测试。<br>
            将玻璃杯置于树叶之上，集中意念，水之变化将昭示你的天赋系属。
          </p>
        </div>

        <div class="test-container">
          <div v-if="nenStage === 'intro'" class="test-stage">
            <div class="cup-container">
              <svg class="cup-svg" viewBox="0 0 200 240">
                <ellipse cx="100" cy="225" rx="80" ry="8" fill="#3a4a2a" opacity="0.8"/>
                <path d="M 30 225 Q 100 215 170 225" fill="none" stroke="#5a6a3a" stroke-width="1"/>
                <path d="M 60 80 L 140 80 L 135 220 L 65 220 Z" fill="rgba(201, 169, 97, 0.1)" stroke="var(--gold)" stroke-width="1.5"/>
                <path d="M 65 140 Q 100 135 135 140 L 132 215 L 68 215 Z" fill="rgba(90, 166, 196, 0.4)" stroke="rgba(90, 166, 196, 0.7)" stroke-width="1"/>
                <ellipse cx="100" cy="140" rx="35" ry="3" fill="rgba(200, 230, 240, 0.4)"/>
              </svg>
            </div>
            <div class="test-intro-text">
              <p style="margin-bottom: 24px;">
                通过下方 6 道问题的回答，水见式将测算出最契合您本质的念系系属。
                请凭直觉作答，不必深思。
              </p>
              <button class="btn btn-primary" @click="startNenTest">开始占卜 · BEGIN</button>
            </div>
          </div>

          <div v-else-if="nenStage === 'question'" class="test-stage">
            <div class="test-progress">
              <span>Q {{ currentQ + 1 }} / {{ nenQuestions.length }}</span>
              <div class="test-progress-bar"><div :style="{ width: (currentQ / nenQuestions.length) * 100 + '%' }"></div></div>
            </div>
            <div class="test-question-text">{{ nenQuestions[currentQ].q }}</div>
            <div class="test-options">
              <button v-for="(o, i) in shuffledOptions" :key="i" class="test-option" @click="answerNen(o.s)">{{ o.text }}</button>
            </div>
          </div>

          <div v-else class="test-stage">
            <div class="flip-scene">
              <div class="flip-card">
                <div class="flip-face flip-back">
                  <div class="flip-back-symbol">✧</div>
                  <div class="flip-back-title">水 见 式</div>
                  <div class="flip-back-sub">WATER DIVINATION</div>
                </div>
                <div class="flip-face flip-front">
                  <div class="result-emblem" :style="{ color: nenResult.color }">{{ nenResult.emblem }}</div>
                  <div class="result-eyebrow">YOUR DIVINATION REVEALS</div>
                  <h3 class="result-title">{{ nenResult.cn }}</h3>
                  <div class="result-en">{{ nenResult.en }}</div>
                  <div class="result-desc">{{ nenResult.desc }}</div>
                  <div class="result-traits">
                    <div v-for="(t, i) in nenResult.traits" :key="i" class="trait-tag">{{ t }}</div>
                  </div>
                </div>
              </div>
            </div>
            <div class="result-actions">
              <button class="btn" @click="resetNenTest">重新占卜 · RESTART</button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ===================== 页脚 ===================== -->
    <footer>
      <div class="footer-grid">
        <div class="footer-brand">
          <div class="nav-brand" style="margin-bottom:20px">
            <svg style="color:var(--gold);width:42px;height:32px"><use href="#crest"/></svg>
            <span>HUNTER · ASSOCIATION</span>
          </div>
          <p>
            承袭古老誓约，守护未知疆界。<br>
            猎人协会本部 · 三角山行政中央<br>
            <span style="color:var(--gold-dim)">Per aspera ad astra</span>
          </p>
        </div>
        <div class="footer-col">
          <h4>本部</h4>
          <ul>
            <li><a href="#about" @click.prevent="scrollTo('about')">协会简介</a></li>
            <li><a href="#members" @click.prevent="scrollTo('members')">核心成员</a></li>
            <li><a href="#members" @click.prevent="scrollTo('members')">十二支</a></li>
            <li><a href="#wanted" @click.prevent="scrollTo('wanted')">通缉名录</a></li>
          </ul>
        </div>
        <div class="footer-col">
          <h4>事务</h4>
          <ul>
            <li><a href="#exam" @click.prevent="scrollTo('exam')">资格考试</a></li>
            <li><a href="#system" @click.prevent="scrollTo('system')">念之六系</a></li>
            <li><a href="#test" @click.prevent="scrollTo('test')">水见式占卜</a></li>
            <li><a href="#" @click.prevent>任务公开</a></li>
          </ul>
        </div>
        <div class="footer-col">
          <h4>联络</h4>
          <ul>
            <li><a href="#" @click.prevent>紧急通讯</a></li>
            <li><a href="#" @click.prevent>公共关系</a></li>
            <li><a href="#" @click.prevent>保密条款</a></li>
            <li><a href="#" @click.prevent>十诫</a></li>
          </ul>
        </div>
      </div>
      <div class="footer-bottom">
        <div>© ANNO MMCMXLVII–MMXXVI · HUNTER ASSOCIATION</div>
        <div>ALL RIGHTS RESERVED · 不得擅自复制传播</div>
      </div>
    </footer>

    <!-- ===================== 成员详情模态 ===================== -->
    <div v-if="activeMember" class="modal-overlay active" @click.self="activeMember = null">
      <div class="modal">
        <div class="modal-inner">
          <button class="modal-close" @click="activeMember = null">✕</button>
          <div class="modal-body">
            <div class="modal-portrait">
              <span class="member-ph">{{ activeMember.nameCn.charAt(0) }}</span>
            </div>
            <div class="modal-info">
              <h2>{{ activeMember.nameEn }}</h2>
              <h1>{{ activeMember.nameCn }}</h1>
              <div class="role">{{ activeMember.title }}</div>
              <div class="modal-stats">
                <div><div class="modal-stat-label">RANK · 等级</div><div class="modal-stat-value">{{ activeMember.stars }} {{ activeMember.rank }}</div></div>
                <div><div class="modal-stat-label">NEN · 念系</div><div class="modal-stat-value">{{ activeMember.nen }}</div></div>
                <div><div class="modal-stat-label">DIVISION · 所属</div><div class="modal-stat-value">{{ activeMember.affiliation }}</div></div>
              </div>
              <div class="modal-section-title">个人简介 · BIOGRAPHY</div>
              <p>{{ activeMember.bio }}</p>
              <div class="modal-section-title">代表战绩 · NOTABLE RECORDS</div>
              <p>{{ activeMember.battle }}</p>
              <div class="modal-quote">{{ activeMember.quote }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===================== 提交成功 ===================== -->
    <div v-if="showSuccess" class="success-overlay active" @click.self="showSuccess = false">
      <div class="success-card">
        <div class="success-card-inner">
          <div class="success-seal"><span>GRANTED<br>授权</span></div>
          <div class="success-stamp">报名成功！</div>
          <div class="success-title">TRAINING CHANNEL OPENED</div>
          <div class="success-title-cn">考 前 训 练 渠 道 已 开 通</div>
          <p class="success-text">
            我们已为您开通考前训练渠道，请自行探索吧！<br>
            专属密钥已发送至邮箱
            <strong style="color:var(--gold-bright)">{{ hunterEmail }}</strong>，请查收。
          </p>
          <div class="success-hint">密钥长期有效 · 请妥善保管 · 切勿泄露</div>
          <button class="btn" @click="showSuccess = false">关闭 CLOSE</button>
        </div>
      </div>
    </div>

    <!-- ===================== 训练密钥输入 ===================== -->
    <div v-if="keyModalOpen" class="success-overlay active" @click.self="closeKeyModal">
      <div class="success-card">
        <div class="success-card-inner">
          <button class="modal-close" @click="closeKeyModal">✕</button>

          <!-- 第一步：输入密钥 -->
          <template v-if="keyStage === 'key'">
            <div class="success-seal"><span>ACCESS<br>密钥</span></div>
            <div class="success-title" style="font-size:22px">TRAINING ACCESS</div>
            <div class="success-title-cn">输 入 训 练 密 钥</div>
            <p class="success-text">请输入您邮箱中收到的猎人训练密钥。</p>
            <input
              v-model="keyInput"
              class="key-input"
              type="text"
              placeholder="HT-XXXX-XXXX-XXXX"
              autocomplete="off"
              @keyup.enter="verifyKey"
            />
            <div v-if="keyError" class="key-error">{{ keyError }}</div>
            <div class="key-actions">
              <button class="btn" @click="closeKeyModal">取消 CANCEL</button>
              <button class="btn btn-primary" @click="verifyKey" :disabled="keyChecking">
                {{ keyChecking ? '验证中…' : '确认 ENTER' }}
              </button>
            </div>
          </template>

          <!-- 第二步：确认专精方向 + 选择念系 -->
          <template v-else>
            <div class="success-seal"><span>PATH<br>方向</span></div>
            <div class="success-title" style="font-size:22px">CONFIRM SPECIALIZATION</div>
            <div class="success-title-cn">确 认 专 精 方 向 与 念 系</div>
            <p class="success-text">密钥验证通过。请确认本次训练的方向与念系：</p>

            <div class="select-field">
              <label>专精方向 <span>SPECIALIZATION</span></label>
              <select v-model="trainClass">
                <option value="" disabled>-- 选择专精方向 --</option>
                <option v-for="c in trainClasses" :key="c.code" :value="c.code">{{ c.cn }} · {{ c.en }}</option>
              </select>
            </div>

            <div class="select-field">
              <label>念系 <span>NEN TYPE</span></label>
              <select v-model="nenType">
                <option value="" disabled>-- 选择念系 --</option>
                <option v-for="n in nenTypes" :key="n.code" :value="n.code">{{ n.cn }} · {{ n.en }}</option>
              </select>
            </div>

            <div class="key-actions">
              <button class="btn" @click="keyStage = 'key'">返回 BACK</button>
              <button class="btn btn-primary" @click="confirmTraining" :disabled="!trainClass || !nenType">
                进入训练 ENTER
              </button>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.hunter-page {
  --bg-deep: #0a0705;
  --bg-dark: #14100a;
  --bg-card: #1a1410;
  --gold: #c9a961;
  --gold-bright: #e8c878;
  --gold-dim: #8a7140;
  --crimson: #6b1a1a;
  --crimson-bright: #a02828;
  --parchment: #d9c9a3;
  --text-dim: #8a7e6a;
  --line: rgba(201, 169, 97, 0.25);
  --line-strong: rgba(201, 169, 97, 0.5);

  min-height: 100vh;
  background: var(--bg-deep);
  color: var(--parchment);
  font-family: 'Cormorant Garamond', 'Noto Serif SC', 'Songti SC', 'SimSun', serif;
  font-size: 17px;
  line-height: 1.7;
  overflow-x: hidden;
  position: relative;
  background-image:
    radial-gradient(ellipse at 20% 10%, rgba(201, 169, 97, 0.04) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 90%, rgba(107, 26, 26, 0.05) 0%, transparent 50%);
}

.hunter-page::before {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 1;
  opacity: 0.06;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' /%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' /%3E%3C/svg%3E");
  mix-blend-mode: overlay;
}

/* ===================== 入场加载页 ===================== */
.boot-loader {
  position: fixed;
  inset: 0;
  background: #050403;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 1s, visibility 1s;
}
.boot-loader.done { opacity: 0; visibility: hidden; pointer-events: none; }
.boot-loader::before {
  content: '';
  position: absolute;
  width: 700px; height: 700px;
  border: 1px solid var(--line);
  border-radius: 50%;
  animation: rotate-slow 40s linear infinite;
  opacity: 0.4;
}
.boot-loader::after {
  content: '';
  position: absolute;
  width: 500px; height: 500px;
  border: 1px dashed var(--line);
  border-radius: 50%;
  animation: rotate-slow 30s linear infinite reverse;
  opacity: 0.5;
}
@keyframes rotate-slow { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.boot-canvas { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; }
.boot-content { text-align: center; position: relative; z-index: 2; max-width: 90vw; }
.boot-emblem { margin: 0 auto 24px; filter: drop-shadow(0 0 18px rgba(232, 200, 120, 0.8)) drop-shadow(0 0 40px rgba(201, 169, 97, 0.5)); animation: boot-pulse 2s ease-in-out infinite; }
@keyframes boot-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.03); }
}
.boot-title {
  font-family: 'Cinzel', 'Times New Roman', serif;
  font-weight: 800;
  font-size: clamp(24px, 4vw, 36px);
  letter-spacing: 0.3em;
  color: var(--gold-bright);
  margin-bottom: 8px;
  text-shadow:
    0 0 8px rgba(232, 200, 120, 0.9),
    0 0 24px rgba(232, 200, 120, 0.6),
    0 0 48px rgba(201, 169, 97, 0.4),
    0 0 90px rgba(201, 169, 97, 0.25);
  animation: boot-glitch 3.2s infinite;
}
@keyframes boot-glitch {
  0%, 88%, 100% {
    text-shadow:
      0 0 8px rgba(232, 200, 120, 0.9),
      0 0 24px rgba(232, 200, 120, 0.6),
      0 0 48px rgba(201, 169, 97, 0.4),
      0 0 90px rgba(201, 169, 97, 0.25);
    transform: translateX(0);
  }
  90% { text-shadow: -3px 0 rgba(255, 45, 85, 0.9), 3px 0 rgba(0, 229, 255, 0.9); transform: translateX(3px) skewX(2deg); }
  92% { text-shadow: 3px 0 rgba(255, 45, 85, 0.9), -3px 0 rgba(0, 229, 255, 0.9); transform: translateX(-3px) skewX(-2deg); }
  94% { text-shadow: -1px 0 rgba(255, 45, 85, 0.9), 1px 0 rgba(0, 229, 255, 0.9); transform: translateX(1px); }
  96% { text-shadow: 0 0 8px rgba(232, 200, 120, 0.9), 0 0 24px rgba(232, 200, 120, 0.6), 0 0 48px rgba(201, 169, 97, 0.4); transform: translateX(0); }
}
.boot-title-cn { font-family: 'Noto Serif SC', 'Songti SC', serif; font-size: 14px; letter-spacing: 0.6em; color: var(--text-dim); margin-bottom: 30px; }
.boot-divider { width: 200px; height: 1px; background: linear-gradient(90deg, transparent, var(--gold), transparent); margin: 0 auto 30px; }
.boot-typing {
  font-family: 'JetBrains Mono', 'Consolas', monospace;
  font-size: 12px;
  color: var(--gold-dim);
  letter-spacing: 0.15em;
  height: 80px;
  margin-bottom: 24px;
  white-space: pre-line;
  line-height: 1.8;
}
.boot-typing .ok { color: var(--gold-bright); }
.boot-typing .cursor { display: inline-block; width: 8px; height: 12px; background: var(--gold); margin-left: 2px; animation: blink 1s infinite; }
@keyframes blink { 50% { opacity: 0; } }
.boot-progress { width: 300px; max-width: 80vw; height: 2px; background: rgba(201, 169, 97, 0.15); margin: 0 auto 16px; overflow: hidden; }
.boot-progress-bar { height: 100%; width: 0%; background: linear-gradient(90deg, var(--crimson), var(--gold)); transition: width 0.3s; box-shadow: 0 0 12px var(--gold), 0 0 24px rgba(232, 200, 120, 0.5); }
.boot-status { font-family: 'JetBrains Mono', 'Consolas', monospace; font-size: 10px; letter-spacing: 0.3em; color: var(--gold); text-shadow: 0 0 10px rgba(232, 200, 120, 0.7); }
.boot-enter { margin-top: 22px; font-family: 'Cinzel', 'Noto Serif SC', serif; font-size: 12px; letter-spacing: 0.3em; color: var(--gold); text-shadow: 0 0 12px rgba(232, 200, 120, 0.6); animation: blink 1.2s infinite; cursor: pointer; }

/* ===================== 顶部导航 ===================== */
.nav {
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 100;
  background: rgba(10, 7, 5, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--line);
  padding: 14px 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.nav-brand { display: flex; align-items: center; gap: 12px; font-family: 'Cinzel', 'Times New Roman', serif; font-weight: 700; letter-spacing: 0.18em; font-size: 13px; color: var(--gold); }
.nav-brand svg { width: 36px; height: 28px; }
.nav-links { display: flex; gap: 28px; list-style: none; margin: 0; padding: 0; }
.nav-links a {
  color: var(--text-dim);
  text-decoration: none;
  font-family: 'Cinzel', 'Times New Roman', serif;
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  transition: color 0.3s, text-shadow 0.3s;
  position: relative;
}
.nav-links a:hover { color: var(--gold-bright); text-shadow: 0 0 12px rgba(232, 200, 120, 0.5); }
.nav-links a::after { content: ''; position: absolute; left: 50%; bottom: -6px; width: 0; height: 1px; background: var(--gold); transition: width 0.3s, left 0.3s; }
.nav-links a:hover::after { width: 100%; left: 0; }
.nav-mobile-toggle { display: none; background: none; border: 1px solid var(--line); color: var(--gold); padding: 8px 12px; cursor: pointer; font-family: 'Cinzel', serif; font-size: 12px; letter-spacing: 0.15em; }
.nav-actions { display: flex; align-items: center; gap: 12px; }
.nav-back {
  background: none;
  border: 1px solid var(--gold-dim);
  color: var(--gold);
  padding: 8px 16px;
  cursor: pointer;
  font-family: 'Cinzel', 'Noto Serif SC', serif;
  font-size: 12px;
  letter-spacing: 0.12em;
  transition: all 0.3s;
  white-space: nowrap;
}
.nav-back:hover { border-color: var(--gold-bright); color: var(--gold-bright); text-shadow: 0 0 12px rgba(232, 200, 120, 0.5); box-shadow: 0 0 14px rgba(201, 169, 97, 0.25); }

section { min-height: 100vh; padding: 120px 60px 80px; position: relative; z-index: 2; }
.section-frame { max-width: 1280px; margin: 0 auto; position: relative; }

/* ===================== 首页 ===================== */
#home { display: flex; align-items: center; justify-content: center; text-align: center; background: radial-gradient(ellipse at center, rgba(201, 169, 97, 0.08) 0%, transparent 60%), var(--bg-deep); overflow: hidden; }
#home::before { content: ''; position: absolute; width: 900px; height: 900px; border: 1px solid var(--line); border-radius: 50%; animation: rotate-slow 60s linear infinite; opacity: 0.4; }
#home::after { content: ''; position: absolute; width: 600px; height: 600px; border: 1px dashed var(--line); border-radius: 50%; animation: rotate-slow 40s linear infinite reverse; opacity: 0.5; }
.hero-content { position: relative; z-index: 3; animation: fade-up 1.5s ease-out; }
@keyframes fade-up { from { opacity: 0; transform: translateY(40px); } to { opacity: 1; transform: translateY(0); } }
.hero-emblem { width: 320px; height: 246px; margin: 0 auto 40px; filter: drop-shadow(0 0 30px rgba(201, 169, 97, 0.4)); animation: float 6s ease-in-out infinite; cursor: pointer; transition: filter 0.4s; }
.hero-emblem:hover { filter: drop-shadow(0 0 42px rgba(232, 200, 120, 0.8)) drop-shadow(0 0 26px rgba(196, 30, 30, 0.55)); }
@keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-12px); } }
.hero-eyebrow { font-family: 'JetBrains Mono', 'Consolas', monospace; font-size: 11px; letter-spacing: 0.5em; color: var(--gold-dim); text-transform: uppercase; margin-bottom: 24px; }
.hero-title { font-family: 'Cinzel', 'Times New Roman', serif; font-weight: 900; font-size: clamp(48px, 8vw, 96px); line-height: 1; letter-spacing: 0.08em; color: var(--gold-bright); margin: 0 0 16px; text-shadow: 0 0 40px rgba(201, 169, 97, 0.3); }
.hero-subtitle-cn { font-family: 'Noto Serif SC', 'Songti SC', serif; font-weight: 300; font-size: clamp(20px, 2.5vw, 28px); letter-spacing: 0.5em; color: var(--parchment); margin-bottom: 40px; padding-left: 0.5em; }
.hero-motto { font-family: 'Cormorant Garamond', 'Georgia', serif; font-style: italic; font-size: 22px; color: var(--text-dim); max-width: 600px; margin: 0 auto 50px; position: relative; }
.hero-motto::before, .hero-motto::after { content: ''; display: inline-block; width: 60px; height: 1px; background: var(--gold-dim); vertical-align: middle; margin: 0 20px; }
.countdown-block { margin: 0 auto 40px; max-width: 600px; }
.countdown-label { font-family: 'Cinzel', serif; font-size: 11px; letter-spacing: 0.4em; color: var(--gold-dim); margin-bottom: 16px; text-transform: uppercase; }
.countdown-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.countdown-cell { background: rgba(20, 16, 10, 0.6); border: 1px solid var(--line); padding: 14px 8px; text-align: center; backdrop-filter: blur(4px); transition: border-color 0.3s; }
.countdown-cell:hover { border-color: var(--gold); }
.countdown-cell span { display: block; font-family: 'Cinzel', serif; font-weight: 800; font-size: clamp(28px, 4vw, 40px); color: var(--gold-bright); line-height: 1; text-shadow: 0 0 12px rgba(232, 200, 120, 0.3); }
.countdown-cell em { display: block; font-style: normal; font-family: 'JetBrains Mono', monospace; font-size: 9px; letter-spacing: 0.2em; color: var(--text-dim); margin-top: 6px; }
.hero-cta { display: inline-flex; gap: 24px; flex-wrap: wrap; justify-content: center; }

.btn {
  display: inline-flex; align-items: center; gap: 12px; padding: 16px 40px;
  background: transparent; border: 1px solid var(--gold); color: var(--gold);
  font-family: 'Cinzel', serif; font-size: 12px; font-weight: 600; letter-spacing: 0.3em;
  text-transform: uppercase; text-decoration: none; cursor: pointer; transition: all 0.4s; position: relative; overflow: hidden;
}
.btn::before { content: ''; position: absolute; inset: 0; background: linear-gradient(90deg, transparent, rgba(201, 169, 97, 0.15), transparent); transform: translateX(-100%); transition: transform 0.6s; }
.btn:hover { background: rgba(201, 169, 97, 0.08); color: var(--gold-bright); box-shadow: 0 0 30px rgba(201, 169, 97, 0.3); }
.btn:hover::before { transform: translateX(100%); }
.btn-primary { background: linear-gradient(180deg, var(--crimson) 0%, #4a1010 100%); border-color: var(--gold); color: var(--gold-bright); }
.btn-primary:hover { background: linear-gradient(180deg, var(--crimson-bright) 0%, var(--crimson) 100%); }

.announcement-bar { position: absolute; bottom: 0; left: 0; right: 0; background: rgba(20, 16, 10, 0.9); border-top: 1px solid var(--line); padding: 14px 0; overflow: hidden; z-index: 4; }
.announcement-bar-label { position: absolute; left: 0; top: 0; bottom: 0; background: var(--crimson); color: var(--gold-bright); padding: 14px 24px; font-family: 'Cinzel', serif; font-size: 11px; letter-spacing: 0.25em; font-weight: 600; z-index: 2; display: flex; align-items: center; }
.ticker { display: flex; animation: ticker 60s linear infinite; white-space: nowrap; padding-left: 160px; }
@keyframes ticker { from { transform: translateX(0); } to { transform: translateX(-50%); } }
.ticker-item { padding: 0 50px; font-family: 'Noto Serif SC', 'Songti SC', serif; font-size: 14px; color: var(--parchment); position: relative; }
.ticker-item::after { content: '✦'; position: absolute; right: -8px; color: var(--gold-dim); }

/* ===================== 协会简介 ===================== */
.intro-section { background: linear-gradient(180deg, var(--bg-deep) 0%, var(--bg-dark) 100%); padding: 140px 60px; }
.intro-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 80px; align-items: center; max-width: 1200px; margin: 0 auto; }
.intro-left { position: relative; }
.intro-eyebrow { font-family: 'JetBrains Mono', 'Consolas', monospace; font-size: 11px; letter-spacing: 0.5em; color: var(--crimson-bright); margin-bottom: 20px; }
.section-title { font-family: 'Cinzel', serif; font-weight: 700; font-size: 52px; line-height: 1.1; color: var(--gold-bright); margin: 0 0 12px; letter-spacing: 0.04em; }
.section-title-cn { font-family: 'Noto Serif SC', 'Songti SC', serif; font-weight: 300; font-size: 22px; color: var(--text-dim); letter-spacing: 0.3em; margin-bottom: 32px; }
.divider-flourish { display: flex; align-items: center; gap: 12px; margin-bottom: 40px; }
.divider-flourish .line { flex: 1; height: 1px; background: linear-gradient(90deg, var(--gold-dim), transparent); }
.divider-flourish .diamond { width: 8px; height: 8px; background: var(--gold); transform: rotate(45deg); }
.intro-text p { margin: 0 0 20px; color: var(--parchment); font-size: 17px; line-height: 1.9; }
.intro-text strong { color: var(--gold-bright); font-weight: 600; }
.intro-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 50px; }
.stat { border-top: 1px solid var(--line); padding-top: 20px; }
.stat-number { font-family: 'Cinzel', serif; font-weight: 800; font-size: 42px; color: var(--gold-bright); line-height: 1; }
.stat-label { font-family: 'Noto Serif SC', 'Songti SC', serif; font-size: 13px; color: var(--text-dim); letter-spacing: 0.15em; margin-top: 8px; }
.intro-right { position: relative; aspect-ratio: 3/4; border: 1px solid var(--line); padding: 20px; background: linear-gradient(135deg, rgba(201, 169, 97, 0.03), transparent), var(--bg-card); }
.intro-right::before { content: ''; position: absolute; inset: 8px; border: 1px solid var(--line); pointer-events: none; }
.intro-right-content { height: 100%; display: flex; flex-direction: column; justify-content: space-between; padding: 30px; position: relative; }
.seal-wrap { position: relative; width: 100%; flex: 1; display: flex; align-items: center; justify-content: center; aspect-ratio: 1; max-width: 420px; margin: 0 auto; }
.seal-ring { position: absolute; inset: 0; width: 100%; height: 100%; animation: rotate-slow 80s linear infinite; }
.seal-center { position: relative; width: 56%; z-index: 2; filter: drop-shadow(0 0 20px rgba(196, 30, 30, 0.3)); }
.crest-text { text-align: center; border-top: 1px solid var(--line); padding-top: 24px; }
.crest-text-lat { font-family: 'Cinzel', serif; font-style: italic; font-size: 14px; color: var(--gold); letter-spacing: 0.15em; }
.crest-text-est { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--text-dim); letter-spacing: 0.4em; margin-top: 12px; }

/* ===================== 核心成员 ===================== */
.members-section { background: var(--bg-dark); padding: 140px 60px; position: relative; }
.members-header { text-align: center; max-width: 800px; margin: 0 auto 80px; }
.members-header p { color: var(--text-dim); font-size: 18px; font-style: italic; margin-top: 24px; }
.zodiac-wrap { max-width: 1280px; margin: 0 auto 60px; }
.zodiac-title { text-align: center; margin-bottom: 40px; }
.zodiac-compass { position: relative; width: 600px; max-width: 90vw; aspect-ratio: 1; margin: 0 auto; }
.zodiac-bg { position: absolute; inset: 0; width: 100%; height: 100%; animation: rotate-slow 120s linear infinite; }
.zodiac-center { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 30%; aspect-ratio: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; filter: drop-shadow(0 0 20px rgba(196, 30, 30, 0.3)); pointer-events: none; }
.zodiac-center-text { font-family: 'Cinzel', serif; font-size: 11px; letter-spacing: 0.3em; color: var(--gold); text-align: center; margin-top: 8px; }
.zodiac-center-text span { font-family: 'Noto Serif SC', 'Songti SC', serif; font-size: 10px; color: var(--text-dim); letter-spacing: 0.2em; }
.zodiac-node { position: absolute; width: 80px; height: 80px; transform: translate(-50%, -50%); cursor: pointer; z-index: 3; }
.zodiac-node-inner { width: 100%; height: 100%; background: var(--bg-card); border: 1px solid var(--gold-dim); border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center; transition: all 0.4s; }
.zodiac-node:hover .zodiac-node-inner, .zodiac-node.active .zodiac-node-inner { border-color: var(--gold); background: rgba(107, 26, 26, 0.3); box-shadow: 0 0 20px rgba(201, 169, 97, 0.4); transform: scale(1.1); }
.zodiac-node-zi { font-family: 'Noto Serif SC', 'Songti SC', serif; font-size: 22px; color: var(--gold-bright); font-weight: 600; line-height: 1; }
.zodiac-node-pinyin { font-family: 'JetBrains Mono', 'Consolas', monospace; font-size: 8px; color: var(--text-dim); letter-spacing: 0.1em; margin-top: 4px; }
.zodiac-node.successor .zodiac-node-inner { border-color: var(--gold); }
.zodiac-card-display { max-width: 900px; margin: 40px auto 0; min-height: 200px; }
.zodiac-card { background: var(--bg-card); border: 1px solid var(--gold); padding: 8px; animation: fade-up 0.5s; }
.zodiac-card-inner { border: 1px solid var(--line); padding: 30px 40px; display: grid; grid-template-columns: auto 1fr; gap: 30px; align-items: center; }
.zodiac-card-zi { width: 100px; height: 100px; border: 2px solid var(--crimson-bright); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-family: 'Noto Serif SC', serif; font-size: 46px; color: var(--gold-bright); background: rgba(107, 26, 26, 0.15); flex-shrink: 0; }
.zodiac-card-name { font-family: 'Cinzel', serif; font-size: 11px; letter-spacing: 0.3em; color: var(--gold-dim); margin-bottom: 4px; }
.zodiac-card-name-cn { font-family: 'Noto Serif SC', serif; font-size: 26px; color: var(--gold-bright); font-weight: 600; margin-bottom: 6px; }
.zodiac-card-role { font-family: 'Cormorant Garamond', serif; font-style: italic; color: var(--text-dim); margin-bottom: 10px; }
.zodiac-card-desc { color: var(--parchment); font-size: 14px; line-height: 1.7; }
.zodiac-card-empty { text-align: center; color: var(--text-dim); font-style: italic; padding: 60px 20px; }
.members-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 40px; max-width: 1280px; margin: 0 auto; }
.member-card { background: var(--bg-card); border: 1px solid var(--line); padding: 0; position: relative; cursor: pointer; transition: all 0.5s; overflow: hidden; }
.member-card:hover { border-color: var(--gold); transform: translateY(-8px); box-shadow: 0 30px 60px rgba(0,0,0,0.5), 0 0 40px rgba(201, 169, 97, 0.15); }
.member-card-inner { position: relative; padding: 6px; }
.member-card-inner::before { content: ''; position: absolute; inset: 6px; border: 1px solid var(--line); pointer-events: none; z-index: 3; }
.member-image { aspect-ratio: 4/5; overflow: hidden; position: relative; background: var(--bg-card); display: flex; align-items: center; justify-content: center; }
.member-ph { font-family: 'Noto Serif SC', 'Songti SC', serif; font-size: 120px; color: rgba(201, 169, 97, 0.16); font-weight: 600; line-height: 1; }
.member-image::after { content: ''; position: absolute; inset: 0; background: linear-gradient(180deg, transparent 0%, transparent 35%, rgba(26, 20, 16, 0.4) 65%, rgba(26, 20, 16, 0.9) 85%, var(--bg-card) 100%); pointer-events: none; }
.member-rank-badge { position: absolute; top: 16px; right: 16px; background: rgba(10, 7, 5, 0.85); border: 1px solid var(--gold); padding: 6px 12px; font-family: 'Cinzel', serif; font-size: 10px; letter-spacing: 0.2em; color: var(--gold-bright); z-index: 4; backdrop-filter: blur(4px); }
.member-rank-badge .stars { color: var(--gold-bright); margin-right: 6px; letter-spacing: 0.05em; }
.member-info { padding: 24px 28px 32px; position: relative; z-index: 2; }
.member-name-en { font-family: 'Cinzel', serif; font-weight: 700; font-size: 14px; letter-spacing: 0.3em; color: var(--gold-dim); margin-bottom: 8px; text-transform: uppercase; }
.member-name-cn { font-family: 'Noto Serif SC', 'Songti SC', serif; font-weight: 600; font-size: 28px; color: var(--gold-bright); margin-bottom: 4px; letter-spacing: 0.05em; }
.member-title { font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 16px; color: var(--text-dim); margin-bottom: 20px; }
.member-meta { display: flex; gap: 16px; padding-top: 16px; border-top: 1px solid var(--line); flex-wrap: wrap; }
.meta-item { flex: 1; min-width: 80px; }
.meta-label { font-family: 'JetBrains Mono', monospace; font-size: 9px; letter-spacing: 0.25em; color: var(--text-dim); text-transform: uppercase; margin-bottom: 4px; }
.meta-value { font-family: 'Noto Serif SC', 'Songti SC', serif; font-size: 14px; color: var(--parchment); font-weight: 500; }
.nen-tag { display: inline-block; padding: 3px 8px; background: rgba(107, 26, 26, 0.25); border: 1px solid var(--crimson-bright); color: #d4a0a0; font-size: 12px; }

/* ===================== 模态详情 ===================== */
.modal-overlay { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.92); backdrop-filter: blur(8px); z-index: 200; display: flex; align-items: center; justify-content: center; padding: 40px 20px; overflow-y: auto; animation: fade-in 0.4s; }
@keyframes fade-in { from { opacity: 0; } to { opacity: 1; } }
.modal { max-width: 1000px; width: 100%; background: var(--bg-card); border: 1px solid var(--gold); padding: 8px; position: relative; max-height: 90vh; overflow-y: auto; animation: modal-up 0.5s; }
@keyframes modal-up { from { opacity: 0; transform: translateY(40px) scale(0.96); } to { opacity: 1; transform: translateY(0) scale(1); } }
.modal-inner { border: 1px solid var(--line); padding: 50px; position: relative; }
.modal-close { position: absolute; top: 20px; right: 20px; width: 40px; height: 40px; background: transparent; border: 1px solid var(--gold-dim); color: var(--gold); cursor: pointer; font-size: 20px; transition: all 0.3s; z-index: 5; }
.modal-close:hover { background: var(--crimson); border-color: var(--gold); transform: rotate(90deg); }
.modal-body { display: grid; grid-template-columns: 280px 1fr; gap: 40px; }
.modal-portrait { aspect-ratio: 3/4; background: var(--bg-card); border: 1px solid var(--line); overflow: hidden; position: relative; display: flex; align-items: center; justify-content: center; }
.modal-info h2 { font-family: 'Cinzel', serif; font-weight: 800; font-size: 18px; letter-spacing: 0.3em; color: var(--gold-dim); text-transform: uppercase; margin: 0 0 4px; }
.modal-info h1 { font-family: 'Noto Serif SC', 'Songti SC', serif; font-weight: 700; font-size: 48px; color: var(--gold-bright); margin: 0 0 8px; letter-spacing: 0.04em; }
.modal-info .role { font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 20px; color: var(--text-dim); margin-bottom: 24px; }
.modal-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 28px; padding: 20px 0; border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); }
.modal-stat-label { font-family: 'JetBrains Mono', monospace; font-size: 9px; letter-spacing: 0.25em; color: var(--text-dim); margin-bottom: 6px; }
.modal-stat-value { font-family: 'Cinzel', serif; font-size: 16px; color: var(--gold-bright); font-weight: 600; }
.modal-section-title { font-family: 'Cinzel', serif; font-size: 12px; letter-spacing: 0.3em; color: var(--gold); margin-bottom: 12px; text-transform: uppercase; display: flex; align-items: center; gap: 12px; }
.modal-section-title::after { content: ''; flex: 1; height: 1px; background: linear-gradient(90deg, var(--gold-dim), transparent); }
.modal-info p { color: var(--parchment); margin: 0 0 20px; line-height: 1.9; }
.modal-quote { margin-top: 30px; padding: 24px 30px; background: rgba(107, 26, 26, 0.1); border-left: 3px solid var(--crimson-bright); font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 22px; color: var(--gold-bright); line-height: 1.5; position: relative; }
.modal-quote::before { content: '"'; font-family: 'Cinzel', serif; font-size: 60px; position: absolute; top: -10px; left: 10px; color: var(--gold-dim); opacity: 0.4; }

/* ===================== 考试报名页 ===================== */
.exam-section { background: linear-gradient(180deg, var(--bg-dark) 0%, var(--bg-deep) 100%); padding: 140px 60px; position: relative; }
.exam-frame { max-width: 1100px; margin: 0 auto; background: var(--bg-card); border: 1px solid var(--gold); padding: 12px; position: relative; }
.exam-frame::before { content: ''; position: absolute; inset: 12px; border: 1px solid var(--line); pointer-events: none; }
.exam-inner { padding: 60px 70px; position: relative; }
.exam-watermark { position: absolute; top: 40px; right: 50px; font-family: 'Cinzel', serif; font-size: 11px; letter-spacing: 0.3em; color: var(--crimson-bright); border: 1px solid var(--crimson-bright); padding: 6px 14px; transform: rotate(-3deg); opacity: 0.7; }
.exam-title-block { text-align: center; margin-bottom: 50px; }
.exam-title-block .stamp { display: inline-block; font-family: 'JetBrains Mono', monospace; font-size: 10px; letter-spacing: 0.4em; color: var(--gold-dim); border-top: 1px solid var(--gold-dim); border-bottom: 1px solid var(--gold-dim); padding: 6px 20px; margin-bottom: 24px; }
.exam-warning { background: rgba(107, 26, 26, 0.15); border: 1px solid var(--crimson-bright); padding: 24px 30px; margin-bottom: 40px; position: relative; }
.exam-warning-title { font-family: 'Cinzel', serif; font-size: 14px; letter-spacing: 0.25em; color: #e88a8a; margin-bottom: 12px; text-transform: uppercase; display: flex; align-items: center; gap: 10px; }
.exam-warning p { font-family: 'Noto Serif SC', 'Songti SC', serif; color: var(--parchment); font-size: 14px; line-height: 1.8; margin: 0; }
.exam-warning strong { color: #ff9090; }
.exam-stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0; margin-bottom: 50px; border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); }
.exam-stat { text-align: center; padding: 24px 16px; border-right: 1px solid var(--line); }
.exam-stat:last-child { border-right: none; }
.exam-stat-num { font-family: 'Cinzel', serif; font-size: 36px; font-weight: 700; color: var(--gold-bright); line-height: 1; }
.exam-stat-label { font-family: 'Noto Serif SC', 'Songti SC', serif; font-size: 12px; color: var(--text-dim); letter-spacing: 0.2em; margin-top: 8px; }
form { display: grid; grid-template-columns: 1fr 1fr; gap: 28px 30px; }
.form-group { display: flex; flex-direction: column; }
.form-group.full { grid-column: 1 / -1; }
.form-group label { font-family: 'Cinzel', serif; font-size: 11px; letter-spacing: 0.25em; color: var(--gold); margin-bottom: 8px; text-transform: uppercase; display: flex; align-items: center; gap: 8px; }
.form-group label .label-cn { font-family: 'Noto Serif SC', 'Songti SC', serif; font-size: 13px; color: var(--text-dim); letter-spacing: 0.1em; text-transform: none; }
.form-group label .req { color: var(--crimson-bright); font-size: 14px; }
.form-group input, .form-group select, .form-group textarea { background: rgba(10, 7, 5, 0.6); border: 1px solid var(--line); border-bottom: 1px solid var(--gold-dim); color: var(--parchment); padding: 14px 16px; font-family: 'Cormorant Garamond', 'Noto Serif SC', serif; font-size: 16px; transition: all 0.3s; outline: none; }
.form-group input:focus, .form-group select:focus, .form-group textarea:focus { border-color: var(--gold); background: rgba(20, 16, 10, 0.8); box-shadow: 0 0 20px rgba(201, 169, 97, 0.15); }
.form-group textarea { resize: vertical; min-height: 100px; font-family: 'Noto Serif SC', serif; }
.form-group select { cursor: pointer; appearance: none; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M2 4l4 4 4-4' stroke='%23c9a961' stroke-width='1.5' fill='none'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 16px center; padding-right: 40px; }
.form-checkbox { grid-column: 1 / -1; display: flex; align-items: flex-start; gap: 12px; padding: 16px 20px; background: rgba(107, 26, 26, 0.1); border: 1px solid var(--line); cursor: pointer; user-select: none; }
.form-checkbox input { display: none; }
.form-checkbox .check-box { width: 20px; height: 20px; border: 1px solid var(--gold); flex-shrink: 0; margin-top: 2px; position: relative; transition: all 0.2s; }
.form-checkbox input:checked + .check-box { background: var(--gold); }
.form-checkbox input:checked + .check-box::after { content: '✓'; position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; color: var(--bg-deep); font-weight: 700; font-size: 14px; }
.form-checkbox span { font-family: 'Noto Serif SC', 'Songti SC', serif; font-size: 13px; color: var(--parchment); line-height: 1.7; }
.form-submit-row { grid-column: 1 / -1; text-align: center; margin-top: 20px; }
.btn-submit { padding: 18px 60px; background: linear-gradient(180deg, var(--crimson-bright) 0%, var(--crimson) 100%); color: var(--gold-bright); border: 1px solid var(--gold); font-family: 'Cinzel', serif; font-size: 13px; font-weight: 700; letter-spacing: 0.4em; text-transform: uppercase; cursor: pointer; transition: all 0.4s; position: relative; overflow: hidden; }
.btn-submit:hover { box-shadow: 0 0 40px rgba(160, 40, 40, 0.5), inset 0 0 30px rgba(201, 169, 97, 0.1); transform: translateY(-2px); }

/* ===================== 提交成功 ===================== */
.success-overlay { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.95); backdrop-filter: blur(10px); z-index: 300; display: flex; align-items: center; justify-content: center; padding: 40px 20px; animation: fade-in 0.5s; }
.success-card { max-width: 540px; background: var(--bg-card); border: 1px solid var(--gold); padding: 12px; text-align: center; animation: modal-up 0.6s; }
.success-card-inner { border: 1px solid var(--line); padding: 50px 40px; position: relative; }
.success-seal { width: 100px; height: 100px; margin: 0 auto 24px; border-radius: 50%; border: 2px solid var(--crimson-bright); display: flex; align-items: center; justify-content: center; color: var(--crimson-bright); font-family: 'Cinzel', serif; font-size: 11px; letter-spacing: 0.2em; transform: rotate(-8deg); position: relative; }
.success-seal::before { content: ''; position: absolute; inset: 6px; border: 1px solid var(--crimson-bright); border-radius: 50%; }
.success-seal span { line-height: 1.3; text-align: center; }
.success-stamp {
  display: inline-block;
  margin: 0 auto 18px;
  padding: 7px 24px 7px 29px;
  font-family: 'Noto Serif SC', 'Songti SC', serif;
  font-weight: 700;
  font-size: 20px;
  letter-spacing: 0.25em;
  color: var(--crimson-bright);
  border: 2px solid var(--crimson-bright);
  border-radius: 4px;
  transform: rotate(-4deg);
  box-shadow: 0 0 18px rgba(160, 40, 40, 0.25);
  text-shadow: 0 0 12px rgba(160, 40, 40, 0.35);
}
.success-title { font-family: 'Cinzel', serif; font-size: 28px; color: var(--gold-bright); letter-spacing: 0.1em; margin-bottom: 8px; }
.success-title-cn { font-family: 'Noto Serif SC', 'Songti SC', serif; font-size: 18px; color: var(--parchment); letter-spacing: 0.3em; margin-bottom: 24px; }
.success-text { font-family: 'Noto Serif SC', 'Songti SC', serif; color: var(--text-dim); font-size: 14px; line-height: 1.9; margin-bottom: 30px; }
.success-code { font-family: 'JetBrains Mono', monospace; font-size: 14px; color: var(--gold); letter-spacing: 0.2em; padding: 12px 20px; background: rgba(10, 7, 5, 0.6); border: 1px dashed var(--gold-dim); margin-bottom: 30px; }
.success-hint { font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: 0.15em; color: var(--gold-dim); margin: 0 auto 30px; max-width: 340px; }
.key-input { width: 100%; box-sizing: border-box; background: rgba(10, 7, 5, 0.6); border: 1px solid var(--line); border-bottom: 1px solid var(--gold-dim); color: var(--parchment); padding: 14px 16px; font-family: 'JetBrains Mono', monospace; font-size: 16px; letter-spacing: 0.15em; text-align: center; margin-bottom: 4px; outline: none; transition: all 0.3s; }
.key-input:focus { border-color: var(--gold); box-shadow: 0 0 20px rgba(201, 169, 97, 0.15); }
.key-input::placeholder { color: var(--gold-dim); font-size: 13px; letter-spacing: 0.1em; }
.key-error { color: #ff9090; font-family: 'Noto Serif SC', serif; font-size: 13px; margin: 6px 0 20px; min-height: 18px; text-align: center; }
.key-actions { display: flex; gap: 16px; justify-content: center; }
.key-actions .btn { padding: 12px 28px; font-size: 11px; }
.select-field {
  margin-bottom: 16px;
  text-align: left;
}
.select-field label {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-family: 'Cinzel', serif;
  font-size: 11px;
  letter-spacing: 0.25em;
  color: var(--gold);
  margin-bottom: 8px;
  text-transform: uppercase;
}
.select-field label span {
  font-family: 'JetBrains Mono', 'Consolas', monospace;
  font-size: 8px;
  letter-spacing: 0.15em;
  color: var(--text-dim);
}
.select-field select {
  width: 100%;
  box-sizing: border-box;
  background: rgba(10, 7, 5, 0.6);
  border: 1px solid var(--line);
  border-bottom: 1px solid var(--gold-dim);
  color: var(--parchment);
  padding: 13px 44px 13px 16px;
  font-family: 'Cormorant Garamond', 'Noto Serif SC', serif;
  font-size: 15px;
  cursor: pointer;
  outline: none;
  transition: all 0.3s;
  appearance: none;
  -webkit-appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M2 4l4 4 4-4' stroke='%23c9a961' stroke-width='1.5' fill='none'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 16px center;
}
.select-field select:focus {
  border-color: var(--gold);
  background-color: rgba(20, 16, 10, 0.8);
  box-shadow: 0 0 20px rgba(201, 169, 97, 0.15);
}
.select-field select option {
  background: #1a1410;
  color: var(--parchment);
}

/* ===================== 通缉令 ===================== */
.wanted-section { background: linear-gradient(180deg, var(--bg-dark) 0%, #0d0808 100%); padding: 140px 60px; position: relative; }
.wanted-section::before { content: ''; position: absolute; inset: 0; background-image: radial-gradient(circle at 30% 20%, rgba(107, 26, 26, 0.08) 0%, transparent 40%), radial-gradient(circle at 70% 80%, rgba(107, 26, 26, 0.06) 0%, transparent 40%); pointer-events: none; }
.wanted-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; max-width: 1280px; margin: 0 auto; }
.wanted-poster { background: linear-gradient(135deg, rgba(217, 195, 145, 0.04), transparent), #1a1410; border: 1px solid var(--line); padding: 10px; position: relative; transition: all 0.4s; cursor: default; }
.wanted-poster::before { content: ''; position: absolute; inset: 10px; border: 1px solid var(--gold-dim); pointer-events: none; }
.wanted-poster:hover { transform: translateY(-6px) rotate(-0.5deg); border-color: var(--crimson-bright); box-shadow: 0 20px 40px rgba(0,0,0,0.5); }
.wanted-inner { padding: 24px 22px 22px; position: relative; z-index: 1; }
.wanted-stamp { font-family: 'Cinzel', serif; font-size: 22px; font-weight: 900; letter-spacing: 0.2em; color: #d97070; text-align: center; border-top: 2px solid #d97070; border-bottom: 2px solid #d97070; padding: 8px 0; margin-bottom: 4px; }
.wanted-sub { font-family: 'Noto Serif SC', 'Songti SC', serif; font-size: 12px; letter-spacing: 0.4em; color: #d97070; text-align: center; margin-bottom: 18px; }
.wanted-portrait { aspect-ratio: 4/5; background: repeating-linear-gradient(45deg, #2a1a1a 0px, #2a1a1a 2px, #1a1010 2px, #1a1010 4px), #1a1410; border: 1px solid var(--line); display: flex; align-items: center; justify-content: center; color: var(--gold-dim); margin-bottom: 18px; position: relative; overflow: hidden; }
.wanted-portrait .silhouette { font-family: 'Noto Serif SC', 'Songti SC', serif; font-size: 60px; color: var(--crimson-bright); opacity: 0.6; line-height: 1; }
.wanted-portrait::after { content: 'CLASSIFIED'; position: absolute; top: 50%; left: 0; right: 0; transform: translateY(-50%) rotate(-15deg); text-align: center; font-family: 'Cinzel', serif; font-size: 28px; letter-spacing: 0.2em; color: var(--crimson-bright); opacity: 0.4; border-top: 3px solid var(--crimson-bright); border-bottom: 3px solid var(--crimson-bright); padding: 4px 0; }
.wanted-name { font-family: 'Noto Serif SC', 'Songti SC', serif; font-size: 24px; font-weight: 700; color: var(--gold-bright); text-align: center; margin-bottom: 4px; }
.wanted-alias { font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 14px; color: var(--text-dim); text-align: center; margin-bottom: 18px; }
.wanted-bounty { background: rgba(107, 26, 26, 0.25); border: 1px solid var(--crimson-bright); padding: 12px; text-align: center; margin-bottom: 16px; }
.wanted-bounty-label { font-family: 'JetBrains Mono', monospace; font-size: 9px; letter-spacing: 0.3em; color: #ff9090; margin-bottom: 4px; }
.wanted-bounty-amount { font-family: 'Cinzel', serif; font-weight: 800; font-size: 24px; color: var(--gold-bright); letter-spacing: 0.05em; }
.wanted-info { border-top: 1px solid var(--line); padding-top: 12px; font-family: 'Noto Serif SC', 'Songti SC', serif; font-size: 12px; color: var(--parchment); line-height: 1.7; }
.wanted-info .row { display: flex; justify-content: space-between; margin-bottom: 6px; }
.wanted-info .row .l { color: var(--text-dim); font-family: 'JetBrains Mono', monospace; font-size: 9px; letter-spacing: 0.2em; }
.wanted-info .row .r { color: var(--parchment); text-align: right; }
.wanted-danger { margin-top: 10px; padding: 8px 12px; background: rgba(196, 30, 30, 0.15); border-left: 3px solid var(--crimson-bright); font-size: 11px; color: #ffb0b0; font-style: italic; line-height: 1.6; }
.threat-A { color: #ff5050; }
.threat-S { color: #ff2020; text-shadow: 0 0 8px rgba(255, 0, 0, 0.5); }
.threat-EX { color: #ffd700; text-shadow: 0 0 12px gold; }

/* ===================== 水见式测试 ===================== */
.test-section { background: radial-gradient(ellipse at center, rgba(90, 166, 196, 0.05) 0%, transparent 60%), var(--bg-deep); padding: 140px 60px; }
.test-container { max-width: 760px; margin: 0 auto; background: var(--bg-card); border: 1px solid var(--gold); padding: 12px; }
.test-stage { border: 1px solid var(--line); padding: 50px 40px; min-height: 480px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; animation: fade-up 0.5s; }
.cup-container { margin-bottom: 30px; }
.cup-svg { width: 160px; height: auto; filter: drop-shadow(0 8px 16px rgba(201, 169, 97, 0.2)); animation: float 4s ease-in-out infinite; }
.test-intro-text { max-width: 460px; color: var(--parchment); line-height: 1.8; }
.test-progress { width: 100%; margin-bottom: 30px; }
.test-progress span { display: block; font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: 0.3em; color: var(--gold); margin-bottom: 8px; }
.test-progress-bar { width: 100%; height: 2px; background: rgba(201, 169, 97, 0.15); }
.test-progress-bar > div { height: 100%; background: linear-gradient(90deg, var(--crimson), var(--gold)); transition: width 0.5s; box-shadow: 0 0 8px var(--gold); }
.test-question-text { font-family: 'Noto Serif SC', 'Songti SC', serif; font-size: 22px; color: var(--gold-bright); margin-bottom: 30px; line-height: 1.5; max-width: 580px; }
.test-options { display: flex; flex-direction: column; gap: 12px; width: 100%; max-width: 540px; }
.test-option { background: rgba(20, 16, 10, 0.6); border: 1px solid var(--line); color: var(--parchment); padding: 16px 24px; font-family: 'Noto Serif SC', 'Songti SC', serif; font-size: 15px; cursor: pointer; transition: all 0.3s; text-align: left; line-height: 1.5; position: relative; }
.test-option::before { content: '◇'; color: var(--gold-dim); margin-right: 12px; transition: color 0.3s; }
.test-option:hover { background: rgba(107, 26, 26, 0.15); border-color: var(--gold); color: var(--gold-bright); transform: translateX(6px); }
.test-option:hover::before { color: var(--gold-bright); content: '◆'; }
.result-emblem { font-size: 80px; margin-bottom: 16px; filter: drop-shadow(0 0 20px currentColor); }
.result-eyebrow { font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: 0.4em; color: var(--gold-dim); margin-bottom: 12px; }
.result-title { font-family: 'Noto Serif SC', 'Songti SC', serif; font-weight: 700; font-size: 48px; color: var(--gold-bright); margin: 0 0 4px; letter-spacing: 0.1em; }
.result-en { font-family: 'Cinzel', serif; font-size: 14px; letter-spacing: 0.4em; color: var(--text-dim); margin-bottom: 30px; }
.result-desc { max-width: 540px; color: var(--parchment); line-height: 1.9; margin-bottom: 30px; font-size: 16px; }
.result-traits { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-bottom: 30px; }
.trait-tag { padding: 6px 16px; border: 1px solid var(--gold-dim); color: var(--gold); font-family: 'Noto Serif SC', 'Songti SC', serif; font-size: 13px; letter-spacing: 0.1em; }
.result-actions { display: flex; gap: 16px; margin-top: 28px; }

/* —— 占卜结果 3D 翻牌 —— */
.flip-scene { perspective: 1200px; width: 100%; max-width: 420px; margin: 0 auto; }
.flip-card {
  position: relative;
  width: 100%;
  min-height: 480px;
  transform-style: preserve-3d;
  animation: flip-reveal 2.6s cubic-bezier(0.3, 0, 0.2, 1) forwards;
}
.flip-face {
  position: absolute;
  inset: 0;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px 28px;
  box-sizing: border-box;
  background: linear-gradient(160deg, #1a1410, #0f0b08);
  border: 1px solid var(--gold);
  box-shadow: 0 0 40px rgba(201, 169, 97, 0.2);
}
.flip-face::before {
  content: '';
  position: absolute;
  inset: 8px;
  border: 1px solid var(--line);
  pointer-events: none;
}
.flip-back {
  background: radial-gradient(circle at center, rgba(201, 169, 97, 0.14) 0%, transparent 62%), linear-gradient(160deg, #1a1410, #0f0b08);
}
.flip-back-symbol { font-size: 64px; color: var(--gold-bright); margin-bottom: 16px; text-shadow: 0 0 20px rgba(232, 200, 120, 0.6); }
.flip-back-title { font-family: 'Noto Serif SC', 'Songti SC', serif; font-size: 32px; letter-spacing: 0.3em; color: var(--gold-bright); margin-bottom: 8px; }
.flip-back-sub { font-family: 'Cinzel', serif; font-size: 12px; letter-spacing: 0.4em; color: var(--gold-dim); }
.flip-front { transform: rotateY(180deg); }
.flip-front .result-emblem { font-size: 56px; margin-bottom: 12px; }
.flip-front .result-title { font-size: 32px; }
.flip-front .result-en { margin-bottom: 20px; }
.flip-front .result-desc { font-size: 14px; margin-bottom: 20px; }
.flip-front .result-traits { margin-bottom: 20px; }

@keyframes flip-reveal {
  0% { transform: rotateY(0deg); }
  100% { transform: rotateY(1260deg); }
}

/* ===================== 念之六系 ===================== */
.nen-card { background: var(--bg-card); border: 1px solid var(--line); padding: 30px 24px; text-align: center; position: relative; transition: all 0.4s; cursor: default; }
.nen-card:hover { border-color: var(--gold); transform: translateY(-4px); box-shadow: 0 20px 40px rgba(0,0,0,0.4); }
.nen-symbol { font-size: 36px; margin-bottom: 16px; color: var(--gold); }
.nen-name-cn { font-family: 'Noto Serif SC', 'Songti SC', serif; font-size: 22px; font-weight: 600; color: var(--gold-bright); margin-bottom: 4px; }
.nen-name-en { font-family: 'Cinzel', serif; font-size: 11px; letter-spacing: 0.25em; color: var(--text-dim); margin-bottom: 16px; }
.nen-desc { font-family: 'Noto Serif SC', 'Songti SC', serif; font-size: 13px; color: var(--parchment); line-height: 1.8; }

/* ===================== 页脚 ===================== */
footer { background: #050403; padding: 60px 60px 30px; border-top: 1px solid var(--line); position: relative; z-index: 2; }
.footer-grid { max-width: 1280px; margin: 0 auto; display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 60px; margin-bottom: 50px; }
.footer-brand p { color: var(--text-dim); font-size: 14px; line-height: 1.8; }
.footer-col h4 { font-family: 'Cinzel', serif; font-size: 11px; letter-spacing: 0.3em; color: var(--gold); margin: 0 0 20px; text-transform: uppercase; }
.footer-col ul { list-style: none; margin: 0; padding: 0; }
.footer-col li { margin-bottom: 10px; }
.footer-col a { color: var(--text-dim); text-decoration: none; font-size: 14px; transition: color 0.3s; }
.footer-col a:hover { color: var(--gold-bright); }
.footer-bottom { max-width: 1280px; margin: 0 auto; padding-top: 30px; border-top: 1px solid var(--line); display: flex; justify-content: space-between; color: var(--text-dim); font-size: 12px; font-family: 'JetBrains Mono', monospace; letter-spacing: 0.15em; }

/* ===================== 响应式 ===================== */
@media (max-width: 968px) {
  .nav { padding: 12px 20px; }
  .nav-links { display: none; }
  .nav-links.open { display: flex; position: absolute; top: 100%; left: 0; right: 0; flex-direction: column; background: rgba(10, 7, 5, 0.98); padding: 20px; border-bottom: 1px solid var(--gold); gap: 18px; }
  .nav-mobile-toggle { display: block; }
  section { padding: 100px 24px 60px; }
  .intro-section, .members-section, .exam-section { padding: 100px 24px; }
  .hero-title { font-size: 56px; }
  .hero-emblem { width: 220px; height: 170px; }
  .hero-subtitle-cn { font-size: 18px; letter-spacing: 0.3em; }
  .hero-motto { font-size: 18px; }
  .hero-motto::before, .hero-motto::after { width: 30px; margin: 0 10px; }
  #home::before { width: 600px; height: 600px; }
  #home::after { width: 400px; height: 400px; }
  .intro-grid { grid-template-columns: 1fr; gap: 50px; }
  .section-title { font-size: 36px; }
  .members-grid { grid-template-columns: 1fr; gap: 30px; }
  .members-header { margin-bottom: 50px; }
  .exam-inner { padding: 40px 24px; }
  .exam-watermark { display: none; }
  form { grid-template-columns: 1fr; }
  .exam-stats-row { grid-template-columns: 1fr 1fr; }
  .exam-stat:nth-child(2) { border-right: none; }
  .exam-stat:nth-child(1), .exam-stat:nth-child(2) { border-bottom: 1px solid var(--line); }
  .modal-inner { padding: 30px 24px; }
  .modal-body { grid-template-columns: 1fr; gap: 24px; }
  .modal-portrait { max-width: 280px; margin: 0 auto; }
  .modal-info h1 { font-size: 36px; }
  .footer-grid { grid-template-columns: 1fr; gap: 40px; }
  .footer-bottom { flex-direction: column; gap: 12px; text-align: center; }
  .ticker-item { padding: 0 30px; font-size: 12px; }
  .announcement-bar-label { font-size: 9px; padding: 14px 14px; }
  .ticker { padding-left: 120px; }
  .test-section { padding: 100px 24px; }
  .test-stage { padding: 30px 24px; }
  .test-question-text { font-size: 18px; }
  .result-title { font-size: 36px; }
  .zodiac-compass { width: 95vw; }
  .zodiac-node { width: 56px; height: 56px; }
  .zodiac-node-zi { font-size: 16px; }
  .zodiac-card-inner { grid-template-columns: 1fr; text-align: center; padding: 24px; }
  .zodiac-card-zi { margin: 0 auto; }
}
@media (max-width: 600px) {
  .members-grid { grid-template-columns: 1fr; }
  .intro-stats { grid-template-columns: 1fr; }
  section { padding: 80px 16px 50px; }
  .hero-emblem { width: 150px; height: 116px; }
  .hero-title { font-size: clamp(30px, 9vw, 40px); letter-spacing: 0.05em; }
  .hero-subtitle-cn { font-size: 15px; letter-spacing: 0.25em; }
  .hero-motto { font-size: 15px; }
  .hero-motto::before, .hero-motto::after { display: none; }
  .countdown-grid { gap: 8px; }
  .countdown-cell { padding: 10px 4px; }
  .countdown-cell span { font-size: clamp(22px, 7vw, 30px); }
  .countdown-cell em { font-size: 8px; letter-spacing: 0.1em; }
  .countdown-label { font-size: 9px; letter-spacing: 0.25em; }
  footer { padding: 40px 20px 24px; }
  .wanted-grid { grid-template-columns: 1fr; }
  .test-option { padding: 14px 16px; font-size: 14px; }
  .test-question-text { font-size: 16px; }
  .result-title { font-size: 30px; }
  .result-emblem { font-size: 60px; }
  .exam-inner { padding: 30px 16px; }
  .nav { padding: 10px 12px; }
  .nav-brand span { font-size: 10px; letter-spacing: 0.1em; }
  .nav-back { padding: 6px 10px; font-size: 10px; }
}
</style>
