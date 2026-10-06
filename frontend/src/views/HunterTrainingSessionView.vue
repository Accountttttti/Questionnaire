<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useHunterStore } from '../stores/hunter.js'

const router = useRouter()
const hunter = useHunterStore()

// ============ 游戏状态 ============
const phase = ref('idle') // idle | playing | over
const canvas = ref(null)
const score = ref(0)
const timeLeft = ref(30)
const finalScore = ref(0)
const bestScore = ref(0)
const disguiseReady = ref(true)

const DURATION = 30

let ctx = null
let W = 0
let H = 0
let rafId = null
let last = 0

// 玩家
const player = { x: 0, y: 0, r: 9, hp: 5, maxHp: 5, invuln: 0 }

// 输入
const keys = {}
let mouseX = 0
let mouseY = 0
let mouseDown = false
let spaceDown = false
let fireCd = 0

// 触屏输入
let touchActive = false
let touchX = 0
let touchY = 0

// 实体
let enemies = []
let pBullets = []
let eBullets = []
let particles = []
let stars = []

let spawnT = 0

// 变化系：伪装成敌方
let disguiseT = 0
let disguiseUsed = false

// 赏金猎人主题配色
const PALETTE = ['#e5484d', '#ff8a4d', '#ffc26e', '#f0a53c']

function bestKey() {
  const u = localStorage.getItem('username') || 'anon'
  return `hunter_${u}_bounty_best`
}

function resize() {
  const c = canvas.value
  if (!c) return
  W = c.width = window.innerWidth
  H = c.height = window.innerHeight
}

function initStars() {
  stars = []
  for (let i = 0; i < 90; i++) {
    stars.push({
      x: Math.random() * W,
      y: Math.random() * H,
      r: Math.random() * 1.5 + 0.3,
      sp: Math.random() * 0.6 + 0.1,
    })
  }
}

function resetGame() {
  player.x = W / 2
  player.y = H - 120
  player.hp = player.maxHp
  player.invuln = 0
  disguiseT = 0
  disguiseUsed = false
  disguiseReady.value = true
  enemies = []
  pBullets = []
  eBullets = []
  particles = []
  score.value = 0
  timeLeft.value = DURATION
  fireCd = 0
  spawnT = 0.6
  Object.keys(keys).forEach((k) => delete keys[k])
  mouseDown = false
  spaceDown = false
  touchActive = false
}

function startGame() {
  resize()
  ctx = canvas.value.getContext('2d')
  resetGame()
  phase.value = 'playing'
  last = performance.now()
  rafId = requestAnimationFrame(loop)
}

function spawnEnemy() {
  const r = 12 + Math.random() * 10
  enemies.push({
    x: 30 + Math.random() * (W - 60),
    y: -r,
    r,
    vx: (Math.random() - 0.5) * 70,
    vy: 60 + Math.random() * 90,
    shootCd: 0.8 + Math.random() * 1.2,
    color: PALETTE[Math.floor(Math.random() * PALETTE.length)],
  })
}

function spawnEnemyBullet(e) {
  const dx = player.x - e.x
  const dy = player.y - e.y
  const d = Math.hypot(dx, dy) || 1
  const sp = 170 + Math.random() * 90
  eBullets.push({ x: e.x, y: e.y, vx: (dx / d) * sp, vy: (dy / d) * sp, r: 4 })
}

function spawnPlayerBullet() {
  const dx = mouseX - player.x
  const dy = mouseY - player.y
  const d = Math.hypot(dx, dy) || 1
  const sp = 640
  pBullets.push({ x: player.x, y: player.y, vx: (dx / d) * sp, vy: (dy / d) * sp, r: 4 })
}

function nearestEnemy() {
  let best = null
  let bd = Infinity
  for (const e of enemies) {
    const d = Math.hypot(e.x - player.x, e.y - player.y)
    if (d < bd) {
      bd = d
      best = e
    }
  }
  return best
}

function spawnAutoBullet() {
  const e = nearestEnemy()
  const sp = 640
  if (!e) {
    pBullets.push({ x: player.x, y: player.y, vx: 0, vy: -sp, r: 4 })
    return
  }
  const dx = e.x - player.x
  const dy = e.y - player.y
  const d = Math.hypot(dx, dy) || 1
  pBullets.push({ x: player.x, y: player.y, vx: (dx / d) * sp, vy: (dy / d) * sp, r: 4 })
}

