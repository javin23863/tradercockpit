const TAU = Math.PI * 2
const STEP = 1 / 60
const COLORS = {
  gold: [255, 184, 72], orange: [255, 103, 22], hot: [255, 239, 199],
  magenta: [211, 76, 255], blue: [91, 172, 255], green: [72, 221, 137],
  violet: [139, 99, 255], red: [255, 75, 57],
}
const MOTION_CONTRACT = Object.freeze({
  fixedStep: STEP,
  particle: Object.freeze({ count: 320, mobileCount: 150, birthX: [.03, .21], velocity: [-.01, .01], lifetimeScale: [.55, 1.3], ageRate: .44, drag: 1.7, stages: [.28, .62, .88], guidance: [.026, .14, .17, .24], captureRadius: .72 }),
  chronosphere: Object.freeze({ shells: 7, phaseSpeed: [.32, .47], radiusStep: .28, yRadiusStep: .085, precessionRate: .08 }),
  correlation: Object.freeze({ frontsPerSide: 6, leftCyclesPerSecond: .075, rightCyclesPerSecond: .07, phaseOffset: .08 }),
  probability: Object.freeze({ bands: 7, exponent: 1.28, waveFrequency: 8.8, temporalRate: [.42, .528], packetRate: [.055, .07] }),
  voiceStates: Object.freeze(['listening', 'reasoning', 'retrieving', 'speaking', 'interrupted']),
})

const clamp = (value, min = 0, max = 1) => Math.max(min, Math.min(max, value))
const mix = (a, b, amount) => a + (b - a) * amount
const fract = (value) => value - Math.floor(value)
const hash = (value) => fract(Math.sin(value * 91.317 + 17.173) * 43758.5453123)
const rgba = (color, alpha) => `rgba(${color[0]},${color[1]},${color[2]},${clamp(alpha)})`

function mulberry32(seed) {
  let value = seed >>> 0
  return () => {
    value |= 0
    value = value + 0x6D2B79F5 | 0
    let result = Math.imul(value ^ value >>> 15, 1 | value)
    result = result + Math.imul(result ^ result >>> 7, 61 | result) ^ result
    return ((result ^ result >>> 14) >>> 0) / 4294967296
  }
}

const glowSprites = new Map()
function glowSprite(color) {
  const key = color.join(',')
  if (glowSprites.has(key)) return glowSprites.get(key)
  const sprite = document.createElement('canvas')
  sprite.width = sprite.height = 48
  const context = sprite.getContext('2d')
  const gradient = context.createRadialGradient(24, 24, 0, 24, 24, 24)
  gradient.addColorStop(0, rgba(color, 1))
  gradient.addColorStop(.2, rgba(color, .62))
  gradient.addColorStop(.52, rgba(color, .16))
  gradient.addColorStop(1, rgba(color, 0))
  context.fillStyle = gradient
  context.fillRect(0, 0, 48, 48)
  glowSprites.set(key, sprite)
  return sprite
}

function dot(context, x, y, radius, color = COLORS.gold, alpha = .7) {
  const size = Math.max(2, radius * 3)
  context.save()
  context.globalAlpha = alpha
  context.drawImage(glowSprite(color), x - size, y - size, size * 2, size * 2)
  context.restore()
  context.beginPath()
  context.arc(x, y, Math.max(.4, radius * .38), 0, TAU)
  context.fillStyle = rgba(COLORS.hot, Math.min(.92, alpha * 1.4))
  context.fill()
}

function stroke(context, color, alpha, width, glow = 3) {
  if (glow) {
    context.strokeStyle = rgba(color, alpha * .2)
    context.lineWidth = width + glow
    context.stroke()
  }
  context.strokeStyle = rgba(color, alpha)
  context.lineWidth = width
  context.stroke()
}

class ParticleField {
  constructor(count = 320, seed = 0x9e3779b9) {
    this.count = count
    this.seed = seed
    this.state = new Float32Array(count * 9)
    this.reset(0)
  }

  spawn(index, fresh = false) {
    const offset = index * 9
    const rng = this.rng
    this.state[offset] = .03 + rng() * .18
    this.state[offset + 1] = .5 + (rng() + rng() - 1) * .42
    this.state[offset + 2] = rng() * 2 - 1
    this.state[offset + 3] = (rng() - .5) * .02
    this.state[offset + 4] = (rng() - .5) * .02
    this.state[offset + 5] = fresh ? 0 : rng()
    this.state[offset + 6] = .55 + rng() * .75
    this.state[offset + 7] = rng()
    this.state[offset + 8] = 0
  }

  reset(seconds) {
    this.rng = mulberry32(this.seed)
    for (let index = 0; index < this.count; index++) this.spawn(index)
    this.time = 0
    for (let index = 0; index < 90; index++) this.step(STEP)
    this.time = 0
    const steps = Math.max(0, Math.round(seconds / STEP))
    for (let index = 0; index < steps; index++) this.step(STEP)
  }

