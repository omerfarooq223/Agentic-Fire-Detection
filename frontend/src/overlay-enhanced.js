/**
 * Enhanced Fire & Smoke Detection Overlay System
 * Stylish, animated, heat-mapped visualization with particle effects
 */

class DetectionOverlay {
  constructor(canvas, config = {}) {
    this.canvas = canvas
    this.ctx = canvas.getContext('2d')
    this.particles = []
    this.animationFrame = 0
    this.config = {
      glowIntensity: 0.8,
      particleCount: 8,
      pulseSpeed: 2,
      ...config,
    }
  }

  /**
   * Main render function - call this on each frame
   */
  render(vw, vh, frame) {
    const ctx = this.ctx
    ctx.save()

    this.animationFrame += this.config.pulseSpeed

    // Always render system status (even when scanning)
    if (frame?.system === 'scanning' || (!frame?.fire && !frame?.smoke)) {
      this.renderSystemStatus(ctx, vw, vh, frame)
      ctx.restore()
      return
    }

    // Render detection overlays only if fire or smoke detected
    if (frame?.fire || frame?.smoke) {
      this.renderSmokeZones(ctx, vw, vh, frame)
      this.renderFireZones(ctx, vw, vh, frame)
      this.renderParticles(ctx, vw, vh)
      this.renderLabels(ctx, vw, vh, frame)
    }

    this.renderSystemStatus(ctx, vw, vh, frame)
    ctx.restore()
  }

  /**
   * Render smoke detection zones with elegant styling
   */
  renderSmokeZones(ctx, vw, vh, frame) {
    const smoke = frame.smoke_boxes || []
    if (!smoke.length) return

    smoke.forEach((smokeBox, idx) => {
      const b = smokeBox?.bbox
      if (!b) return

      const x = (b.x - b.w / 2) * vw
      const y = (b.y - b.h / 2) * vh
      const w = b.w * vw
      const h = b.h * vh

      // Subtle pulsing effect for smoke
      const pulse = Math.sin(this.animationFrame * 0.03 + idx * 0.5) * 0.15 + 0.85
      const alpha = 0.25 * pulse

      // Smoke gradient (cool blues/purples)
      const gradient = ctx.createLinearGradient(x, y, x, y + h)
      gradient.addColorStop(0, `rgba(129, 140, 248, ${alpha * 0.6})`)
      gradient.addColorStop(0.5, `rgba(139, 92, 246, ${alpha * 0.4})`)
      gradient.addColorStop(1, `rgba(99, 102, 241, ${alpha * 0.3})`)

      // Draw rounded rectangle with gradient
      this.drawRoundedRect(ctx, x, y, w, h, 8)
      ctx.fillStyle = gradient
      ctx.fill()

      // Animated dashed border
      ctx.strokeStyle = `rgba(129, 140, 248, ${0.7 * pulse})`
      ctx.lineWidth = 2
      ctx.setLineDash([8, 6])
      ctx.lineDashOffset = -(this.animationFrame * 0.5)
      ctx.stroke()
      ctx.setLineDash([])
    })
  }

  /**
   * Render fire detection zones with heat mapping and glow
   */
  renderFireZones(ctx, vw, vh, frame) {
    const masks = frame.fire_masks || []
    const fireBoxes = frame.fire_boxes || []
    const fireArea = Number(frame.fire_segment_area_pixels || 0)

    // Calculate intensity (0-1) based on fire area
    const maxArea = 120000
    const intensity = Math.min(fireArea / maxArea, 1)

    if (masks.length > 0) {
      // Render polygonal masks (for segmentation)
      this.renderFireMasks(ctx, vw, vh, masks, intensity)
    } else if (fireBoxes.length > 0) {
      // Render bounding boxes
      this.renderFireBoxes(ctx, vw, vh, fireBoxes, intensity)
    } else if (frame.bbox && frame.fire) {
      // Fallback to frame bbox
      const b = frame.bbox
      const x = (b.x - b.w / 2) * vw
      const y = (b.y - b.h / 2) * vh
      const w = b.w * vw
      const h = b.h * vh
      this.renderFireBox(ctx, x, y, w, h, intensity)
    }

    // Spawn particles in fire zones
    if (intensity > 0.2) {
      this.spawnFireParticles(vw, vh, frame, intensity)
    }
  }

