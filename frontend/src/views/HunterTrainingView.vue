<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useHunterStore } from '../stores/hunter.js'

const router = useRouter()
const hunter = useHunterStore()

// ============ 专精方向 → 主题 ============
const themes = {
  bounty: {
    cn: '赏金猎人', en: 'BLACKLIST HUNTER',
    accent: '#e5484d', accent2: '#ff8a4d',
    bg: '#160a0a', icon: '⚔',
    tagline: '追缉 · 悬赏 · 战斗',
    shape: 'streak',
    palette: ['#e5484d', '#ff8a4d', '#ffc26e'],
  },
  gourmet: {
    cn: '美食猎人', en: 'GOURMET HUNTER',
    accent: '#f0a53c', accent2: '#f7d774',
    bg: '#1a1208', icon: '🍖',
    tagline: '寻味 · 香料 · 料理',
    shape: 'orb',
    palette: ['#f0a53c', '#f7d774', '#fff0c0'],
  },
  ruins: {
    cn: '遗迹猎人', en: 'RUINS HUNTER',
    accent: '#3fb6a8', accent2: '#c9a961',
    bg: '#0d1614', icon: '◈',
    tagline: '考古 · 符文 · 探索',
    shape: 'rune',
    palette: ['#3fb6a8', '#c9a961', '#8fe3d8'],
  },
  rare: {
    cn: '稀种猎人', en: 'RARE BEAST HUNTER',
    accent: '#b57edc', accent2: '#7aa2ff',
    bg: '#120e1c', icon: '✦',
    tagline: '追踪 · 荧光 · 幻兽',
    shape: 'glow',
    palette: ['#b57edc', '#7aa2ff', '#e0b0ff'],
  },
}
const defaultTheme = {
  cn: '猎人训练', en: 'HUNTER TRAINING',
  accent: '#c9a961', accent2: '#e8c878',
  bg: '#0a0705', icon: '◆',
  tagline: '秘密训练',
  shape: 'glow',
  palette: ['#c9a961', '#e8c878', '#fff0c0'],
}

function themeFor(code) {
  if (themes[code]) return themes[code]
  if (code === 'archaeologist' || code === 'sacred') return themes.ruins
  return defaultTheme
}

const theme = computed(() => themeFor(hunter.hunterClass))

const classNames = {
  bounty: '赏金猎人',
  gourmet: '美食猎人',
  ruins: '遗迹猎人',
  rare: '稀种猎人',
  archaeologist: '考古猎人',
  sacred: '圣物猎人',
  dark: '暗黑大陆探索',
  other: '其他',
}
const greetingClass = computed(() => classNames[hunter.hunterClass] || theme.value.cn || '猎人')

// ============ 主题粒子 + 鼠标跟随 ============
const canvas = ref(null)
let ctx = null
let particles = []
let rafId = null
let W = 0
let H = 0
let mouseX = -1
let mouseY = -1
let hasMouse = false
const leaving = ref(false)
let leaveTimer = null

function resize() {
  const cvs = canvas.value
  if (!cvs) return
  W = cvs.width = window.innerWidth
  H = cvs.height = window.innerHeight
}

function spawnOne() {
  const t = theme.value
  const color = t.palette[Math.floor(Math.random() * t.palette.length)]
  const angle = Math.random() * Math.PI * 2
  const speed = 0.3 + Math.random() * 0.8
  particles.push({
    x: Math.random() * W,
    y: Math.random() * H,
    vx: Math.cos(angle) * speed,
    vy: Math.sin(angle) * speed - 0.2,
    r: 1 + Math.random() * 2.2,
    life: 1,
    decay: 0.004 + Math.random() * 0.008,
    color,
    trail: false,
  })
}

function spawnTrail(x, y) {
  const t = theme.value
  const color = t.palette[Math.floor(Math.random() * t.palette.length)]
  particles.push({
    x, y,
    vx: (Math.random() - 0.5) * 0.9,
    vy: (Math.random() - 0.5) * 0.9,
    r: 0.8 + Math.random() * 1.8,
    life: 1,
    decay: 0.04 + Math.random() * 0.05,
    color,
    trail: true,
  })
}

function burst() {
  const t = theme.value
  const cx = W / 2
  const cy = H / 2
  const count = 200
  for (let i = 0; i < count; i++) {
    const angle = Math.random() * Math.PI * 2
    const speed = 2.5 + Math.random() * 9.5
    const color = t.palette[Math.floor(Math.random() * t.palette.length)]
    particles.push({
      x: cx, y: cy,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed,
      r: 1.5 + Math.random() * 3.5,
      life: 1,
      decay: 0.014 + Math.random() * 0.026,
      color,
      trail: false,
      shard: true,
      rot: Math.random() * Math.PI * 2,
      spin: (Math.random() - 0.5) * 0.5,
    })
  }
}

function onPointerMove(e) {
  if (leaving.value) return
  mouseX = e.clientX
  mouseY = e.clientY
  hasMouse = true
  spawnTrail(e.clientX, e.clientY)
}

