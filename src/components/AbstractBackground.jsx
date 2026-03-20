import { useEffect, useRef } from 'react'

function AbstractBackground() {
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

    const circles = Array.from({ length: 4 }, (_, i) => ({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      radius: 100 + Math.random() * 150,
      color: i % 2 === 0 ? 'rgba(0, 255, 136, 0.15)' : 'rgba(233, 69, 96, 0.15)',
      speedX: (Math.random() - 0.5) * 0.3,
      speedY: (Math.random() - 0.5) * 0.3,
      phase: Math.random() * Math.PI * 2,
    }))

    const squares = Array.from({ length: 3 }, (_, i) => ({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      size: 60 + Math.random() * 80,
      rotation: Math.random() * Math.PI * 2,
      rotationSpeed: (Math.random() - 0.5) * 0.01,
      color: i === 0 ? 'rgba(255, 204, 0, 0.12)' : 'rgba(0, 255, 136, 0.12)',
      speedX: (Math.random() - 0.5) * 0.2,
      speedY: (Math.random() - 0.5) * 0.2,
    }))

    const triangles = Array.from({ length: 3 }, (_, i) => ({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      size: 50 + Math.random() * 70,
      rotation: Math.random() * Math.PI * 2,
      rotationSpeed: (Math.random() - 0.5) * 0.015,
      color: i === 0 ? 'rgba(233, 69, 96, 0.12)' : 'rgba(255, 204, 0, 0.12)',
      speedX: (Math.random() - 0.5) * 0.25,
      speedY: (Math.random() - 0.5) * 0.25,
    }))

    const lines = Array.from({ length: 5 }, () => ({
      x1: Math.random() * window.innerWidth,
      y1: Math.random() * window.innerHeight,
      x2: Math.random() * window.innerWidth,
      y2: Math.random() * window.innerHeight,
      color: 'rgba(0, 255, 136, 0.2)',
      phase: Math.random() * Math.PI * 2,
    }))

    const particles = Array.from({ length: 40 }, () => ({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      size: 2 + Math.random() * 4,
      speedX: (Math.random() - 0.5) * 0.8,
      speedY: (Math.random() - 0.5) * 0.8,
      color: Math.random() > 0.5 ? '#00ff88' : '#e94560',
      trail: [],
    }))

    const drawTriangle = (x, y, size, rotation, color) => {
      ctx.save()
      ctx.translate(x, y)
      ctx.rotate(rotation)
      ctx.fillStyle = color
      ctx.beginPath()
      ctx.moveTo(0, -size)
      ctx.lineTo(size * 0.866, size * 0.5)
      ctx.lineTo(-size * 0.866, size * 0.5)
      ctx.closePath()
      ctx.fill()
      ctx.restore()
    }

    const animate = (time) => {
      const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height)
      gradient.addColorStop(0, '#1a1a2e')
      gradient.addColorStop(0.5, '#16213e')
      gradient.addColorStop(1, '#0f3460')
      ctx.fillStyle = gradient
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      circles.forEach(circle => {
        const pulse = Math.sin(time * 0.001 + circle.phase) * 0.2 + 1
        const gradient = ctx.createRadialGradient(
          circle.x, circle.y, 0,
          circle.x, circle.y, circle.radius * pulse
        )
        gradient.addColorStop(0, circle.color)
        gradient.addColorStop(1, 'transparent')
        ctx.fillStyle = gradient
        ctx.beginPath()
        ctx.arc(circle.x, circle.y, circle.radius * pulse, 0, Math.PI * 2)
        ctx.fill()

        circle.x += circle.speedX
        circle.y += circle.speedY
        if (circle.x < -circle.radius || circle.x > canvas.width + circle.radius) circle.speedX *= -1
        if (circle.y < -circle.radius || circle.y > canvas.height + circle.radius) circle.speedY *= -1
      })

      squares.forEach(square => {
        ctx.save()
        ctx.translate(square.x, square.y)
        ctx.rotate(square.rotation)
        ctx.fillStyle = square.color
        ctx.fillRect(-square.size / 2, -square.size / 2, square.size, square.size)
        ctx.restore()

        square.rotation += square.rotationSpeed
        square.x += square.speedX
        square.y += square.speedY
        if (square.x < -square.size || square.x > canvas.width + square.size) square.speedX *= -1
        if (square.y < -square.size || square.y > canvas.height + square.size) square.speedY *= -1
      })

      triangles.forEach(triangle => {
        drawTriangle(triangle.x, triangle.y, triangle.size, triangle.rotation, triangle.color)
        triangle.rotation += triangle.rotationSpeed
        triangle.x += triangle.speedX
        triangle.y += triangle.speedY
        if (triangle.x < -triangle.size || triangle.x > canvas.width + triangle.size) triangle.speedX *= -1
        if (triangle.y < -triangle.size || triangle.y > canvas.height + triangle.size) triangle.speedY *= -1
      })

      lines.forEach(line => {
        const pulse = Math.sin(time * 0.002 + line.phase) * 0.3 + 0.7
        ctx.strokeStyle = line.color.replace('0.2', pulse.toFixed(2))
        ctx.lineWidth = 2
        ctx.beginPath()
        ctx.moveTo(line.x1, line.y1)
        ctx.lineTo(line.x2, line.y2)
        ctx.stroke()
      })

      particles.forEach(particle => {
        particle.trail.push({ x: particle.x, y: particle.y })
        if (particle.trail.length > 10) particle.trail.shift()

        particle.trail.forEach((pos, idx) => {
          const alpha = idx / particle.trail.length * 0.5
          ctx.fillStyle = particle.color + Math.floor(alpha * 255).toString(16).padStart(2, '0')
          ctx.beginPath()
          ctx.arc(pos.x, pos.y, particle.size * (idx / particle.trail.length), 0, Math.PI * 2)
          ctx.fill()
        })

        ctx.fillStyle = particle.color
        ctx.beginPath()
        ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2)
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

export default AbstractBackground