  /**
   * Render fire masks with smooth polygons and glow effects
   */
  renderFireMasks(ctx, vw, vh, masks, intensity) {
    masks.forEach((poly, idx) => {
      if (!poly || poly.length < 3) return

      const color = this.getHeatColor(intensity)

      // Multi-layer glow effect
      for (let i = 3; i >= 1; i--) {
        ctx.strokeStyle = `rgba(${color.r}, ${color.g}, ${color.b}, ${(0.2 / i) * intensity})`
        ctx.lineWidth = i * 2.5
        ctx.beginPath()
        ctx.moveTo(poly[0].x * vw, poly[0].y * vh)
        for (let j = 1; j < poly.length; j++) {
          ctx.lineTo(poly[j].x * vw, poly[j].y * vh)
        }
        ctx.closePath()
        ctx.stroke()
      }

      // Main fill with gradient
      const bounds = this.getPolyBounds(poly, vw, vh)
      const gradient = ctx.createRadialGradient(
        bounds.cx,
        bounds.cy,
        0,
        bounds.cx,
        bounds.cy,
        Math.max(bounds.w, bounds.h),
      )
      gradient.addColorStop(0, `rgba(${color.r}, ${color.g}, ${color.b}, ${0.35 * intensity})`)
      gradient.addColorStop(0.7, `rgba(${color.r}, ${color.g}, ${color.b}, ${0.1 * intensity})`)
      gradient.addColorStop(1, `rgba(${color.r}, ${color.g}, ${color.b}, 0)`)

      ctx.fillStyle = gradient
      ctx.beginPath()
      ctx.moveTo(poly[0].x * vw, poly[0].y * vh)
      for (let j = 1; j < poly.length; j++) {
        ctx.lineTo(poly[j].x * vw, poly[j].y * vh)
      }
      ctx.closePath()
      ctx.fill()

      // Bright outline
      ctx.strokeStyle = `rgba(${color.r}, ${color.g}, ${color.b}, ${0.95})`
      ctx.lineWidth = 2.5
      ctx.stroke()
    })
  }

  /**
   * Render fire bounding boxes with heat-based styling
   */
  renderFireBoxes(ctx, vw, vh, fireBoxes, intensity) {
    fireBoxes.forEach((box, idx) => {
      const b = box?.bbox
      if (!b) return
      const x = (b.x - b.w / 2) * vw
      const y = (b.y - b.h / 2) * vh
      const w = b.w * vw
      const h = b.h * vh
      this.renderFireBox(ctx, x, y, w, h, intensity)
    })
  }

