/**
 * 标签按钮组件
 *
 * 用于 Hero 区域的功能卡片，点击后跳转到对应标签页
 */
import { motion } from 'framer-motion'

export default function TabButton({ icon, title, desc, onClick }) {
  return (
    <motion.div
      className="feature-card card"
      whileHover={{
        scale: 1.02,
        y: -5,
      }}
      transition={{ type: 'spring', stiffness: 400, damping: 20 }}
      onClick={onClick}
    >
      <span className="feature-icon">{icon}</span>
      <h3 className="feature-title">{title}</h3>
      <p className="feature-desc">{desc}</p>
    </motion.div>
  )
}