  seek(seconds) {
    if (seconds < this.time || seconds - this.time > .25) {
      this.reset(seconds)
      return
    }
    while (this.time + STEP <= seconds + 1e-6) this.step(STEP)
  }

  step(dt) {
    const centerX = .79
    const centerY = .52
    const coreRadius = .17
    const state = this.state
    const time = this.time
    for (let index = 0; index < this.count; index++) {
      const offset = index * 9
      let x = state[offset]
      let y = state[offset + 1]
      state[offset + 5] += dt * MOTION_CONTRACT.particle.ageRate / state[offset + 6]
      const age = state[offset + 5]
      const seed = state[offset + 7]
      const turbulenceX = Math.sin(3.1 * y + time * .5 + seed * TAU) + .5 * Math.sin(7.3 * y - time * .8)
      const turbulenceY = Math.cos(2.7 * x - time * .45 + seed * 4.1) + .5 * Math.cos(6.1 * x + time * .7)
      let forceX = turbulenceX * .01
      let forceY = turbulenceY * .01
      let targetX
      let targetY
      let guidance
      if (age < MOTION_CONTRACT.particle.stages[0]) {
        targetX = .16
        targetY = .5 + (seed - .5) * .44
        guidance = MOTION_CONTRACT.particle.guidance[0]
      } else if (age < MOTION_CONTRACT.particle.stages[1]) {
        const well = Math.floor(seed * 6) % 6
        const orbit = (.62 - age) * .13
        const phase = time * (.65 + .1 * well) + seed * 18
        targetX = .38 + Math.cos(phase) * orbit
        targetY = .5 + ((well * .618034) % 1 - .5) * .52 + Math.sin(phase) * orbit
        guidance = MOTION_CONTRACT.particle.guidance[1]
      } else if (age < MOTION_CONTRACT.particle.stages[2]) {
        const well = Math.floor(seed * 97) % 3
        const orbit = (.88 - age) * .1
        const phase = -time * (.85 + .08 * well) + seed * 15
        targetX = .61 + Math.cos(phase) * orbit
        targetY = .5 + ((well * .618034 + .21) % 1 - .5) * .34 + Math.sin(phase) * orbit
        guidance = MOTION_CONTRACT.particle.guidance[2]
      } else {
        targetX = centerX
        targetY = centerY
        guidance = MOTION_CONTRACT.particle.guidance[3]
        const spin = .075 * (1 - age + .22)
        forceX -= (centerY - y) * spin
        forceY += (centerX - x) * spin
      }
      forceX += (targetX - x) * guidance
      forceY += (targetY - y) * guidance
      state[offset + 3] = (state[offset + 3] + forceX * dt * 8) * Math.exp(-MOTION_CONTRACT.particle.drag * dt)
      state[offset + 4] = (state[offset + 4] + forceY * dt * 8) * Math.exp(-MOTION_CONTRACT.particle.drag * dt)
      x += state[offset + 3] * dt * 8
      y += state[offset + 4] * dt * 8
      state[offset] = x
      state[offset + 1] = y
      const distance = Math.hypot(centerX - x, centerY - y)
      if (distance < coreRadius * MOTION_CONTRACT.particle.captureRadius || age >= 1) this.spawn(index, true)
    }
    this.time += dt
  }
}

function corePath(context, x, y, radius, time, seed, layer = 0) {
  context.beginPath()
  for (let point = 0; point <= 64; point++) {
    const angle = point / 64 * TAU
    const deformation = 1
      + Math.sin(angle * 3 + time * .23 + seed * .7 + layer) * .025
      + Math.sin(angle * 7 - time * .17 + seed * 1.3 - layer) * .012
    const px = x + Math.cos(angle) * radius * deformation
    const py = y + Math.sin(angle) * radius * deformation
    if (point) context.lineTo(px, py); else context.moveTo(px, py)
  }
  context.closePath()
}