function explode(x, y, color, n = 14) {
  for (let i = 0; i < n; i++) {
    const a = Math.random() * Math.PI * 2
    const sp = 60 + Math.random() * 220
    particles.push({
      x, y,
      vx: Math.cos(a) * sp,
      vy: Math.sin(a) * sp,
      r: 2 + Math.random() * 3,
      life: 1,
      decay: 0.03 + Math.random() * 0.04,
      color,
    })
  }
}

function isInvulnerable() {
  return player.invuln > 0 || disguiseT > 0
}

function useDisguise() {
  if (hunter.nenType !== 'transmutation' || disguiseUsed || disguiseT > 0) return
  disguiseUsed = true
  disguiseT = 5
  disguiseReady.value = false
}

function hurtPlayer() {
  player.hp--
  player.invuln = 1.2
  explode(player.x, player.y, '#e5484d', 20)
  if (player.hp <= 0) endGame()
}

function endGame() {
  finalScore.value = score.value
  if (score.value > bestScore.value) {
    bestScore.value = score.value
    localStorage.setItem(bestKey(), String(score.value))
  }
  phase.value = 'over'
}

function update(dt) {
  // 移动
  let mx = 0
  let my = 0
  if (keys['ArrowLeft'] || keys['KeyA']) mx -= 1
  if (keys['ArrowRight'] || keys['KeyD']) mx += 1
  if (keys['ArrowUp'] || keys['KeyW']) my -= 1
  if (keys['ArrowDown'] || keys['KeyS']) my += 1
  if (mx || my) {
    const l = Math.hypot(mx, my)
    const sp = 290
    player.x += (mx / l) * sp * dt
    player.y += (my / l) * sp * dt
  }
  // 触屏：飞船跟随手指（显示在手指上方 80px，避免被拇指挡住）
  if (touchActive) {
    const tx = touchX
    const ty = touchY - 80
    const dx = tx - player.x
    const dy = ty - player.y
    const d = Math.hypot(dx, dy)
    if (d > 2) {
      const step = Math.min(900 * dt, d)
      player.x += (dx / d) * step
      player.y += (dy / d) * step
    }
  }
  player.x = Math.max(player.r, Math.min(W - player.r, player.x))
  player.y = Math.max(player.r, Math.min(H - player.r, player.y))
  if (player.invuln > 0) player.invuln -= dt
  if (disguiseT > 0) disguiseT -= dt

  // 射击（触屏自动索敌；键鼠朝鼠标方向）
  fireCd -= dt
  const wantFire = touchActive || mouseDown || spaceDown
  if (wantFire && fireCd <= 0) {
    if (touchActive) spawnAutoBullet()
    else spawnPlayerBullet()
    fireCd = 0.16
  }

  // 生成敌人（随时间加快）
  spawnT -= dt
  if (spawnT <= 0) {
    spawnEnemy()
    const elapsed = DURATION - timeLeft.value
    spawnT = Math.max(0.35, 1.0 - elapsed * 0.02)
  }

  // 敌人
  for (let i = enemies.length - 1; i >= 0; i--) {
    const e = enemies[i]
    e.x += e.vx * dt
    e.y += e.vy * dt
    if (e.x < e.r || e.x > W - e.r) e.vx *= -1
    e.shootCd -= dt
    if (e.shootCd <= 0 && e.y > 0 && e.y < H - 60) {
      spawnEnemyBullet(e)
      e.shootCd = 1.1 + Math.random() * 1.3
    }
    if (e.y > H + e.r) {
      enemies.splice(i, 1)
      continue
    }
    if (!isInvulnerable() && Math.hypot(e.x - player.x, e.y - player.y) < e.r + player.r) {
      hurtPlayer()
      explode(e.x, e.y, '#ff8a4d')
      enemies.splice(i, 1)
    }
  }

  // 玩家子弹
  for (let i = pBullets.length - 1; i >= 0; i--) {
    const b = pBullets[i]
    b.x += b.vx * dt
    b.y += b.vy * dt
    if (b.y < -20 || b.y > H + 20 || b.x < -20 || b.x > W + 20) {
      pBullets.splice(i, 1)
      continue
    }
    let hit = false
    for (let j = enemies.length - 1; j >= 0; j--) {
      const e = enemies[j]
      if (Math.hypot(b.x - e.x, b.y - e.y) < b.r + e.r) {
        enemies.splice(j, 1)
        score.value += Math.round(e.r)
        explode(e.x, e.y, e.color)
        hit = true
        break
      }
    }
    if (hit) pBullets.splice(i, 1)
  }

  // 敌方子弹
  for (let i = eBullets.length - 1; i >= 0; i--) {
    const b = eBullets[i]
    b.x += b.vx * dt
    b.y += b.vy * dt
    if (b.x < -20 || b.x > W + 20 || b.y < -20 || b.y > H + 20) {
      eBullets.splice(i, 1)
      continue
    }
    if (!isInvulnerable() && Math.hypot(b.x - player.x, b.y - player.y) < b.r + player.r) {
      hurtPlayer()
      eBullets.splice(i, 1)
    }
  }

  // 粒子
  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i]
    p.x += p.vx * dt
    p.y += p.vy * dt
    p.vx *= 0.96
    p.vy *= 0.96
    p.life -= p.decay
    if (p.life <= 0) particles.splice(i, 1)
  }

  // 倒计时
  timeLeft.value = Math.max(0, timeLeft.value - dt)
  if (timeLeft.value <= 0) endGame()
}

