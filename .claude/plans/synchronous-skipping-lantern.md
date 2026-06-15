# MediaPilot UI 现代化改造计划

## Context
当前 MediaPilot 网页 UI 存在以下问题：
1. 输入框太小，不适合长文本输入
2. 设计风格有"廉价小程序感"，缺乏现代科技网站质感
3. 过度使用卡片边框，视觉效果僵硬

用户选择了 **Notion 风格** + **全屏式编辑器** 作为改造方向。

---

## 设计方向：Notion 风格 + 全屏式编辑器

### 核心设计原则
1. **干净极简**：白色/浅灰背景，移除多余装饰
2. **灰度层次**：用不同灰度区分内容，而非彩色
3. **实用主义**：功能优先，淡化装饰元素
4. **沉浸式输入**：大输入区占据主要视觉空间

### 色彩系统
```css
/* Notion 风格色彩 */
--bg-primary: #ffffff
--bg-secondary: #f7f7f5
--bg-tertiary: #efefef
--text-primary: #37352f
--text-secondary: #787774
--text-tertiary: #9b9a97
--border-color: #e0e0e0
--hover-bg: #efefef
--active-bg: #dcdcdc

/* 功能色（保持克制） */
--primary: #2383e2
--primary-hover: #1a6cb8
--success: #0f7b6c
--warning: #c97a16
--error: #e03e3f
```

---

## 改造范围

### 阶段 1：新建 Notion 主题系统
**文件：** `web/src/index.css`

1. 移除所有主题相关的复杂动画和渐变背景
2. 新增 Notion 主题色彩定义
3. 简化全局样式，移除阴影和发光效果
4. 优化排版：字体大小、行高、字间距

### 阶段 2：新建全屏式输入组件
**新建文件：** `web/src/components/FullscreenEditor.jsx`

```jsx
// 全屏编辑器组件特性：
- 占据整个视口高度
- 左侧大输入区域（70%）
- 右侧预览区域（30%），可折叠
- 底部固定操作栏
- 支持键盘快捷键（Ctrl/Cmd + Enter 提交）
- 行号显示
- 字数统计
```

### 阶段 3：改造页面组件（按优先级）

#### 3.1 ScriptPage.jsx（脚本生成）
- 用 FullscreenEditor 替换原有布局
- 简化平台/时长/风格选择器为简洁的胶囊按钮
- 移除卡片容器，改用干净的边框分割

#### 3.2 HotSearchPage.jsx（热点搜索）
- 同上使用 FullscreenEditor
- 移除装饰性图标

#### 3.3 VideoAnalysisPage.jsx（视频分析）
- 保留左右分栏但简化样式
- 输入框改用简洁样式

#### 3.4 TranscriptionPage.jsx（语音转写）
- 上传区域改用拖拽样式（类似 Notion 文件上传）

#### 3.5 其他页面
- DataImportPage.jsx
- CalendarPage.jsx
- TemplatesPage.jsx
- CompetitorsPage.jsx
- AnalyticsPage.jsx
- HistoryPage.jsx
- SettingsPage.jsx

### 阶段 4：简化 Hero 首页
**文件：** `web/src/pages/HeroSection.jsx`

- 移除花哨的动画背景
- 简化为干净的文字排版
- Logo 和 Slogan 居中，大标题
- 功能卡片改为简洁的列表

### 阶段 5：更新导航和布局组件
**文件：**
- `web/src/components/layout/Header.jsx`
- `web/src/components/layout/Tabs.jsx`

- Header：简化为顶部细线条，Logo 左对齐
- Tabs：改为 Notion 风格的横向列表，无下划线

### 阶段 6：移除不必要的组件
**删除/禁用：**
- 所有动态背景组件（SpaceCyberBackground、CyberpunkBackground 等）
- DynamicBackground 组件（替换为静态渐变）
- ThemeSwitcher 组件（暂时禁用多主题切换）

---

## 关键设计细节

### 输入框样式
```css
.notion-input {
  background: transparent;
  border: none;
  font-size: 16px;
  line-height: 1.8;
  color: var(--text-primary);
  resize: none;
  outline: none;
  padding: 24px;
}

.notion-input::placeholder {
  color: var(--text-tertiary);
}
```

### 按钮样式
```css
.notion-btn {
  background: var(--primary);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}

.notion-btn:hover {
  background: var(--primary-hover);
}
```

### 分割线
```css
.notion-divider {
  border: none;
  border-top: 1px solid var(--border-color);
  margin: 24px 0;
}
```

---

## 执行顺序

| 阶段 | 任务 | 预估时间 |
|------|------|----------|
| 1 | 新建 Notion 主题系统 | 30min |
| 2 | 创建 FullscreenEditor 组件 | 45min |
| 3.1 | 改造 ScriptPage | 30min |
| 3.2 | 改造 HotSearchPage | 20min |
| 3.3 | 改造 VideoAnalysisPage | 25min |
| 3.4 | 改造 TranscriptionPage | 20min |
| 3.5 | 改造其他页面 | 60min |
| 4 | 简化 Hero 首页 | 20min |
| 5 | 更新导航和布局 | 20min |
| 6 | 清理旧组件 | 15min |
| **总计** | | **~4.5小时** |

---

## 验收标准

1. 输入框高度至少 60vh，宽度充足
2. 整体色调为白/灰，无炫彩效果
3. 页面加载快，无复杂动画
4. 所有功能正常工作
5. 响应式布局在移动端也能正常显示
6. 代码可维护性良好

---

## 回滚方案

如需回滚，使用 Git：
```bash
git checkout HEAD -- web/src/
```
或保留原文件作为备份，在改造前复制到 `web/src.backup/`