function drawCore(context, x, y, radius, time, seed = 1, state = 'core') {
  context.save()
  context.globalCompositeOperation = 'lighter'
  const pulse = 1 + Math.sin(time * (.72 + hash(seed) * .25) + seed) * .035
  const r = radius * pulse
  const halo = context.createRadialGradient(x, y, r * .15, x, y, r * 1.65)
  halo.addColorStop(0, rgba(COLORS.hot, .3))
  halo.addColorStop(.38, rgba(COLORS.orange, .16))
  halo.addColorStop(1, rgba(COLORS.orange, 0))
  context.fillStyle = halo
  context.fillRect(x - r * 1.8, y - r * 1.8, r * 3.6, r * 3.6)

  const body = context.createRadialGradient(x - r * .25, y - r * .3, r * .05, x, y, r)
  body.addColorStop(0, '#fff6d4')
  body.addColorStop(.12, '#ff9c28')
  body.addColorStop(.43, '#a92d0a')
  body.addColorStop(.78, '#260508')
  body.addColorStop(1, '#040101')
  context.fillStyle = body
  corePath(context, x, y, r, time, seed)
  context.fill()
  corePath(context, x, y, r * .985, time, seed, .8)
  stroke(context, COLORS.orange, .72, .9, 4)
  corePath(context, x, y, r * .91, time, seed, 1.7)
  stroke(context, COLORS.gold, .24, .55, 2)

  context.save()
  corePath(context, x, y, r * .97, time, seed, .2)
  context.clip()
  const filaments = radius > 65 ? 13 : 8
  for (let index = 0; index < filaments; index++) {
    const value = hash(seed * 41 + index * 7.13)
    const start = TAU * value + time * (.014 + hash(seed + index) * .017) * (index % 2 ? 1 : -1)
    const curl = mix(-2.2, 2.4, hash(seed * 3 + index * 19))
    const phase = TAU * hash(seed * 11 + index * 3.7)
    context.beginPath()
    for (let point = 0; point <= 16; point++) {
      const amount = point / 16
      const rr = r * (.08 + .9 * amount)
      const wave = .12 * Math.sin(amount * (8 + hash(index + seed) * 7) + phase + time * (.18 + value * .2))
      const angle = start + curl * (amount - .45) + wave
      const px = x + Math.cos(angle) * rr + Math.sin(amount * 15 + phase) * r * .012
      const py = y + Math.sin(angle) * rr + Math.cos(amount * 11 + phase) * r * .01
      if (point) context.lineTo(px, py); else context.moveTo(px, py)
    }
    const color = hash(seed + index * 9) > .84 ? COLORS.magenta : (value > .72 ? COLORS.hot : COLORS.gold)
    stroke(context, color, .48 + value * .36, value > .72 ? 1.05 : .72, 2.2)
  }
  context.restore()

  for (const side of [-1, 1]) {
    context.beginPath()
    for (let point = 0; point <= 34; point++) {
      const amount = point / 34
      const py = y + (amount - .5) * r * 1.45
      const px = x + side * r * .1 + Math.sin((amount - .5) * 5 + time * .065 + seed) * r * .09
      if (point) context.lineTo(px, py); else context.moveTo(px, py)
    }
    stroke(context, side < 0 ? COLORS.magenta : COLORS.blue, .24, .7, 2)
  }

  const prominenceCount = radius > 65 ? 7 : 4
  for (let index = 0; index < prominenceCount; index++) {
    const angle = TAU * hash(seed * 13 + index * 11) + time * (.006 + hash(seed + index) * .008)
    const span = mix(.08, .22, hash(seed * 7 + index * 5))
    const height = r * mix(.08, state === 'speaking' ? .3 : .18, hash(seed * 23 + index * 3))
    const a0 = angle - span
    const a1 = angle + span
    const x0 = x + Math.cos(a0) * r
    const y0 = y + Math.sin(a0) * r
    const x1 = x + Math.cos(a1) * r
    const y1 = y + Math.sin(a1) * r
    const apexX = x + Math.cos(angle) * (r + height)
    const apexY = y + Math.sin(angle) * (r + height)
    context.beginPath()
    context.moveTo(x0, y0)
    context.quadraticCurveTo(apexX, apexY, x1, y1)
    stroke(context, COLORS.gold, .62, .9, 3.4)
  }

  for (let index = 0; index < Math.max(4, Math.round(radius / 18)); index++) {
    const amount = fract(time * (.025 + hash(seed + index) * .018) + hash(seed * 8 + index * 17))
    const angle = TAU * hash(seed * 4 + index * 23) + amount * 1.4
    const rr = r * (.2 + .75 * amount)
    dot(context, x + Math.cos(angle) * rr, y + Math.sin(angle) * rr, 1.05, COLORS.gold, .58)
  }
  drawVoiceGrammar(context, x, y, r, time, state)
  context.restore()
}