function drawHUD() {
  ctx.textBaseline = 'top'
  ctx.textAlign = 'left'
  ctx.fillStyle = '#e8c878'
  ctx.font = '700 18px Cinzel, serif'
  ctx.fillText('赏金 BOUNTY  ¥ ' + score.value, 24, 100)

  ctx.textAlign = 'center'
  ctx.fillStyle = timeLeft.value <= 5 ? '#ff8a4d' : '#e8c878'
  ctx.font = '800 28px Cinzel, serif'
  ctx.fillText(String(Math.ceil(timeLeft.value)), W / 2, 94)

  ctx.textAlign = 'right'
  for (let i = 0; i < player.maxHp; i++) {
    const x = W - 24 - i * 26
    ctx.beginPath()
    ctx.arc(x, 108, 9, 0, Math.PI * 2)
    ctx.fillStyle = i < player.hp ? '#e5484d' : 'rgba(232, 200, 120, 0.15)'
    ctx.fill()
  }

  // 念系状态提示
  ctx.textAlign = 'center'
  if (disguiseT > 0) {
    ctx.fillStyle = '#ff8a4d'
    ctx.font = '700 16px Cinzel, serif'
    ctx.fillText('伪装中 DISGUISE · ' + disguiseT.toFixed(1) + 's', W / 2, 140)
  } else if (hunter.nenType === 'transmutation' && !disguiseUsed) {
    ctx.fillStyle = 'rgba(232, 200, 120, 0.7)'
    ctx.font = '700 13px Cinzel, serif'
    ctx.fillText('按 J 伪装成敌方（每局限 1 次）', W / 2, 140)
  }
  ctx.textAlign = 'left'
}

