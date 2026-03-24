# MediaPilot 数据监控插件

## 安装步骤

### 1. 准备图标文件

由于无法直接生成PNG图标，请执行以下步骤之一：

**方案A：使用在线工具**
1. 访问 https://www.favicon-generator.org/
2. 上传 `icon128.svg`
3. 下载生成的 16x16, 48x48, 128x128 PNG 文件
4. 重命名为 `icon16.png`, `icon48.png`, `icon128.png`
5. 放到 extension 目录下

**方案B：临时使用相同大小的PNG**
1. 任意找一张 128x128 的 PNG 图片
2. 复制三份，分别命名为 `icon16.png`, `icon48.png`, `icon128.png`
3. 放到 extension 目录下

### 2. 加载插件到 Chrome

1. 打开 Chrome 浏览器
2. 访问 `chrome://extensions/`
3. 打开右上角「开发者模式」
4. 点击「加载已解压的扩展程序」
5. 选择 extension 目录

### 3. 使用插件

1. 访问小红书创作者中心或笔记页面
2. 点击浏览器工具栏的插件图标
3. 配置 MediaPilot 网站地址（如 http://localhost:5173）
4. 点击「抓取当前数据」
5. 数据会自动复制到剪贴板，可以粘贴到 MediaPilot

## 功能说明

- 支持小红书笔记页面数据抓取
- 支持小红书创作者中心数据抓取
- 自动识别页面类型
- 数据实时预览
- 历史记录保存
- 支持同步到 MediaPilot 网站（需要 API 支持）

## 文件结构

```
extension/
├── manifest.json      # 插件配置文件
├── popup.html        # 弹出窗口 UI
├── popup.js          # 弹出窗口逻辑
├── styles.css        # 样式文件
├── content.js        # 内容脚本（数据抓取）
├── background.js     # 后台服务
├── icon16.png        # 16x16 图标
├── icon48.png        # 48x48 图标
└── icon128.png       # 128x128 图标
```

## 测试

### 测试小红书笔记页面

1. 访问任意小红书笔记页面
2. 点击插件图标
3. 查看「当前页面数据」是否正确显示

### 测试小红书创作者中心

1. 访问小红书创作者中心
2. 点击插件图标
3. 查看账号数据是否正确显示

## 数据格式

### 笔记数据
```json
{
  "platform": "小红书",
  "type": "note",
  "noteId": "abc123",
  "title": "笔记标题",
  "views": 10000,
  "likes": 500,
  "collects": 200,
  "comments": 50,
  "url": "https://...",
  "scrapedAt": "2024-..."
}
```

### 账号数据
```json
{
  "platform": "小红书",
  "type": "account",
  "nickname": "用户名",
  "fans": 10000,
  "totalViews": 100000,
  "totalLikes": 50000,
  "url": "https://...",
  "scrapedAt": "2024-..."
}
```