function drawVoiceGrammar(context, x, y, radius, time, state) {
  if (!state || state === 'core') return
  if (state === 'listening') {
    context.setLineDash([3, 5])
    context.lineDashOffset = -time * 5
    context.beginPath()
    context.ellipse(x, y, radius * 1.3, radius * .72, -.18, Math.PI * .78, Math.PI * 1.7)
    stroke(context, COLORS.blue, .55, .8, 2)
    context.setLineDash([])
    for (let index = 0; index < 4; index++) {
      const amount = fract(time * (.08 + index * .009) + index * .21)
      dot(context, x - radius * mix(1.7, 1.02, amount), y + (index - 1.5) * radius * .16, .9, COLORS.blue, (1 - amount) * .7)
    }
  } else if (state === 'reasoning') {
    for (let index = 0; index < 2; index++) {
      context.setLineDash([3, 3.5])
      context.lineDashOffset = (index ? 1 : -1) * time * 6
      context.beginPath()
      context.ellipse(x, y, radius * (1.22 + index * .13), radius * (.56 + index * .08), (index ? -1 : 1) * time * (.12 + index * .04), 0, TAU)
      stroke(context, index ? COLORS.gold : COLORS.orange, .52, .8, 2)
    }
    context.setLineDash([])
  } else if (state === 'retrieving') {
    const angle = time * .5
    context.setLineDash([4, 3])
    context.lineDashOffset = -time * 7
    context.beginPath()
    context.ellipse(x, y, radius * 1.54, radius * .66, -.14, 0, TAU)
    stroke(context, COLORS.gold, .64, .8, 2)
    context.setLineDash([])
    const px = x + Math.cos(angle) * radius * 1.54
    const py = y + Math.sin(angle) * radius * .66
    dot(context, px, py, 1.2, COLORS.hot, .8)
    context.beginPath()
    context.moveTo(x + radius * .7, y + radius * .1)
    context.quadraticCurveTo(x + radius, y - radius * .7, px, py)
    stroke(context, COLORS.orange, .5, .8, 2)
  } else if (state === 'speaking') {
    for (let index = 0; index < 3; index++) {
      const phase = fract(time * .23 + index * .31)
      context.beginPath()
      context.arc(x, y, radius * (1.03 + phase * .78), -.46, .46)
      stroke(context, COLORS.gold, (1 - phase) * .5, .8, 2)
    }
    for (const side of [-1, 1]) {
      context.beginPath()
      context.moveTo(x + side * radius * .9, y - radius * .16)
      context.bezierCurveTo(x + side * radius * 1.28, y - radius * .36, x + side * radius * 1.55, y + radius * .2, x + side * radius * 1.9, y)
      stroke(context, COLORS.orange, .58, 1, 3)
    }
  } else if (state === 'interrupted') {
    context.setLineDash([4, 7])
    context.lineDashOffset = -Math.floor(time * 7)
    context.beginPath()
    context.arc(x, y, radius * 1.1, 0, TAU)
    stroke(context, COLORS.red, .42 + .18 * Math.sin(time * 4.2), .8, 2)
    context.setLineDash([])
    if (Math.sin(time * 5.7) > .2) {
      context.beginPath()
      context.moveTo(x - radius, y + radius * .14)
      context.lineTo(x + radius * .9, y + radius * .1)
      stroke(context, COLORS.orange, .38, .6, 1)
    }
  }
}

function drawGenesis(context, width, height, time, field, limit = MOTION_CONTRACT.particle.count) {
  field.seek(((time % 6) + 6) % 6)
  context.save()
  context.globalCompositeOperation = 'lighter'
  const scale = Math.min(width, height)
  const state = field.state
  const groups = [COLORS.orange, COLORS.gold, COLORS.hot].map((color) => ({ color, heads: new Path2D(), trails: new Path2D() }))
  for (let index = 0; index < Math.min(limit, field.count); index++) {
    const offset = index * 9
    const age = state[offset + 5]
    const fade = Math.min(1, age * 6) * (1 - Math.max(0, age - .82) / .18)
    const x = state[offset] * width
    const y = state[offset + 1] * height
    const vx = state[offset + 3] * width
    const vy = state[offset + 4] * height
    const size = (.55 + 3.1 * age * age) * (1 + state[offset + 2] * .2) * scale / 240
    if (fade <= .04) continue
    const group = groups[state[offset + 7] > .95 ? 2 : (state[offset + 7] > .67 ? 1 : 0)]
    group.trails.moveTo(x - vx * 3, y - vy * 3)
    group.trails.lineTo(x, y)
    group.heads.moveTo(x + Math.max(.55, size), y)
    group.heads.arc(x, y, Math.max(.55, size), 0, TAU)
    if (state[offset + 7] > .97 && index % 11 === 0) dot(context, x, y, Math.max(.7, size), COLORS.hot, fade * .45)
  }
  context.lineCap = 'round'
  for (const group of groups) {
    context.strokeStyle = rgba(group.color, .22)
    context.lineWidth = Math.max(.4, scale / 520)
    context.stroke(group.trails)
    context.fillStyle = rgba(group.color, .5)
    context.fill(group.heads)
  }
  context.restore()
  const targetRadius = width < 280 ? height * .4 : Math.min(width * .21, height * .34)
  drawCore(context, width * .79, height * .52, targetRadius, time, 17)
}