function draw() {
  ctx.clearRect(0, 0, W, H)
  ctx.fillStyle = '#0a0705'
  ctx.fillRect(0, 0, W, H)

  // 背景星空
  for (const s of stars) {
    s.y += s.sp
    if (s.y > H) {
      s.y = 0
      s.x = Math.random() * W
    }
    ctx.globalAlpha = 0.5
    ctx.fillStyle = '#8a7140'
    ctx.beginPath()
    ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2)
    ctx.fill()
  }
  ctx.globalAlpha = 1

  // 敌方子弹
  for (const b of eBullets) {
    ctx.fillStyle = '#ff8a4d'
    ctx.shadowColor = '#ff8a4d'
    ctx.shadowBlur = 8
    ctx.beginPath()
    ctx.arc(b.x, b.y, b.r, 0, Math.PI * 2)
    ctx.fill()
    ctx.shadowBlur = 0
  }

  // 玩家子弹
  for (const b of pBullets) {
    ctx.fillStyle = '#ffc26e'
    ctx.shadowColor = '#ffc26e'
    ctx.shadowBlur = 10
    ctx.beginPath()
    ctx.arc(b.x, b.y, b.r, 0, Math.PI * 2)
    ctx.fill()
    ctx.shadowBlur = 0
  }

  // 敌人（倒三角飞船）
  for (const e of enemies) {
    ctx.save()
    ctx.translate(e.x, e.y)
    ctx.fillStyle = e.color
    ctx.beginPath()
    ctx.moveTo(0, e.r)
    ctx.lineTo(e.r * 0.9, -e.r * 0.7)
    ctx.lineTo(-e.r * 0.9, -e.r * 0.7)
    ctx.closePath()
    ctx.fill()
    ctx.restore()
  }

  // 粒子
  for (const p of particles) {
    ctx.globalAlpha = Math.max(0, p.life)
    ctx.fillStyle = p.color
    ctx.beginPath()
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
    ctx.fill()
  }
  ctx.globalAlpha = 1

  // 玩家（金色菱形，受击闪烁；伪装时变敌方橙红 + 虚线环）
  const disguiseActive = disguiseT > 0
  const blink = !disguiseActive && player.invuln > 0 && Math.floor(player.invuln * 10) % 2 === 0
  if (!blink) {
    ctx.save()
    ctx.translate(player.x, player.y)
    const pColor = disguiseActive ? '#ff8a4d' : '#e8c878'
    ctx.fillStyle = pColor
    ctx.shadowColor = pColor
    ctx.shadowBlur = 16
    ctx.beginPath()
    ctx.moveTo(0, -player.r * 1.3)
    ctx.lineTo(player.r * 0.95, player.r)
    ctx.lineTo(0, player.r * 0.5)
    ctx.lineTo(-player.r * 0.95, player.r)
    ctx.closePath()
    ctx.fill()
    ctx.shadowBlur = 0
    if (disguiseActive) {
      ctx.strokeStyle = '#ffc26e'
      ctx.lineWidth = 2
      ctx.setLineDash([5, 4])
      ctx.stroke()
      ctx.setLineDash([])
    }
    ctx.restore()
  }

  drawHUD()
}

function loop(now) {
  if (phase.value !== 'playing') return
  const dt = Math.min(0.05, (now - last) / 1000)
  last = now
  update(dt)
  draw()
  rafId = requestAnimationFrame(loop)
}

// ============ 输入监听 ============
function onKeyDown(e) {
  if (phase.value !== 'playing') return
  keys[e.code] = true
  if (e.code === 'Space') {
    spaceDown = true
    e.preventDefault()
  }
  if (e.code.startsWith('Arrow')) e.preventDefault()
  if (e.code === 'KeyJ') useDisguise()
}
function onKeyUp(e) {
  keys[e.code] = false
  if (e.code === 'Space') spaceDown = false
}
function onMouseMove(e) {
  mouseX = e.clientX
  mouseY = e.clientY
}
function onMouseDown(e) {
  if (phase.value === 'playing' && e.button === 0) mouseDown = true
}
function onMouseUp(e) {
  if (e.button === 0) mouseDown = false
}
function onTouchStart(e) {
  if (phase.value !== 'playing') return
  e.preventDefault()
  const t = e.touches[0]
  if (!t) return
  touchActive = true
  touchX = t.clientX
  touchY = t.clientY
}
function onTouchMove(e) {
  if (!touchActive) return
  e.preventDefault()
  const t = e.touches[0]
  if (!t) return
  touchX = t.clientX
  touchY = t.clientY
}
function onTouchEnd() {
  touchActive = false
}

onMounted(() => {
  hunter.load()
  if (!hunter.trainingUnlocked) {
    router.replace('/hunter')
    return
  }
  bestScore.value = Number(localStorage.getItem(bestKey()) || 0)
  player.maxHp = hunter.nenType === 'enhancement' ? 6 : 5
  resize()
  initStars()
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('keyup', onKeyUp)
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mousedown', onMouseDown)
  window.addEventListener('mouseup', onMouseUp)
  window.addEventListener('resize', resize)
  const c = canvas.value
  if (c) {
    c.addEventListener('touchstart', onTouchStart, { passive: false })
    c.addEventListener('touchmove', onTouchMove, { passive: false })
    c.addEventListener('touchend', onTouchEnd)
    c.addEventListener('touchcancel', onTouchEnd)
  }
})

