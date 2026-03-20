import { useEffect, useRef } from 'react'

function CyberpunkBackground() {
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

    const gridLines = []
    const spacing = 50
    for (let x = 0; x < window.innerWidth + spacing; x += spacing) {
      gridLines.push({ x, type: 'vertical' })
    }
    for (let y = 0; y < window.innerHeight + spacing; y += spacing) {
      gridLines.push({ y, type: 'horizontal' })
    }

    const scanline = { y: 0, speed: 2 }

    const glitches = Array.from({ length: 3 }, (_, i) => ({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      width: 100 + Math.random() * 200,
      height: 2 + Math.random() * 4,
      speed: 1 + Math.random() * 2,
      offset: Math.random() * 100,
      color: i % 2 === 0 ? 'rgba(255, 0, 110, 0.3)' : 'rgba(0, 245, 212, 0.3)',
    }))

    const neonParticles = Array.from({ length: 30 }, () => ({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      size: 2 + Math.random() * 3,
      speedX: (Math.random() - 0.5) * 0.5,
      speedY: (Math.random() - 0.5) * 0.5,
      color: Math.random() > 0.5 ? '#ff006e' : '#00f5d4',
      phase: Math.random() * Math.PI * 2,
    }))

    const animate = (time) => {
      ctx.fillStyle = '#0d0221'
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      ctx.strokeStyle = 'rgba(255, 0, 110, 0.1)'
      ctx.lineWidth = 1
      gridLines.forEach(line => {
        ctx.beginPath()
        if (line.type === 'vertical') {
          ctx.moveTo(line.x, 0)
          ctx.lineTo(line.x, canvas.height)
        } else {
          ctx.moveTo(0, line.y)
          ctx.lineTo(canvas.width, line.y)
        }
        ctx.stroke()
      })

      ctx.fillStyle = 'rgba(0, 245, 212, 0.03)'
      ctx.fillRect(0, scanline.y, canvas.width, 3)
      scanline.y += scanline.speed
      if (scanline.y > canvas.height) scanline.y = -3

      glitches.forEach(glitch => {
        const pulse = Math.sin(time * 0.01 + glitch.offset) * 0.5 + 0.5
        ctx.fillStyle = glitch.color
        ctx.fillRect(
          glitch.x + pulse * 20,
          glitch.y,
          glitch.width,
          glitch.height
        )
        glitch.y += glitch.speed
        if (glitch.y > canvas.height) {
          glitch.y = -10
          glitch.x = Math.random() * canvas.width
        }
      })

      neonParticles.forEach(particle => {
        const glow = Math.sin(time * 0.005 + particle.phase) * 0.5 + 0.5
        const gradient = ctx.createRadialGradient(
          particle.x, particle.y, 0,
          particle.x, particle.y, particle.size * (2 + glow)
        )
        gradient.addColorStop(0, particle.color)
        gradient.addColorStop(0.5, `${particle.color}88`)
        gradient.addColorStop(1, 'transparent')
        ctx.fillStyle = gradient
        ctx.beginPath()
        ctx.arc(particle.x, particle.y, particle.size * (2 + glow), 0, Math.PI * 2)
        ctx.fill()

        particle.x += particle.speedX
        particle.y += particle.speedY
        if (particle.x < 0 || particle.x > canvas.width) particle.speedX *= -1
        if (particle.y < 0 || particle.y > canvas.height) particle.speedY *= -1
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

export default CyberpunkBackground