function tick() {
  if (!ctx) return
  ctx.clearRect(0, 0, W, H)
  ctx.globalCompositeOperation = 'lighter'
  const shape = theme.value.shape
  let ambient = 0
  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i]
    if (!p.trail && !p.shard && hasMouse && !leaving.value) {
      const dx = mouseX - p.x
      const dy = mouseY - p.y
      const d = Math.hypot(dx, dy)
      if (d > 0 && d < 300) {
        const f = ((300 - d) / 300) * 0.09
        p.vx += (dx / d) * f
        p.vy += (dy / d) * f
      }
      p.vx *= 0.985
      p.vy *= 0.985
    }
    p.x += p.vx
    p.y += p.vy
    if (p.shard) p.rot += p.spin
    p.life -= p.decay
    if (p.life <= 0) {
      particles.splice(i, 1)
      continue
    }
    if (!p.trail && !p.shard) ambient++
    const a = Math.max(0, p.life)
    ctx.strokeStyle = p.color
    ctx.fillStyle = p.color
    if (p.trail) {
      ctx.globalAlpha = a * 0.3
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.r * 2.4, 0, Math.PI * 2)
      ctx.fill()
      ctx.globalAlpha = a
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
      ctx.fill()
    } else if (p.shard) {
      ctx.globalAlpha = a
      ctx.save()
      ctx.translate(p.x, p.y)
      ctx.rotate(p.rot)
      const s = p.r * 3
      ctx.beginPath()
      ctx.moveTo(0, -s)
      ctx.lineTo(s * 0.65, s * 0.55)
      ctx.lineTo(-s * 0.65, s * 0.55)
      ctx.closePath()
      ctx.fill()
      ctx.restore()
    } else if (shape === 'streak') {
      ctx.globalAlpha = a * 0.8
      ctx.lineWidth = p.r * 0.6
      ctx.beginPath()
      ctx.moveTo(p.x, p.y)
      ctx.lineTo(p.x - p.vx * 8, p.y - p.vy * 8)
      ctx.stroke()
    } else if (shape === 'rune') {
      const s = p.r * 2.2
      ctx.globalAlpha = a * 0.9
      ctx.save()
      ctx.translate(p.x, p.y)
      ctx.rotate(0.8)
      ctx.fillRect(-s / 2, -s / 2, s, s)
      ctx.restore()
    } else if (shape === 'glow') {
      ctx.globalAlpha = a * 0.25
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.r * 2.6, 0, Math.PI * 2)
      ctx.fill()
      ctx.globalAlpha = a
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
      ctx.fill()
    } else {
      ctx.globalAlpha = a * 0.85
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
      ctx.fill()
    }
  }
  ctx.globalAlpha = 1
  ctx.globalCompositeOperation = 'source-over'
  if (!leaving.value && ambient < 80) {
    for (let i = 0; i < 3; i++) spawnOne()
  }
  rafId = requestAnimationFrame(tick)
}

function initParticles() {
  resize()
  ctx = canvas.value.getContext('2d')
  particles = []
  for (let i = 0; i < 80; i++) spawnOne()
  window.addEventListener('resize', resize)
  window.addEventListener('pointermove', onPointerMove)
  rafId = requestAnimationFrame(tick)
}

function startTraining() {
  if (leaving.value) return
  leaving.value = true
  burst()
  leaveTimer = setTimeout(() => {
    router.push('/hunter/training/session')
  }, 720)
}

onMounted(() => {
  hunter.load()
  if (!hunter.trainingUnlocked) {
    router.replace('/hunter')
    return
  }
  initParticles()
})

onBeforeUnmount(() => {
  if (rafId) cancelAnimationFrame(rafId)
  if (leaveTimer) clearTimeout(leaveTimer)
  window.removeEventListener('resize', resize)
  window.removeEventListener('pointermove', onPointerMove)
})
</script>

<template>
  <div
    class="training-page"
    :class="{ leaving }"
    :style="{ '--accent': theme.accent, '--accent2': theme.accent2, '--tbg': theme.bg }"
  >
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

    <canvas ref="canvas" class="particles"></canvas>
    <div class="flash"></div>

    <nav class="nav">
      <div class="nav-brand">
        <svg style="color:var(--accent2)"><use href="#crest"/></svg>
        <span>HUNTER · TRAINING</span>
      </div>
      <div class="nav-actions">
        <button class="nav-back" @click="router.push('/hunter')">返回协会</button>
      </div>
    </nav>

    <main class="content">
      <div class="class-badge">{{ theme.icon }}</div>
      <div class="eyebrow">{{ theme.en }} · 专精方向</div>
      <h1 class="title">{{ theme.cn }}</h1>
      <div class="tagline">{{ theme.tagline }}</div>
      <div class="divider"></div>
      <p class="greeting">欢迎进入训练，<span class="name">{{ greetingClass }}</span>！</p>
      <button class="start-btn" @click="startTraining">开始训练 · BEGIN</button>
    </main>
  </div>
</template>