onBeforeUnmount(() => {
  if (rafId) cancelAnimationFrame(rafId)
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('keyup', onKeyUp)
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mousedown', onMouseDown)
  window.removeEventListener('mouseup', onMouseUp)
  window.removeEventListener('resize', resize)
  const c = canvas.value
  if (c) {
    c.removeEventListener('touchstart', onTouchStart)
    c.removeEventListener('touchmove', onTouchMove)
    c.removeEventListener('touchend', onTouchEnd)
    c.removeEventListener('touchcancel', onTouchEnd)
  }
})
</script>

<template>
  <div class="session-page">
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

    <canvas ref="canvas" class="game-canvas"></canvas>

    <button
      v-if="phase === 'playing' && hunter.nenType === 'transmutation' && disguiseReady"
      class="disguise-btn"
      @click="useDisguise"
    >
      <span class="disguise-key">J</span> 伪装
    </button>

    <nav class="nav">
      <div class="nav-brand">
        <svg style="color:var(--gold)"><use href="#crest"/></svg>
        <span>HUNTER · TRAINING · BOUNTY</span>
      </div>
      <div class="nav-actions">
        <button class="nav-back" @click="router.push('/hunter/training')">返回训练</button>
      </div>
    </nav>

    <!-- 开始界面 -->
    <div v-if="phase === 'idle'" class="panel-overlay">
      <div class="panel">
        <div class="panel-emblem">⚔</div>
        <div class="panel-eyebrow">BLACKLIST HUNTER · TRAINING</div>
        <h1 class="panel-title">赏金猎人 · 弹幕训练</h1>
        <div class="panel-divider"></div>
        <div class="controls">
          <div class="controls-title">操作说明 · CONTROLS</div>
          <div class="control-row"><span class="key">W A S D</span> / <span class="key">方向键</span> 移动</div>
          <div class="control-row"><span class="key">鼠标左键</span> / <span class="key">空格</span> 射击（朝鼠标方向）</div>
          <div class="control-row"><span class="key">手指拖动</span> 移动并自动射击（手机）</div>
          <div class="control-row">在 <span class="key">30 秒</span> 内击落敌人赚取赏金，躲避红色弹幕</div>
          <div class="control-row dim">被弹幕或敌人撞到会损失生命，生命归零则提前结束</div>
        </div>
        <div class="buff-box">
          <div class="buff-title">念系增幅 · NEN BUFF</div>
          <div class="buff-row">
            <span class="buff-tag">强化系</span>
            <span class="buff-desc">生命 +1（共 6 点）</span>
          </div>
          <div class="buff-row">
            <span class="buff-tag">变化系</span>
            <span class="buff-desc">按 <span class="key">J</span> 键（手机点按钮）伪装成敌方 5 秒，期间无敌（每局限 1 次）</span>
          </div>
          <div v-if="hunter.nenType" class="buff-current">当前念系：{{ hunter.nenType === 'enhancement' ? '强化系' : '变化系' }}</div>
        </div>
        <button class="start-btn" @click="startGame">开始训练 · BEGIN</button>
        <div v-if="bestScore > 0" class="best">历史最高赏金：¥ {{ bestScore }}</div>
      </div>
    </div>

    <!-- 结束界面 -->
    <div v-if="phase === 'over'" class="panel-overlay">
      <div class="panel">
        <div class="panel-emblem">⚔</div>
        <div class="panel-eyebrow">TRAINING COMPLETE</div>
        <h1 class="panel-title">训练结束</h1>
        <div class="panel-divider"></div>
        <div class="result-label">本局赏金 · BOUNTY</div>
        <div class="result-score">¥ {{ finalScore }}</div>
        <div v-if="finalScore >= bestScore && finalScore > 0" class="best new">★ 新纪录！</div>
        <div v-else class="best">历史最高：¥ {{ bestScore }}</div>
        <div class="panel-actions">
          <button class="start-btn" @click="startGame">再来一局 · RETRY</button>
          <button class="ghost-btn" @click="router.push('/hunter/training')">返回训练</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.session-page {
  --accent: #e5484d;
  --accent2: #ff8a4d;
  --gold: #c9a961;
  --gold-bright: #e8c878;
  --gold-dim: #8a7140;
  --parchment: #d9c9a3;
  --text-dim: #8a7e6a;
  --line: rgba(201, 169, 97, 0.25);
  --bg-deep: #0a0705;

  min-height: 100vh;
  background: var(--bg-deep);
  color: var(--parchment);
  font-family: 'Cormorant Garamond', 'Noto Serif SC', 'Songti SC', 'SimSun', serif;
  position: relative;
  overflow: hidden;
  user-select: none;
  animation: page-in 0.5s ease-out both;
}
@keyframes page-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