  /**
   * Render a single fire box with glow and animations
   */
  renderFireBox(ctx, x, y, w, h, intensity) {
    const color = this.getHeatColor(intensity)

    // Animated pulsing effect
    const pulse = Math.sin(this.animationFrame * 0.05) * 0.2 + 0.8

    // Outer glow layers
    for (let i = 4; i >= 1; i--) {
      ctx.shadowColor = `rgba(${color.r}, ${color.g}, ${color.b}, ${(0.6 / i) * intensity})`
      ctx.shadowBlur = i * 4
      ctx.strokeStyle = `rgba(${color.r}, ${color.g}, ${color.b}, ${(0.15 / i) * pulse * intensity})`
      ctx.lineWidth = i * 1.5
      this.drawRoundedRect(ctx, x - i, y - i, w + i * 2, h + i * 2, 6)
      ctx.stroke()
    }

    // Main gradient fill
    const gradient = ctx.createLinearGradient(x, y, x, y + h)
    gradient.addColorStop(0, `rgba(${color.r}, ${color.g}, ${color.b}, ${0.25 * intensity})`)
    gradient.addColorStop(1, `rgba(${color.r}, ${color.g}, ${color.b}, ${0.1 * intensity})`)

    ctx.fillStyle = gradient
    ctx.shadowColor = `rgba(${color.r}, ${color.g}, ${color.b}, 0.5)`
    ctx.shadowBlur = 15
    this.drawRoundedRect(ctx, x, y, w, h, 6)
    ctx.fill()

    // Bright animated border
    ctx.strokeStyle = `rgba(${color.r}, ${color.g}, ${color.b}, ${0.9 * pulse})`
    ctx.lineWidth = 3
    ctx.shadowColor = `rgba(${color.r}, ${color.g}, ${color.b}, 0.8)`
    ctx.shadowBlur = 12
    this.drawRoundedRect(ctx, x, y, w, h, 6)
    ctx.stroke()

    // Corner accents (tactical look)
    this.drawCornerAccents(ctx, x, y, w, h, color, intensity * pulse)
  }

  /**
   * Render animated particles (fire sparks)
   */
  renderParticles(ctx, vw, vh) {
    this.particles = this.particles.filter((p) => p.life > 0)

    this.particles.forEach((p) => {
      p.life -= 0.02
      p.x += p.vx
      p.y += p.vy
      p.vy += 0.1 // gravity

      const alpha = Math.max(0, p.life)
      const size = p.size * alpha

      // Particle glow
      ctx.shadowColor = `rgba(${p.color.r}, ${p.color.g}, ${p.color.b}, ${alpha})`
      ctx.shadowBlur = size * 2

      ctx.fillStyle = `rgba(${p.color.r}, ${p.color.g}, ${p.color.b}, ${alpha})`
      ctx.beginPath()
      ctx.arc(p.x, p.y, size / 2, 0, Math.PI * 2)
      ctx.fill()
    })

    ctx.shadowColor = 'transparent'
  }

  /**
   * Spawn fire particles in detection zones
   */
  spawnFireParticles(vw, vh, frame, intensity) {
    const count = Math.ceil(this.config.particleCount * intensity)
    const fireBoxes = frame.fire_boxes || []
    const masks = frame.fire_masks || []

    let spawnAreas = []

    if (masks.length > 0) {
      spawnAreas = masks.map((poly) => {
        const bounds = this.getPolyBounds(poly, vw, vh)
        return {
          x: bounds.cx,
          y: bounds.cy,
          w: bounds.w,
          h: bounds.h,
        }
      })
    } else if (fireBoxes.length > 0) {
      spawnAreas = fireBoxes.map((box) => {
        const b = box?.bbox
        if (!b) return null
        return {
          x: (b.x - b.w / 2) * vw,
          y: (b.y - b.h / 2) * vh,
          w: b.w * vw,
          h: b.h * vh,
        }
      })
    } else if (frame.bbox && frame.fire) {
      const b = frame.bbox
      spawnAreas = [
        {
          x: (b.x - b.w / 2) * vw,
          y: (b.y - b.h / 2) * vh,
          w: b.w * vw,
          h: b.h * vh,
        },
      ]
    }

    spawnAreas.forEach((area) => {
      if (!area) return
      for (let i = 0; i < count; i++) {
        const color = this.getHeatColor(Math.random() * intensity)
        this.particles.push({
          x: area.x + Math.random() * area.w,
          y: area.y + Math.random() * area.h,
          vx: (Math.random() - 0.5) * 1.5,
          vy: (Math.random() - 1) * 0.8,
          size: Math.random() * 4 + 2,
          life: 1,
          color,
        })
      }
    })
  }

