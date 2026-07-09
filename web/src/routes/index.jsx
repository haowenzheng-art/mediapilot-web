/**
 * 路由配置
 *
 * 定义应用的标签页路由和对应组件
 */
import { ROUTE_PATHS } from './route_paths'

export const TABS = [
  { id: ROUTE_PATHS.TRENDING, name: '热点搜索', icon: '🔥' },
  { id: ROUTE_PATHS.COPYWRITING, name: '口播文案', icon: '🎤' },
  { id: ROUTE_PATHS.SHOOT_SCRIPT, name: '拍摄脚本', icon: '🎬' },
  { id: ROUTE_PATHS.SUBSCRIPTION, name: '话题订阅', icon: '📬' },
  { id: ROUTE_PATHS.CONTENT_LIBRARY, name: '内容库', icon: '📚' },
  { id: ROUTE_PATHS.TRANSCRIPTION, name: '智能转录', icon: '🎙️' },
  { id: ROUTE_PATHS.VIDEO_ANALYSIS, name: '视频分析', icon: '📺' },
  { id: ROUTE_PATHS.VIDEO_EDIT, name: 'AI 剪辑', icon: '✂️' },
]

export { ROUTE_PATHS }
export default TABS
