import { motion } from 'framer-motion'

export default function PageContainer({ children, title, description }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="page-container"
    >
      {title && (
        <div className="page-header">
          <h1 className="page-title">{title}</h1>
          {description && (
            <p className="page-description">{description}</p>
          )}
        </div>
      )}

      <div className="page-body">
        {children}
      </div>
    </motion.div>
  )
}