  /**
   * Render information labels with statistics
   */
  renderLabels(ctx, vw, vh, frame) {
    const labels = []

    // Fire label
    if (frame.fire) {
      const fireArea = Number(frame.fire_segment_area_pixels || 0)
      const intensity = Math.min(fireArea / 120000, 1)

      labels.push({
        text: `🔥 FIRE DETECTED`,
        subtext: `Area: ${Math.round(fireArea)} px`,
        x: 20,
        y: 40,
        color: this.getHeatColor(intensity),
      })
    }

    // Smoke label
    if (frame.smoke) {
      labels.push({
        text: `💨 SMOKE DETECTED`,
        subtext: 'Smoke zones identified',
        x: 20,
        y: frame.fire ? 105 : 40,
        color: { r: 129, g: 140, b: 248 },
      })
    }


    // Draw labels
    labels.forEach((label) => {
      this.drawLabel(ctx, label)
    })
  }

  /**
   * Draw a styled label with background and shadow
   */
  drawLabel(ctx, label) {
    const color = label.color

    // Label background - measure main text and add extra width for subtext
    ctx.font = 'bold 15px Inter, system-ui, sans-serif'
    const mainTextWidth = ctx.measureText(label.text).width
    const padding = 18
    let bgW = mainTextWidth + padding * 2 + 20
    
    // If there's subtext, ensure box is wide enough
    if (label.subtext) {
      ctx.font = '12px Inter, system-ui, sans-serif'
      const subtextWidth = ctx.measureText(label.subtext).width
      bgW = Math.max(bgW, subtextWidth + padding * 2 + 20)
    }

    const bgX = label.x - padding
    const bgY = label.y - 28
    const bgH = label.subtext ? 64 : 40

    // Glow background
    ctx.shadowColor = `rgba(${color.r}, ${color.g}, ${color.b}, 0.5)`
    ctx.shadowBlur = 12
    ctx.fillStyle = `rgba(10, 14, 26, 0.9)`
    this.drawRoundedRect(ctx, bgX, bgY, bgW, bgH, 8)
    ctx.fill()

    // Border
    ctx.strokeStyle = `rgba(${color.r}, ${color.g}, ${color.b}, 0.7)`
    ctx.lineWidth = 1.5
    this.drawRoundedRect(ctx, bgX, bgY, bgW, bgH, 8)
    ctx.stroke()

    // Main text
    ctx.shadowColor = 'transparent'
    ctx.fillStyle = `rgb(${color.r}, ${color.g}, ${color.b})`
    ctx.font = 'bold 15px Inter, system-ui, sans-serif'
    ctx.fillText(label.text, label.x, label.y)

    // Sub text
    if (label.subtext) {
      ctx.fillStyle = `rgba(${color.r}, ${color.g}, ${color.b}, 0.7)`
      ctx.font = '12px Inter, system-ui, sans-serif'
      ctx.fillText(label.subtext, label.x, label.y + 20)
    }

  }

  /**
   * Draw corner accents for tactical look
   */
  drawCornerAccents(ctx, x, y, w, h, color, intensity) {
    const accentLen = Math.min(w, h) * 0.15
    const accentWidth = 2

    ctx.strokeStyle = `rgba(${color.r}, ${color.g}, ${color.b}, ${0.8 * intensity})`
    ctx.lineWidth = accentWidth

    // Top-left
    ctx.beginPath()
    ctx.moveTo(x, y + accentLen)
    ctx.lineTo(x, y)
    ctx.lineTo(x + accentLen, y)
    ctx.stroke()

    // Top-right
    ctx.beginPath()
    ctx.moveTo(x + w - accentLen, y)
    ctx.lineTo(x + w, y)
    ctx.lineTo(x + w, y + accentLen)
    ctx.stroke()

    // Bottom-left
    ctx.beginPath()
    ctx.moveTo(x, y + h - accentLen)
    ctx.lineTo(x, y + h)
    ctx.lineTo(x + accentLen, y + h)
    ctx.stroke()

    // Bottom-right
    ctx.beginPath()
    ctx.moveTo(x + w - accentLen, y + h)
    ctx.lineTo(x + w, y + h)
    ctx.lineTo(x + w, y + h - accentLen)
    ctx.stroke()
  }

