import { useEffect, useRef } from 'react'

function ChineseStyleBackground() {
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

    // 墨迹粒子
    const inkBlobs = Array.from({ length: 8 }, () => ({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      radius: 50 + Math.random() * 100,
      opacity: 0.03 + Math.random() * 0.05,
      speedX: (Math.random() - 0.5) * 0.2,
      speedY: (Math.random() - 0.5) * 0.2,
      phase: Math.random() * Math.PI * 2,
    }))

    const drawInkBlob = (blob, time) => {
      const pulse = Math.sin(blob.phase + time * 0.001) * 0.2 + 1
      const radius = blob.radius * pulse

      const gradient = ctx.createRadialGradient(
        blob.x, blob.y, 0,
        blob.x, blob.y, radius
      )
      gradient.addColorStop(0, `rgba(139, 69, 19, ${blob.opacity})`)
      gradient.addColorStop(0.5, `rgba(139, 69, 19, ${blob.opacity * 0.5})`)
      gradient.addColorStop(1, 'transparent')

      ctx.beginPath()
      ctx.arc(blob.x, blob.y, radius, 0, Math.PI * 2)
      ctx.fillStyle = gradient
      ctx.fill()
    }

    const drawInkTexture = () => {
      // 宣纸纹理
      for (let i = 0; i < 50; i++) {
        const x = Math.random() * canvas.width
        const y = Math.random() * canvas.height
        const size = Math.random() * 3 + 1
        const opacity = Math.random() * 0.02

        ctx.beginPath()
        ctx.arc(x, y, size, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(139, 69, 19, ${opacity})`
        ctx.fill()
      }
    }

    const animate = (time) => {
      // 米色背景
      ctx.fillStyle = '#fdf6e3'
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      // 绘制宣纸纹理
      drawInkTexture()

      // 更新和绘制墨迹
      inkBlobs.forEach(blob => {
        blob.x += blob.speedX
        blob.y += blob.speedY
        blob.phase += 0.01

        // 边界反弹
        if (blob.x < -100 || blob.x > canvas.width + 100) blob.speedX *= -1
        if (blob.y < -100 || blob.y > canvas.height + 100) blob.speedY *= -1

        drawInkBlob(blob, time)
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

export default ChineseStyleBackground
