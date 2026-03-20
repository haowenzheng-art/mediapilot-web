import { useEffect, useRef } from 'react'

function SpaceCyberBackground() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    let animationId

    // 设置canvas尺寸
    const resize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    resize()
    window.addEventListener('resize', resize)

    // 星星粒子
    const stars = Array.from({ length: 200 }, () => ({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      size: Math.random() * 2 + 0.5,
      speed: Math.random() * 0.5 + 0.1,
      opacity: Math.random() * 0.8 + 0.2,
    }))

    // 星云效果
    const nebulae = [
      { x: 0.2, y: 0.3, radius: 200, color: 'rgba(0, 238, 255, 0.15)' },
      { x: 0.7, y: 0.6, radius: 250, color: 'rgba(255, 0, 255, 0.1)' },
      { x: 0.5, y: 0.8, radius: 180, color: 'rgba(0, 255, 200, 0.12)' },
    ]

    // 脉冲星
    const pulsars = Array.from({ length: 5 }, () => ({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      phase: Math.random() * Math.PI * 2,
      speed: Math.random() * 0.02 + 0.01,
    }))

    const animate = () => {
      ctx.fillStyle = '#0f2027'
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      // 绘制星云
      nebulae.forEach(nebula => {
        const gradient = ctx.createRadialGradient(
          nebula.x * canvas.width, nebula.y * canvas.height, 0,
          nebula.x * canvas.width, nebula.y * canvas.height, nebula.radius
        )
        gradient.addColorStop(0, nebula.color)
        gradient.addColorStop(1, 'transparent')
        ctx.fillStyle = gradient
        ctx.fillRect(0, 0, canvas.width, canvas.height)
      })

      // 更新和绘制星星
      stars.forEach(star => {
        star.y += star.speed
        if (star.y > canvas.height) {
          star.y = 0
          star.x = Math.random() * canvas.width
        }

        ctx.beginPath()
        ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(255, 255, 255, ${star.opacity})`
        ctx.fill()
      })

      // 绘制脉冲星
      pulsars.forEach(pulsar => {
        pulsar.phase += pulsar.speed
        const pulse = Math.sin(pulsar.phase) * 0.5 + 0.5

        const gradient = ctx.createRadialGradient(
          pulsar.x, pulsar.y, 0,
          pulsar.x, pulsar.y, 30 + pulse * 20
        )
        gradient.addColorStop(0, `rgba(0, 238, 255, ${0.8 + pulse * 0.2})`)
        gradient.addColorStop(0.5, `rgba(0, 238, 255, ${0.3 + pulse * 0.3})`)
        gradient.addColorStop(1, 'transparent')

        ctx.beginPath()
        ctx.arc(pulsar.x, pulsar.y, 30 + pulse * 20, 0, Math.PI * 2)
        ctx.fillStyle = gradient
        ctx.fill()
      })

      animationId = requestAnimationFrame(animate)
    }

    animate()

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

export default SpaceCyberBackground