function drawAtlas(context, width, height, time) {
  const x = width / 2
  const y = height * .5
  const radius = Math.min(width, height) * .25
  const nodes = [[0,-1],[-.82,-.56],[.82,-.56],[-1,.18],[1,.18],[-.72,.82],[.72,.82]]
  context.save()
  context.globalCompositeOperation = 'lighter'
  for (let index = 0; index < nodes.length; index++) {
    const nx = x + nodes[index][0] * radius * 1.65
    const ny = y + nodes[index][1] * radius * 1.4
    context.beginPath(); context.moveTo(x, y); context.lineTo(nx, ny)
    stroke(context, COLORS.gold, .2, .7, 1)
    const amount = fract(time * (.055 + index * .0015) + index * .113)
    dot(context, mix(x, nx, amount), mix(y, ny, amount), .9, index % 3 ? COLORS.gold : COLORS.blue, Math.sin(Math.PI * amount) * .55)
    dot(context, nx, ny, 1.3, COLORS.hot, .65)
  }
  context.restore()
  drawCore(context, x, y, radius, time, 23)
}

function drawExecution(context, width, height, time) {
  const x = width / 2
  const y = height * .51
  const radius = Math.min(width, height) * .25
  context.save()
  context.globalCompositeOperation = 'lighter'
  for (let index = 0; index < 2; index++) {
    context.setLineDash(index ? [2, 5] : [7, 6])
    context.lineDashOffset = (index ? 1 : -1) * time * (8 + index * 3)
    context.beginPath(); context.arc(x, y, radius * (1.18 + index * .45), 0, TAU)
    stroke(context, index ? COLORS.blue : COLORS.gold, index ? .24 : .34, .8, 2)
  }
  context.setLineDash([])
  const angle = time * .38
  dot(context, x + Math.cos(angle) * radius * 1.63, y + Math.sin(angle) * radius * 1.63, 1.3, COLORS.hot, .8)
  for (let index = 0; index < 8; index++) {
    const checkpoint = index * TAU / 8
    const pulse = .45 + .55 * Math.sin(time * 1.7 + index * .8)
    dot(context, x + Math.cos(checkpoint) * radius * 1.18, y + Math.sin(checkpoint) * radius * 1.18, 1, index % 3 === 1 ? COLORS.blue : COLORS.gold, .28 * pulse)
  }
  context.restore()
  drawCore(context, x, y, radius * .78, time, 31)
}

function drawConstellation(context, width, height, time) {
  const x = width / 2
  const y = height * .5
  const radius = Math.min(width, height) * .29
  const nodes = Array.from({ length: 9 }, (_, index) => {
    const angle = -Math.PI / 2 + index * TAU / 9
    return [x + Math.cos(angle) * radius * 2.05, y + Math.sin(angle) * radius * 1.55]
  })
  context.save(); context.globalCompositeOperation = 'lighter'
  nodes.forEach(([nx, ny], index) => {
    context.beginPath(); context.moveTo(x, y); context.quadraticCurveTo(width * hash(index + 2), height * hash(index + 7), nx, ny)
    stroke(context, COLORS.gold, .15, .65, 1)
    const amount = fract(time * (.055 + index * .0015) + index * .113)
    dot(context, mix(x, nx, amount), mix(y, ny, amount), .8, index % 4 ? COLORS.gold : COLORS.blue, Math.sin(Math.PI * amount) * .4)
    dot(context, nx, ny, 1, COLORS.hot, .5)
  })
  context.restore()
  drawCore(context, x, y, radius, time, 37)
}

function drawChronosphere(context, width, height, time) {
  const x = width / 2
  const y = height * .59
  const coreRadius = Math.min(width, height) * .245
  const colors = [COLORS.gold, [255, 199, 84], COLORS.green, [68, 210, 205], COLORS.blue, [107, 132, 255], COLORS.violet]
  context.save(); context.globalCompositeOperation = 'lighter'
  for (let index = 0; index < MOTION_CONTRACT.chronosphere.shells; index++) {
    const rx = coreRadius * (.92 + index * MOTION_CONTRACT.chronosphere.radiusStep)
    const ry = coreRadius * (.46 + index * MOTION_CONTRACT.chronosphere.yRadiusStep)
    const rotation = (index - 3) * .015 + Math.sin(time * MOTION_CONTRACT.chronosphere.precessionRate + index) * .006
    context.setLineDash([5 + index * .4, 3 + index * .25])
    context.lineDashOffset = -time * (7 + index * .6) * (index % 2 ? 1 : -1)
    context.beginPath(); context.ellipse(x, y, rx, ry, rotation, 0, TAU)
    stroke(context, colors[index], .38, index === 3 ? 1 : .7, 2)
    const phaseStep = (MOTION_CONTRACT.chronosphere.phaseSpeed[1] - MOTION_CONTRACT.chronosphere.phaseSpeed[0]) / (MOTION_CONTRACT.chronosphere.shells - 1)
    const angle = time * (MOTION_CONTRACT.chronosphere.phaseSpeed[0] + index * phaseStep) * (index % 2 ? -1 : 1) + index * .78
    dot(context, x + Math.cos(angle) * rx, y + Math.sin(angle) * ry, 1, colors[index], .65)
  }
  context.setLineDash([]); context.restore()
  drawCore(context, x, y, coreRadius, time, 43)
}

