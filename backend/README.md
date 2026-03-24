
# MediaPilot 后端服务

## 快速开始

```bash
cd backend
pip install -r ../requirements.txt
python main.py
```

API文档访问: http://localhost:8000/docs

## API接口

### 热点搜索
- `POST /api/v1/trending/search` - 搜索热点话题

### 对标账号
- `POST /api/v1/competitors/search` - 搜索对标账号
- `GET /api/v1/competitors/export` - 导出Excel

### 视频分析
- `POST /api/v1/video/fetch` - 获取视频信息
- `POST /api/v1/video/transcript` - 获取逐字稿
- `POST /api/v1/video/rewrite` - 改写文案

### 内容生成
- `POST /api/v1/content/generate` - 生成分镜头脚本

### 音视频转写
- `POST /api/v1/media/upload` - 上传文件
- `GET /api/v1/media/{task_id}/status` - 查询状态
- `GET /api/v1/media/{task_id}/result` - 获取结果

### AI配置
- `POST /api/v1/ai/configure` - 配置AI服务