.game-canvas {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  touch-action: none;
}

.disguise-btn {
  position: fixed;
  right: 24px;
  bottom: 32px;
  z-index: 150;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(229, 72, 77, 0.12);
  border: 1px solid var(--accent2);
  color: var(--gold-bright);
  font-family: 'Cinzel', 'Noto Serif SC', serif;
  font-size: 13px;
  letter-spacing: 0.12em;
  border-radius: 10px;
  cursor: pointer;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
}
.disguise-key {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: 1px solid var(--gold-dim);
  border-radius: 5px;
  font-family: 'JetBrains Mono', 'Consolas', monospace;
  font-size: 12px;
}
.disguise-btn:active {
  background: rgba(229, 72, 77, 0.28);
  border-color: var(--accent);
}

.nav {
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 100;
  background: rgba(10, 7, 5, 0.8);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--line);
  padding: 12px 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.nav-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  font-family: 'Cinzel', 'Times New Roman', serif;
  font-weight: 700;
  letter-spacing: 0.16em;
  font-size: 13px;
  color: var(--gold);
}
.nav-brand svg { width: 34px; height: 26px; }
.nav-actions { display: flex; align-items: center; gap: 12px; }
.nav-back {
  background: none;
  border: 1px solid var(--gold-dim);
  color: var(--gold);
  padding: 7px 15px;
  cursor: pointer;
  font-family: 'Cinzel', 'Noto Serif SC', serif;
  font-size: 12px;
  letter-spacing: 0.12em;
  transition: all 0.3s;
  white-space: nowrap;
}
.nav-back:hover {
  border-color: var(--gold-bright);
  color: var(--gold-bright);
  text-shadow: 0 0 12px rgba(232, 200, 120, 0.5);
  box-shadow: 0 0 14px rgba(201, 169, 97, 0.25);
}

