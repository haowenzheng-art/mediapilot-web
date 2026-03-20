import { useEffect, useRef } from 'react'

function AnimeBackground() {
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

    const sakuraPetals = Array.from({ length: 25 }, (_, i) => ({
      x: Math.random() * window.innerWidth,
      y: -50 - Math.random() * window.innerHeight,
      size: 12 + Math.random() * 12,
      speed: 1 + Math.random() * 2,
      rotation: Math.random() * Math.PI * 2,
      rotationSpeed: (Math.random() - 0.5) * 0.05,
      swayPhase: Math.random() * Math.PI * 2,
      swayAmount: 0.5 + Math.random() * 1.5,
      swaySpeed: 0.02 + Math.random() * 0.02,
      opacity: 0.7 + Math.random() * 0.3,
    }))

    const sparkles = Array.from({ length: 30 }, () => ({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      size: 2 + Math.random() * 4,
      phase: Math.random() * Math.PI * 2,
      speed: 0.03 + Math.random() * 0.02,
    }))

    const lightSpots = [
      { x: 0.2, y: 0.15, size: 150, phase: 0 },
      { x: 0.85, y: 0.6, size: 120, phase: Math.PI / 2 },
    ]

    const drawSakuraPetal = (x, y, size, rotation, opacity) => {
      ctx.save()
      ctx.translate(x, y)
      ctx.rotate(rotation)
      ctx.scale(1, 0.7)

      ctx.fillStyle = `rgba(255, 182, 193, ${opacity})`
      ctx.beginPath()
      for (let i = 0; i < 5; i++) {
        const angle = (i * Math.PI * 2) / 5 - Math.PI / 2
        ctx.ellipse(
          Math.cos(angle) * size * 0.4,
          Math.sin(angle) * size * 0.4,
          size * 0.35,
          size * 0.5,
          angle,
          0,
          Math.PI * 2
        )
      }
      ctx.fill()

      ctx.fillStyle = `rgba(255, 255, 150, ${opacity * 0.5})`
      ctx.beginPath()
      ctx.arc(0, 0, size * 0.15, 0, Math.PI * 2)
      ctx.fill()

      ctx.restore()
    }

    const drawSparkle = (x, y, size, intensity) => {
      const gradient = ctx.createRadialGradient(x, y, 0, x, y, size * 2)
      gradient.addColorStop(0, `rgba(255, 255, 255, ${intensity})`)
      gradient.addColorStop(0.5, `rgba(255, 200, 220, ${intensity * 0.5})`)
      gradient.addColorStop(1, 'transparent')
      ctx.fillStyle = gradient
      ctx.beginPath()
      ctx.arc(x, y, size * 2, 0, Math.PI * 2)
      ctx.fill()

      ctx.strokeStyle = `rgba(255, 255, 255, ${intensity * 0.8})`
      ctx.lineWidth = 1
      for (let i = 0; i < 4; i++) {
        const angle = (i * Math.PI) / 2
        ctx.beginPath()
        ctx.moveTo(x, y)
        ctx.lineTo(x + Math.cos(angle) * size * 3, y + Math.sin(angle) * size * 3)
        ctx.stroke()
      }
    }

    const drawLightSpot = (x, y, size, intensity) => {
      const gradient = ctx.createRadialGradient(x, y, 0, x, y, size)
      gradient.addColorStop(0, `rgba(255, 255, 255, ${intensity * 0.3})`)
      gradient.addColorStop(0.3, `rgba(255, 220, 240, ${intensity * 0.15})`)
      gradient.addColorStop(1, 'transparent')
      ctx.fillStyle = gradient
      ctx.beginPath()
      ctx.arc(x, y, size, 0, Math.PI * 2)
      ctx.fill()
    }

    const animate = (time) => {
      const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height)
      gradient.addColorStop(0, '#ffe4ec')
      gradient.addColorStop(0.5, '#ffd1dc')
      gradient.addColorStop(1, '#ffbcd4')
      ctx.fillStyle = gradient
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      lightSpots.forEach(spot => {
        const intensity = Math.sin(time * 0.001 + spot.phase) * 0.3 + 0.7
        drawLightSpot(
          spot.x * canvas.width,
          spot.y * canvas.height,
          spot.size,
          intensity
        )
      })

      sparkles.forEach(sparkle => {
        const intensity = Math.sin(time * sparkle.speed + sparkle.phase) * 0.5 + 0.5
        drawSparkle(sparkle.x, sparkle.y, sparkle.size, intensity)
      })

      sakuraPetals.forEach(petal => {
        petal.y += petal.speed
        petal.x += Math.sin(time * petal.swaySpeed + petal.swayPhase) * petal.swayAmount
        petal.rotation += petal.rotationSpeed

        if (petal.y > canvas.height + 50) {
          petal.y = -50
          petal.x = Math.random() * canvas.width
          petal.swayPhase = Math.random() * Math.PI * 2
        }

        drawSakuraPetal(petal.x, petal.y, petal.size, petal.rotation, petal.opacity)
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

export default AnimeBackground
