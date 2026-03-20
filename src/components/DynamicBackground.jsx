import { useTheme } from '../contexts/ThemeContext'
import SpaceCyberBackground from './SpaceCyberBackground'
import ChineseStyleBackground from './ChineseStyleBackground'
import CyberpunkBackground from './CyberpunkBackground'
import PixarBackground from './PixarBackground'
import AnimeBackground from './AnimeBackground'
import AbstractBackground from './AbstractBackground'

function DynamicBackground() {
  const { currentThemeId } = useTheme()

  switch (currentThemeId) {
    case 'spaceCyber':
      return <SpaceCyberBackground />
    case 'chineseStyle':
      return <ChineseStyleBackground />
    case 'cyberpunk':
      return <CyberpunkBackground />
    case 'pixar':
      return <PixarBackground />
    case 'anime':
      return <AnimeBackground />
    case 'abstract':
      return <AbstractBackground />
    default:
      return null
  }
}

export default DynamicBackground