.panel-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: rgba(10, 7, 5, 0.82);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  animation: fade-in 0.4s;
}
@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}
.panel {
  width: 100%;
  max-width: 560px;
  background: linear-gradient(160deg, #1a1410, #0f0b08);
  border: 1px solid var(--gold);
  padding: 12px;
  text-align: center;
  box-shadow: 0 0 60px rgba(201, 169, 97, 0.12);
  animation: panel-up 0.5s cubic-bezier(0.22, 1, 0.36, 1) both;
}
@keyframes panel-up {
  from { opacity: 0; transform: translateY(30px) scale(0.97); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
.panel::before {
  content: '';
  display: block;
  margin: 0 auto 20px;
  width: 100%;
  height: 0;
}
.panel-inner { border: 1px solid var(--line); padding: 40px 36px; }
.panel > * { position: relative; }

.panel-emblem {
  font-size: 54px;
  line-height: 1;
  color: var(--accent2);
  filter: drop-shadow(0 0 18px var(--accent));
  margin-top: 12px;
}
.panel-eyebrow {
  font-family: 'JetBrains Mono', 'Consolas', monospace;
  font-size: 11px;
  letter-spacing: 0.4em;
  color: var(--text-dim);
  text-transform: uppercase;
  margin-top: 18px;
}
.panel-title {
  font-family: 'Noto Serif SC', 'Songti SC', serif;
  font-weight: 700;
  font-size: 30px;
  color: var(--gold-bright);
  margin: 8px 0 0;
  letter-spacing: 0.08em;
}
.panel-divider {
  width: 200px;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--accent2), transparent);
  margin: 24px auto;
}

.controls {
  text-align: left;
  max-width: 420px;
  margin: 0 auto 28px;
  font-family: 'Noto Serif SC', 'Songti SC', serif;
  color: var(--parchment);
  font-size: 14px;
  line-height: 2;
}
.controls-title {
  font-family: 'Cinzel', serif;
  font-size: 12px;
  letter-spacing: 0.25em;
  color: var(--gold);
  text-align: center;
  margin-bottom: 10px;
}
.control-row { margin: 0 0 6px; }
.control-row.dim { color: var(--text-dim); font-size: 13px; }
.key {
  display: inline-block;
  padding: 0 8px;
  margin: 0 2px;
  border: 1px solid var(--gold-dim);
  border-radius: 4px;
  color: var(--gold-bright);
  font-family: 'JetBrains Mono', 'Consolas', monospace;
  font-size: 12px;
  letter-spacing: 0.05em;
  background: rgba(201, 169, 97, 0.06);
}

.buff-box {
  max-width: 420px;
  margin: 0 auto 24px;
  text-align: left;
  border: 1px solid var(--line);
  background: rgba(201, 169, 97, 0.04);
  padding: 14px 18px;
  font-family: 'Noto Serif SC', 'Songti SC', serif;
  font-size: 13px;
  line-height: 1.9;
}
.buff-title {
  font-family: 'Cinzel', serif;
  font-size: 12px;
  letter-spacing: 0.25em;
  color: var(--gold);
  text-align: center;
  margin-bottom: 8px;
}
.buff-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 4px 0;
}
.buff-tag {
  flex: 0 0 auto;
  display: inline-block;
  padding: 0 8px;
  border: 1px solid var(--accent2);
  border-radius: 3px;
  color: var(--accent2);
  font-size: 12px;
  letter-spacing: 0.05em;
  white-space: nowrap;
}
.buff-desc { color: var(--parchment); }
.buff-current {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--line);
  color: var(--gold-bright);
  font-size: 12px;
  text-align: center;
}

.start-btn {
  display: inline-block;
  padding: 15px 54px;
  background: linear-gradient(180deg, var(--accent) 0%, transparent 160%);
  color: var(--gold-bright);
  border: 1px solid var(--accent2);
  font-family: 'Cinzel', serif;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.4s;
}
.start-btn:hover {
  box-shadow: 0 0 34px var(--accent), inset 0 0 24px rgba(255, 138, 77, 0.25);
  transform: translateY(-2px);
}
.ghost-btn {
  display: inline-block;
  padding: 14px 34px;
  background: none;
  color: var(--gold);
  border: 1px solid var(--gold-dim);
  font-family: 'Cinzel', 'Noto Serif SC', serif;
  font-size: 13px;
  letter-spacing: 0.2em;
  cursor: pointer;
  transition: all 0.3s;
}
.ghost-btn:hover { border-color: var(--gold-bright); color: var(--gold-bright); }

.best {
  margin-top: 20px;
  font-family: 'JetBrains Mono', 'Consolas', monospace;
  font-size: 12px;
  letter-spacing: 0.12em;
  color: var(--gold-dim);
}
.best.new { color: var(--accent2); text-shadow: 0 0 12px var(--accent); }

.result-label {
  font-family: 'Cinzel', serif;
  font-size: 12px;
  letter-spacing: 0.3em;
  color: var(--text-dim);
  margin-top: 8px;
}
.result-score {
  font-family: 'Cinzel', serif;
  font-weight: 800;
  font-size: 64px;
  color: var(--gold-bright);
  line-height: 1;
  margin: 10px 0 4px;
  text-shadow: 0 0 30px rgba(232, 200, 120, 0.35);
}
.panel-actions {
  display: flex;
  gap: 14px;
  justify-content: center;
  margin-top: 30px;
  flex-wrap: wrap;
}

@media (max-width: 600px) {
  .nav { padding: 10px 12px; }
  .nav-brand span { font-size: 10px; letter-spacing: 0.1em; }
  .nav-back { padding: 6px 10px; font-size: 10px; }
  .panel-title { font-size: 24px; }
  .result-score { font-size: 48px; }
  .controls { font-size: 13px; }
}
</style>
