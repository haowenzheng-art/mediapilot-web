/**
 * 功能卡片组件
 *
 * 显示 Hero 区域的功能特性
 */
import TabButton from './TabButton'

export default function FeatureCard({ features, onFeatureClick }) {
  return (
    <div className="feature-cards">
      {features.map((feature, idx) => (
        <TabButton
          key={idx}
          icon={feature.icon}
          title={feature.title}
          desc={feature.desc}
          onClick={() => onFeatureClick(feature.tab)}
        />
      ))}
    </div>
  )
}