function drawCorrelation(context, width, height, time) {
  const x = width / 2
  const y = height * .58
  const coreRadius = Math.min(width, height) * .2
  context.save(); context.globalCompositeOperation = 'lighter'
  for (let index = 0; index < MOTION_CONTRACT.correlation.frontsPerSide; index++) {
    const phaseLeft = fract(time * MOTION_CONTRACT.correlation.leftCyclesPerSecond + index / MOTION_CONTRACT.correlation.frontsPerSide)
    const phaseRight = fract(time * MOTION_CONTRACT.correlation.rightCyclesPerSecond + index / MOTION_CONTRACT.correlation.frontsPerSide + MOTION_CONTRACT.correlation.phaseOffset)
    const leftRadius = coreRadius * (.42 + phaseLeft * 3.35)
    const rightRadius = coreRadius * (.42 + phaseRight * 3.35)
    context.setLineDash([5, 3]); context.lineDashOffset = -time * 7 - index * 2
    context.beginPath(); context.arc(x - coreRadius * 2.8, y, leftRadius, -.72, .72)
    stroke(context, COLORS.green, .07 + .3 * (1 - phaseLeft), .8, 2)
    context.beginPath(); context.arc(x + coreRadius * 2.8, y, rightRadius, Math.PI - .72, Math.PI + .72)
    stroke(context, COLORS.blue, .07 + .3 * (1 - phaseRight), .8, 2)
  }
  context.setLineDash([])
  for (let index = 0; index < 5; index++) dot(context, x + Math.sin(time * .65 + index) * 3, y - coreRadius * .8 + index * coreRadius * .4, .9, COLORS.hot, .25 + .2 * Math.sin(time * 2.2 + index))
  context.restore()
  drawCore(context, x, y, coreRadius, time, 47)
}

function probabilityY(index, amount, time, centerY, span) {
  const quantile = 1 - index / 3
  const envelope = span * Math.pow(amount, MOTION_CONTRACT.probability.exponent)
  const amplitude = 1.4 + 4 * amount
  const phase = amount * MOTION_CONTRACT.probability.waveFrequency
  const differential = Math.min(amplitude * .25, Math.abs(envelope) * .2)
  const temporalStep = (MOTION_CONTRACT.probability.temporalRate[1] - MOTION_CONTRACT.probability.temporalRate[0]) / (MOTION_CONTRACT.probability.bands - 1)
  return centerY + quantile * envelope + Math.sin(phase + time * MOTION_CONTRACT.probability.temporalRate[0]) * amplitude + Math.sin(phase + time * (MOTION_CONTRACT.probability.temporalRate[0] + index * temporalStep) + index * .65) * differential
}

function drawProbability(context, width, height, time) {
  const x = width * .3
  const y = height * .58
  const coreRadius = Math.min(width, height) * .25
  const colors = [COLORS.red, COLORS.orange, [255, 209, 76], COLORS.hot, COLORS.green, COLORS.blue, COLORS.violet]
  context.save(); context.globalCompositeOperation = 'lighter'
  for (let index = 0; index < MOTION_CONTRACT.probability.bands; index++) {
    const middle = index === 3
    context.beginPath()
    for (let point = 0; point <= 42; point++) {
      const amount = point / 42
      const px = mix(x + coreRadius * .62, width * .9, amount)
      const py = probabilityY(index, amount, time, y, height * .19)
      if (point) context.lineTo(px, py); else context.moveTo(px, py)
    }
    stroke(context, colors[index], middle ? .54 : .34, middle ? 1.15 : .72, middle ? 3 : 2)
    context.beginPath()
    for (let point = 0; point <= 26; point++) {
      const amount = point / 26
      const px = mix(x - coreRadius * .62, width * .03, amount)
      const py = probabilityY(index, amount, time + 1.3, y, height * .1)
      if (point) context.lineTo(px, py); else context.moveTo(px, py)
    }
    stroke(context, colors[index], middle ? .3 : .18, middle ? .9 : .6, 1.5)
    const packetStep = (MOTION_CONTRACT.probability.packetRate[1] - MOTION_CONTRACT.probability.packetRate[0]) / (MOTION_CONTRACT.probability.bands - 1)
    const packet = fract(time * (MOTION_CONTRACT.probability.packetRate[0] + index * packetStep) + index * .137)
    dot(context, mix(x + coreRadius * .62, width * .9, packet), probabilityY(index, packet, time, y, height * .19), middle ? 1.2 : .85, colors[index], middle ? .7 : .5)
  }
  context.restore()
  drawCore(context, x, y, coreRadius, time, 53)
}

