# MediaPilot 网站部署指南

## 域名：mediapilot.com

### 第一步：检查并注册域名

1. 访问域名注册商（推荐）：
   - [Namecheap](https://www.namecheap.com)
   - [GoDaddy](https://www.godaddy.com)
   - [阿里云](https://wanwang.aliyun.com)

2. 搜索 `mediapilot.com` 检查是否可用

3. 如果可用，完成注册购买

### 第二步：部署到 Vercel

#### 方法一：使用 Vercel CLI（推荐）

```bash
# 1. 安装 Vercel CLI
npm install -g vercel

# 2. 登录 Vercel
vercel login

# 3. 进入 web 目录并部署
cd web
vercel

# 4. 按照提示操作：
#    - Set up and deploy? → Y
#    - Link to existing project? → N
#    - Project name → mediapilot
#    - In which directory is your code located? → ./
#    - Want to modify these settings? → N

# 5. 部署到生产环境
vercel --prod
```

#### 方法二：使用 Git（推荐长期使用）

```bash
# 1. 初始化 Git 仓库（如果还没有）
cd MediaPilot
git init
git add .
git commit -m "Initial commit"

# 2. 在 GitHub 创建新仓库，然后推送
git remote add origin https://github.com/你的用户名/mediapilot.git
git branch -M main
git push -u origin main

# 3. 访问 https://vercel.com/new
# 4. 导入你的 GitHub 仓库
# 5. 配置：
#    - Framework Preset → Vite
#    - Root Directory → web
# 6. 点击 Deploy
```

### 第三步：配置自定义域名

#### 在 Vercel 中添加域名：

1. 进入 Vercel 项目控制台
2. 点击 Settings → Domains
3. 输入 `mediapilot.com` 并添加
4. Vercel 会给你 DNS 配置信息

#### 在域名注册商处配置 DNS：

登录你的域名注册商，添加以下记录：

| 类型 | 主机记录 | 记录值 | TTL |
|------|----------|--------|-----|
| A | @ | 76.76.21.21 | 600 |
| A | www | 76.76.21.21 | 600 |

或者使用 CNAME：

| 类型 | 主机记录 | 记录值 | TTL |
|------|----------|--------|-----|
| CNAME | www | 你的-vercel-app.vercel.app | 600 |

### 第四步：等待 DNS 生效

- DNS 传播通常需要 1-24 小时
- 可以用 https://dnschecker.org/ 检查

---

## 快速开始（如果你已经有域名）

如果你已经注册了域名，直接运行：

```bash
cd web
npm install -g vercel
vercel login
vercel --prod
```

然后在 Vercel 设置中添加你的域名即可！

---

## 备选域名（如果 mediapilot.com 已被注册）

- mediapilot.app
- mediapilot.tech
- mediapilot.io
- mediapilot.hk
- mediapilot.com.hk