  /**
   * Get color based on heat intensity (cool to hot gradient)
   */
  getHeatColor(intensity) {
    // Cool (blue) -> Warm (orange/red) gradient
    if (intensity < 0.3) {
      // Blue
      return { r: 34, g: 211, b: 238 }
    } else if (intensity < 0.6) {
      // Yellow
      return { r: 251, g: 191, b: 36 }
    } else {
      // Red/Orange
      return { r: 239, g: 68, b: 68 }
    }
  }

  /**
   * Draw rounded rectangle
   */
  drawRoundedRect(ctx, x, y, w, h, radius) {
    ctx.beginPath()
    ctx.moveTo(x + radius, y)
    ctx.lineTo(x + w - radius, y)
    ctx.quadraticCurveTo(x + w, y, x + w, y + radius)
    ctx.lineTo(x + w, y + h - radius)
    ctx.quadraticCurveTo(x + w, y + h, x + w - radius, y + h)
    ctx.lineTo(x + radius, y + h)
    ctx.quadraticCurveTo(x, y + h, x, y + h - radius)
    ctx.lineTo(x, y + radius)
    ctx.quadraticCurveTo(x, y, x + radius, y)
    ctx.closePath()
  }

  /**
   * Get bounding box of polygon
   */
  getPolyBounds(poly, vw, vh) {
    let minX = Infinity,
      maxX = -Infinity,
      minY = Infinity,
      maxY = -Infinity

    poly.forEach((p) => {
      const x = p.x * vw
      const y = p.y * vh
      minX = Math.min(minX, x)
      maxX = Math.max(maxX, x)
      minY = Math.min(minY, y)
      maxY = Math.max(maxY, y)
    })

    return {
      cx: (minX + maxX) / 2,
      cy: (minY + maxY) / 2,
      w: maxX - minX,
      h: maxY - minY,
    }
  }

  /**
   * Render continuous system scanning status
   */
  renderSystemStatus(ctx, vw, vh, frame) {
    const isScanning = frame?.system === 'scanning' || (!frame.fire && !frame.smoke)
    if (!isScanning) return

    ctx.save()
    const color = { r: 6, g: 182, b: 212 } // Cyan
    const alpha = Math.sin(this.animationFrame * 0.05) * 0.2 + 0.4
    
    // Top-right status
    ctx.font = 'bold 10px monospace'
    ctx.fillStyle = `rgba(${color.r}, ${color.g}, ${color.b}, ${alpha})`
    ctx.textAlign = 'right'
    ctx.fillText('SYSTEM_ACTIVE // SCANNING_FEED...', vw - 20, 30)
    
    // Reticle in center
    const cx = vw / 2
    const cy = vh / 2
    const size = 30
    ctx.strokeStyle = `rgba(${color.r}, ${color.g}, ${color.b}, ${alpha * 0.5})`
    ctx.lineWidth = 1
    
    ctx.beginPath(); ctx.moveTo(cx - size, cy); ctx.lineTo(cx + size, cy); ctx.stroke()
    ctx.beginPath(); ctx.moveTo(cx, cy - size); ctx.lineTo(cx, cy + size); ctx.stroke()
    
    // Scanline
    const scanY = (this.animationFrame * 2) % vh
    ctx.strokeStyle = `rgba(${color.r}, ${color.g}, ${color.b}, 0.1)`
    ctx.beginPath(); ctx.moveTo(0, scanY); ctx.lineTo(vw, scanY); ctx.stroke()
    
    ctx.restore()
  }

  /**
   * Clear overlay
   */
  clear() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height)
  }
}

export default DetectionOverlay