function drawVoiceStates(context, width, height, time, activeState) {
  const states = MOTION_CONTRACT.voiceStates
  states.forEach((state, index) => {
    context.save(); context.globalAlpha = state === activeState ? 1 : .28
    drawCore(context, width * (.1 + index * .2), height * .55, Math.min(width / 13, height * .23) * (state === 'speaking' ? 1.18 : 1), time, 59 + index * 7, state)
    context.restore()
  })
}

const query = new URLSearchParams(location.search)
const prefersReduced = matchMedia('(prefers-reduced-motion: reduce)')
const forcedTime = Number(query.get('motionTime'))
const particleField = new ParticleField(MOTION_CONTRACT.particle.count)
const canvases = [...document.querySelectorAll('canvas[data-helios-motion]')].map((canvas) => ({
  canvas,
  context: canvas.getContext('2d', { alpha: true }),
  kind: canvas.dataset.heliosMotion,
  width: 0,
  height: 0,
  dpr: 1,
}))

let running = false
let speed = 1
let time = Number.isFinite(forcedTime) ? forcedTime : 0
let raf = 0
let lastClock = 0
let lastPaint = 0
let lastPresented = 0
let frameWindow = []
let renderWindow = []
let voiceState = 'listening'
let readbackSettled = false

function configure(item) {
  const rect = item.canvas.getBoundingClientRect()
  if (!rect.width || !rect.height) return false
  const mobile = innerWidth <= 760
  const dpr = mobile ? .65 : .7
  const width = Math.max(2, Math.round(rect.width * dpr))
  const height = Math.max(2, Math.round(rect.height * dpr))
  if (item.canvas.width !== width || item.canvas.height !== height) {
    item.canvas.width = width
    item.canvas.height = height
  }
  item.width = rect.width
  item.height = rect.height
  item.dpr = dpr
  item.context.setTransform(dpr, 0, 0, dpr, 0, 0)
  item.context.imageSmoothingEnabled = true
  return true
}

function renderItem(item, at) {
  if (!configure(item)) return
  const { canvas, context, width, height, dpr, kind } = item
  context.setTransform(1, 0, 0, 1, 0, 0)
  context.clearRect(0, 0, canvas.width, canvas.height)
  context.setTransform(dpr, 0, 0, dpr, 0, 0)
  if (kind === 'solar') drawCore(context, width / 2, height * .5, Math.min(width, height) * (width < 300 ? .46 : .42), at, 11, voiceState)
  else if (kind === 'genesis') drawGenesis(context, width, height, at, particleField)
  else if (kind === 'genesis-study') drawGenesis(context, width, height, at, particleField, 190)
  else if (kind === 'mobile-genesis') drawGenesis(context, width, height, at, particleField, MOTION_CONTRACT.particle.mobileCount)
  else if (kind === 'atlas') drawAtlas(context, width, height, at)
  else if (kind === 'execution') drawExecution(context, width, height, at)
  else if (kind === 'constellation') drawConstellation(context, width, height, at)
  else if (kind === 'chronosphere') drawChronosphere(context, width, height, at)
  else if (kind === 'correlation') drawCorrelation(context, width, height, at)
  else if (kind === 'probability') drawProbability(context, width, height, at)
  else if (kind === 'voice') drawVoiceStates(context, width, height, at, voiceState)
}

function render(at = time) {
  const started = performance.now()
  for (const item of canvases) renderItem(item, at)
  renderWindow.push(performance.now() - started)
  if (renderWindow.length > 180) renderWindow.shift()
  document.documentElement.dataset.motion = running ? 'running' : 'paused'
}

function targetFps() { return innerWidth <= 760 ? 18 : 24 }
function tick(now) {
  if (!running) return
  if (!lastClock) lastClock = now
  const delta = clamp((now - lastClock) / 1000, 0, .1)
  lastClock = now
  time += delta * speed
  // Small headroom absorbs display-callback quantization; the gate bounds
  // delivered cadence around each declared target.
  const presentationFps = targetFps() + (innerWidth <= 760 ? 2.5 : 2)
  const interval = 1000 / presentationFps
  if (!lastPaint || now - lastPaint >= interval - .5) {
    if (lastPresented) {
      frameWindow.push(now - lastPresented)
      if (frameWindow.length > 180) frameWindow.shift()
    }
    lastPresented = now
    lastPaint = lastPaint ? lastPaint + interval * Math.max(1, Math.floor((now - lastPaint) / interval)) : now
    render(time)
  }
  raf = requestAnimationFrame(tick)
}