<style scoped>
.training-page {
  --accent: #c9a961;
  --accent2: #e8c878;
  --tbg: #0a0705;
  --gold-dim: #8a7140;
  --parchment: #d9c9a3;
  --text-dim: #8a7e6a;
  --line: rgba(201, 169, 97, 0.25);

  min-height: 100vh;
  background: var(--tbg);
  color: var(--parchment);
  font-family: 'Cormorant Garamond', 'Noto Serif SC', 'Songti SC', 'SimSun', serif;
  position: relative;
  overflow-x: hidden;
  transition: background 0.6s;
  background-image:
    radial-gradient(ellipse at 20% 10%, var(--accent) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 90%, var(--accent2) 0%, transparent 50%);
  background-blend-mode: screen;
}

.training-page::before {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 1;
  opacity: 0.06;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' /%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' /%3E%3C/svg%3E");
  mix-blend-mode: overlay;
}

.particles {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
}

.flash {
  position: fixed;
  inset: 0;
  z-index: 3;
  pointer-events: none;
  opacity: 0;
  background: radial-gradient(circle at 50% 50%, var(--accent2) 0%, var(--accent) 30%, transparent 70%);
  transition: opacity 0.15s;
}

.training-page.leaving .flash {
  opacity: 1;
  animation: flash-pulse 0.7s ease-out forwards;
}

@keyframes flash-pulse {
  0% { opacity: 0; transform: scale(0.6); }
  35% { opacity: 1; transform: scale(1.15); }
  100% { opacity: 1; transform: scale(1.6); }
}

.training-page.leaving .nav {
  opacity: 0;
  transform: translateY(-20px);
  filter: blur(8px);
}

.training-page.leaving .content {
  opacity: 0;
  transform: scale(1.06);
  filter: blur(10px);
}

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
  transition: opacity 0.5s, transform 0.5s, filter 0.5s;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  font-family: 'Cinzel', 'Times New Roman', serif;
  font-weight: 700;
  letter-spacing: 0.18em;
  font-size: 13px;
  color: var(--accent2);
}

.nav-brand svg { width: 36px; height: 28px; }

.nav-actions { display: flex; align-items: center; gap: 12px; }

.nav-back {
  background: none;
  border: 1px solid var(--gold-dim);
  color: var(--accent2);
  padding: 8px 16px;
  cursor: pointer;
  font-family: 'Cinzel', 'Noto Serif SC', serif;
  font-size: 12px;
  letter-spacing: 0.12em;
  transition: all 0.3s;
  white-space: nowrap;
}

.nav-back:hover {
  border-color: var(--accent2);
  color: var(--accent2);
  text-shadow: 0 0 12px var(--accent);
  box-shadow: 0 0 14px var(--accent);
}

.content {
  position: relative;
  z-index: 2;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 120px 24px 80px;
  transition: opacity 0.5s, transform 0.5s, filter 0.5s;
}

.class-badge {
  font-size: 84px;
  line-height: 1;
  color: var(--accent2);
  filter: drop-shadow(0 0 24px var(--accent));
  animation: float 5s ease-in-out infinite;
  margin-bottom: 20px;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-14px); }
}

.eyebrow {
  font-family: 'JetBrains Mono', 'Consolas', monospace;
  font-size: 11px;
  letter-spacing: 0.45em;
  color: var(--text-dim);
  text-transform: uppercase;
  margin-bottom: 18px;
}

.title {
  font-family: 'Cinzel', 'Times New Roman', serif;
  font-weight: 800;
  font-size: clamp(40px, 7vw, 72px);
  letter-spacing: 0.25em;
  color: var(--accent2);
  margin: 0 0 12px;
  text-shadow: 0 0 30px var(--accent);
}

.tagline {
  font-family: 'Noto Serif SC', 'Songti SC', serif;
  font-size: 16px;
  letter-spacing: 0.4em;
  color: var(--text-dim);
}

.divider {
  width: 220px;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--accent2), transparent);
  margin: 32px auto;
}

.greeting {
  font-family: 'Noto Serif SC', 'Songti SC', serif;
  font-size: 24px;
  color: var(--parchment);
  letter-spacing: 0.1em;
  margin: 0 0 40px;
}

.greeting .name {
  color: var(--accent2);
  font-weight: 700;
  text-shadow: 0 0 18px var(--accent);
}

.start-btn {
  padding: 18px 64px;
  background: linear-gradient(180deg, var(--accent) 0%, transparent 160%);
  color: var(--accent2);
  border: 1px solid var(--accent2);
  font-family: 'Cinzel', serif;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.35em;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.4s;
  position: relative;
  overflow: hidden;
}

.start-btn:hover {
  box-shadow: 0 0 42px var(--accent), inset 0 0 28px var(--accent);
  transform: translateY(-2px);
}

@media (max-width: 600px) {
  .nav { padding: 10px 12px; }
  .nav-brand span { font-size: 10px; letter-spacing: 0.1em; }
  .nav-back { padding: 6px 10px; font-size: 10px; }
  .class-badge { font-size: 60px; }
  .greeting { font-size: 20px; }
  .start-btn { padding: 14px 44px; font-size: 12px; }
}
</style>
