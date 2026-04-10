# Inkcore NC 集成指南

## 概述

本指南说明如何在 Nova Agent (NC) 中使用 Inkcore 技法分析服务。

## 快速开始

### 1. 启动 Inkcore API 服务

```bash
# 安装依赖
pip install fastapi uvicorn

# 启动服务（默认端口 8000）
python nc_api.py
```

### 2. 测试服务

```bash
# 运行测试
python test_nc_api.py
```

预期输出：
```
============================================================
Inkcore NC Service 测试
============================================================

[测试1] 获取技法类别
✓ 共 7 个类别

[测试2] 搜索对话场景技法
✓ 找到 5 个技法

[测试3] 分析章节
✓ 检测到 5 个技法

[测试4] 获取风格画像
✓ 小说: 间客
```

## API 端点

### 获取技法类别
```bash
curl http://localhost:8000/api/v1/categories
```

响应：
```json
[
  {"id": "plot", "name": "情节类", "count": 4},
  {"id": "character", "name": "人物类", "count": 4},
  ...
]
```

### 搜索技法
```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"scene_type": "战斗", "limit": 5}'
```

响应：
```json
[
  {
    "name": "危机开场",
    "category": "plot",
    "confidence": 0.85,
    "definition": "..."
  },
  ...
]
```

### 分析章节
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"chapter_text": "雨夜，街道上..."}'
```

响应：
```json
{
  "techniques_count": 5,
  "quality_score": 0.50,
  "category_distribution": {"plot": 2, "character": 2, "scene": 1},
  "techniques": [...]
}
```

### 获取风格画像
```bash
curl http://localhost:8000/api/v1/style/间客
```

## 在 Nova Agent 中使用

### 配置

在 `config/default/tools.yaml` 中添加：

```yaml
inkcore:
  enabled: true
  base_url: http://localhost:8000
```

### 使用工具

```python
# 搜索战斗场景技法
result = await tools.execute("inkcore", action="search", scene_type="战斗")

# 分析章节质量
result = await tools.execute("inkcore", action="analyze", chapter_text="章节内容...")

# 获取风格画像
result = await tools.execute("inkcore", action="style", novel_name="间客")
```

## 与 NC 集成的工作流

### 1. 章节生成时注入技法
```
NC 生成章节 → Inkcore 搜索适用技法 → 注入提示词 → 输出
```

### 2. 生成后质量评估
```
NC 生成章节 → Inkcore 分析 → 质量评分 → 决定是否重试
```

### 3. 风格化生成
```
Inkcore 提取风格 → NC 应用风格 → 输出特定风格章节
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `nc_api.py` | Inkcore NC API 服务 |
| `test_nc_api.py` | 测试脚本 |
| `NC_INTEGRATION.md` | 本指南 |

## 技术细节

- **技法规则**: 28个预定义规则
- **技法类别**: 7大类别 (plot/character/scene/dialogue/emotion/pacing/theme)
- **置信度范围**: 0.6 - 0.95
- **质量评分**: 基于检测到的技法数量 (0-1)