function play() {
  if (running || prefersReduced.matches || document.hidden) return false
  running = true
  frameWindow = []
  renderWindow = []
  lastClock = 0
  lastPaint = 0
  lastPresented = 0
  raf = requestAnimationFrame(tick)
  return true
}

function pause() {
  running = false
  cancelAnimationFrame(raf)
  raf = 0
  lastClock = 0
  render(time)
}

function seek(value) {
  const next = Number(value)
  if (!Number.isFinite(next)) return time
  time = next
  frameWindow = []
  renderWindow = []
  particleField.reset(((time % 6) + 6) % 6)
  render(time)
  if (!readbackSettled) {
    for (const { context } of canvases) context.getImageData(0, 0, 1, 1)
    readbackSettled = true
    render(time)
  }
  return time
}

function status() {
  const sorted = [...frameWindow].sort((a, b) => a - b)
  const renderSorted = [...renderWindow].sort((a, b) => a - b)
  const p95 = sorted.length ? sorted[Math.min(sorted.length - 1, Math.floor(sorted.length * .95))] : 0
  const renderP95 = renderSorted.length ? renderSorted[Math.min(renderSorted.length - 1, Math.floor(renderSorted.length * .95))] : 0
  const mean = frameWindow.length ? frameWindow.reduce((sum, value) => sum + value, 0) / frameWindow.length : 0
  return {
    running, time, speed, targetFps: targetFps(), measuredFps: mean ? 1000 / mean : 0,
    p95FrameMs: p95, longFrameRatio: frameWindow.length ? frameWindow.filter((value) => value > 100).length / frameWindow.length : 0,
    renderP95Ms: renderP95, reducedMotion: prefersReduced.matches, canvasCount: canvases.length,
  }
}

function probe(value) {
  const at = Number(value)
  const sampleTime = Number.isFinite(at) ? at : time
  const particleTime = ((sampleTime % 6) + 6) % 6
  particleField.reset(particleTime)
  let finiteParticles = 0
  for (const coordinate of particleField.state) if (Number.isFinite(coordinate)) finiteParticles++
  const probability = Array.from({ length: MOTION_CONTRACT.probability.bands }, (_, index) => probabilityY(index, .8, sampleTime, 0, .19))
  const probabilitySamples = [18, 33].flatMap((span) => Array.from({ length: 43 }, (_, sample) => (
    Array.from({ length: MOTION_CONTRACT.probability.bands }, (_, index) => probabilityY(index, (sample + 1) / 43, sampleTime, 0, span))
  )))
  return {
    time: sampleTime,
    particle: { count: particleField.count, finiteValues: finiteParticles, valueCount: particleField.state.length },
    chronospherePhases: Array.from({ length: MOTION_CONTRACT.chronosphere.shells }, (_, index) => sampleTime * (MOTION_CONTRACT.chronosphere.phaseSpeed[0] + index * ((MOTION_CONTRACT.chronosphere.phaseSpeed[1] - MOTION_CONTRACT.chronosphere.phaseSpeed[0]) / (MOTION_CONTRACT.chronosphere.shells - 1))) * (index % 2 ? -1 : 1) + index * .78),
    correlationRadii: Array.from({ length: MOTION_CONTRACT.correlation.frontsPerSide }, (_, index) => ({
      left: .42 + fract(sampleTime * MOTION_CONTRACT.correlation.leftCyclesPerSecond + index / MOTION_CONTRACT.correlation.frontsPerSide) * 3.35,
      right: .42 + fract(sampleTime * MOTION_CONTRACT.correlation.rightCyclesPerSecond + index / MOTION_CONTRACT.correlation.frontsPerSide + MOTION_CONTRACT.correlation.phaseOffset) * 3.35,
    })),
    probability, probabilitySamples,
    executionAngle: sampleTime * .38,
  }
}

window.addEventListener('helios:voice-state', (event) => {
  voiceState = event.detail?.state || 'listening'
  render(time)
})
window.addEventListener('resize', () => render(time), { passive: true })
document.addEventListener('visibilitychange', () => document.hidden ? pause() : play())
prefersReduced.addEventListener('change', () => prefersReduced.matches ? pause() : play())

window.__heliosMotion = Object.freeze({ contract: MOTION_CONTRACT, play, pause, toggle: () => running ? pause() : play(), seek, status, probe, renderAt: seek })
window.__renderAt = ({ time: value = 12, paused = true } = {}) => {
  seek(value)
  if (paused) pause(); else play()
  return status()
}

if (prefersReduced.matches) seek(12)
else {
  render(time)
  play()
}
document.documentElement.dataset.heliosReady = 'true'
window.dispatchEvent(new CustomEvent('helios:ready', { detail: status() }))
