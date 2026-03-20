import { useEffect, useRef } from 'react'

function PixarBackground() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    let animationId

    const resize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    resize()
    window.addEventListener('resize', resize)

    const clouds = Array.from({ length: 5 }, (_, i) => ({
      x: Math.random() * window.innerWidth,
      y: 100 + Math.random() * 300,
      baseY: 100 + Math.random() * 300,
      scale: 0.8 + Math.random() * 1.2,
      speed: 0.2 + Math.random() * 0.3,
      opacity: 0.6 + Math.random() * 0.3,
      phase: Math.random() * Math.PI * 2,
    }))

    const drawCloud = (x, y, scale, opacity) => {
      ctx.fillStyle = `rgba(255, 255, 255, ${opacity})`
      ctx.beginPath()
      ctx.arc(x, y, 30 * scale, 0, Math.PI * 2)
      ctx.arc(x + 25 * scale, y - 10 * scale, 25 * scale, 0, Math.PI * 2)
      ctx.arc(x + 50 * scale, y, 30 * scale, 0, Math.PI * 2)
      ctx.arc(x + 25 * scale, y + 10 * scale, 20 * scale, 0, Math.PI * 2)
      ctx.fill()
    }

    const rainbows = []
    const rainbowColors = [
      '#ff6b35',
      '#f7931e',
      '#ffd700',
      '#6bcb77',
      '#4d96ff',
      '#9b59b6',
    ]

    const stars = Array.from({ length: 20 }, () => ({
      x: Math.random() * window.innerWidth,
      y: 50 + Math.random() * 200,
      size: 3 + Math.random() * 5,
      phase: Math.random() * Math.PI * 2,
      speed: 0.02 + Math.random() * 0.03,
    }))

    const animate = (time) => {
      const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height)
      gradient.addColorStop(0, '#87ceeb')
      gradient.addColorStop(0.5, '#98d8ee')
      gradient.addColorStop(1, '#b0e0e6')
      ctx.fillStyle = gradient
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      stars.forEach(star => {
        const glow = Math.sin(time * star.speed + star.phase) * 0.3 + 0.7
        ctx.save()
        ctx.translate(star.x, star.y)
        ctx.rotate(time * 0.001 + star.phase)
        ctx.fillStyle = `rgba(255, 215, 0, ${glow * 0.8})`
        ctx.beginPath()
        for (let i = 0; i < 5; i++) {
          const angle = (i * Math.PI * 2) / 5 - Math.PI / 2
          const innerAngle = angle + Math.PI / 5
          ctx.lineTo(Math.cos(angle) * star.size, Math.sin(angle) * star.size)
          ctx.lineTo(Math.cos(innerAngle) * star.size * 0.4, Math.sin(innerAngle) * star.size * 0.4)
        }
        ctx.closePath()
        ctx.fill()
        ctx.restore()
      })

      if (time % 10000 < 5000 && rainbows.length === 0) {
        rainbows.push({
          x: canvas.width * 0.5,
          y: canvas.height * 0.3,
          radius: Math.min(canvas.width, canvas.height) * 0.4,
          opacity: 0,
          fadingIn: true,
        })
      }

      rainbows.forEach((rainbow, idx) => {
        if (rainbow.fadingIn && rainbow.opacity < 0.6) {
          rainbow.opacity += 0.005
        } else if (!rainbow.fadingIn && rainbow.opacity > 0) {
          rainbow.opacity -= 0.005
        } else if (rainbow.opacity >= 0.6) {
          rainbow.fadingIn = false
        }

        if (rainbow.opacity <= 0 && !rainbow.fadingIn) {
          rainbows.splice(idx, 1)
          return
        }

        rainbowColors.forEach((color, i) => {
          ctx.strokeStyle = `${color}${Math.floor(rainbow.opacity * 255).toString(16).padStart(2, '0')}`
          ctx.lineWidth = 15
          ctx.beginPath()
          ctx.arc(rainbow.x, rainbow.y + rainbow.radius, rainbow.radius - i * 15, Math.PI, 0)
          ctx.stroke()
        })
      })

      clouds.forEach(cloud => {
        cloud.x += cloud.speed
        cloud.y = cloud.baseY + Math.sin(time * 0.001 + cloud.phase) * 10

        if (cloud.x > canvas.width + 200) {
          cloud.x = -200
        }

        drawCloud(cloud.x, cloud.y, cloud.scale, cloud.opacity)
      })

      animationId = requestAnimationFrame(animate)
    }

    animate(0)

    return () => {
      window.removeEventListener('resize', resize)
      cancelAnimationFrame(animationId)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: -1,
        pointerEvents: 'none',
      }}
    />
  )
}

export default PixarBackground
