# NC + Inkcore + AI 三方协作工作流

## 概述

```
用户需求
    ↓
┌─────────────────────────────────────────────────────┐
│  阶段1：策划（NC + Inkcore）                        │
│  • NC: 输出节拍设计、人物约束、一致性检查            │
│  • Inkcore: 推荐适用技法、风格指南、反模式           │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│  阶段2：创作（AI）                                   │
│  • 按NC约束写作                                      │
│  • 应用Inkcore技法推荐                               │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│  阶段3：验证（Inkcore）                              │
│  • 检测技法覆盖率                                    │
│  • 质量评分                                          │
│  • 改进建议                                          │
└─────────────────────────────────────────────────────┘
    ↓
    ✓ 达标 → 交付
    ✗ 不达标 → 返回阶段2重写
```

---

## Inkcore 核心能力

### 1. 事前推荐 `recommend_techniques()`

根据场景和节拍类型推荐适用技法：

```python
from nc_integration import InkcoreNCIntegration

service = InkcoreNCIntegration()

# 获取推荐
result = service.recommend_techniques(
    scene_type="博物馆修复室",  # 场景类型
    beat_type="场景建立",         # 节拍类型
    goal_words=800,              # 目标字数
    novel_style="默认"            # 小说风格
)

# 返回结构
{
    "recommended_techniques": [
        {"name": "环境描写", "category": "scene", "priority": "primary", ...},
        {"name": "氛围营造", "category": "scene", "priority": "secondary", ...},
        ...
    ],
    "style_guide": {...},
    "antipattern_warnings": ["避免：...", ...],
    "tips": ["创作提示1", "创作提示2", ...],
    "word_distribution": {"total_goal": 800, "current_beat": 240, ...}
}
```

### 2. 风格指南 `get_style_guide()`

获取特定小说风格的创作指南：

```python
style = service.get_style_guide("猫腻")
# 返回：猫腻风格的技法偏好、节奏建议等
```

### 3. 事后验证 `analyze_and_feedback()`

分析章节并提供反馈：

```python
analysis = service.analyze_and_feedback(
    chapter_text="章节内容...",
    target_recommendations=result  # 之前的推荐
)

# 返回
{
    "quality_score": 0.95,
    "techniques_found": 12,
    "target_met": {
        "matched": ["环境描写", "氛围营造", ...],
        "missing": [],
        "match_rate": 0.85
    },
    "improvements": [],
    "verdict": "pass"  # 或 "revise" / "fail"
}
```

### 4. 完整工作流 `get_full_workflow()`

一键执行策划+验证：

```python
workflow = service.get_full_workflow(
    scene_type="博物馆修复室",
    beat_type="场景建立",
    goal_words=800,
    novel_style="默认",
    chapter_text="..."  # 可选
)
```

---

## 节拍类型定义

| 节拍类型 | 目标字数占比 | 核心技法 | 反模式 |
|---------|------------|---------|--------|
| 场景建立 | 20-25% | 环境描写、人物出场、氛围营造 | 避免：大段背景介绍 |
| 触发事件 | 10-15% | 悬念设置、危机开场 | 避免：事件突兀 |
| 情节推进 | 30-35% | 对话推进、快节奏 | 避免：对话过长 |
| 高潮发现 | 15-20% | 高潮爆发、情绪爆发 | 避免：情感突兀 |
| 收尾悬念 | 10-15% | 悬念设置 | 避免：戛然而止 |

---

## 场景关键词 → 技法映射

| 场景关键词 | 推荐技法 |
|-----------|---------|
| 博物馆 | 环境描写、氛围营造、空间转换 |
| 修复 | 人物出场、对话推进 |
| 科技 | 快节奏、对话推进、高潮爆发 |
| 战斗 | 快节奏、高潮爆发、情绪爆发 |
| 对话 | 对话推进、潜台词 |
| 抒情 | 温情描写、慢节奏、内心独白 |
| 夜晚 | 环境描写、氛围营造、慢节奏 |
| 危机 | 危机开场、悬念设置、快节奏 |
| 分析 | 对话推进、快节奏、内心独白 |

---

## 风格指南

### 猫腻风格
- 特点：政治斗争、细腻情感、伏笔深远
- 核心技法：对话推进、潜台词、内心独白、伏笔埋设
- 节奏：中慢节奏，注重内心变化

### 烽火戏诸侯风格
- 特点：热血战斗、兄弟情义、爽点密集
- 核心技法：快节奏、高潮爆发、情绪爆发
- 节奏：快节奏，高潮迭起

### 土豆风格
- 特点：废柴流、升级流、简洁有力
- 核心技法：快节奏、悬念设置、高潮爆发
- 节奏：简洁不拖沓

---

## 实际使用示例

### 场景：写《星隐回响》第一章第1节

**用户需求**：写第一章场景建立节拍

**步骤1：策划**
```python
recommendation = service.recommend_techniques(
    scene_type="博物馆修复室",
    beat_type="场景建立",
    goal_words=800,
    novel_style="默认"
)
```

**输出**：
```
【推荐技法】
- 主要：环境描写、人物出场、慢节奏
- 辅助：氛围营造

【风格提示】
- 用细节建立氛围
- 保持节奏，平衡叙事与对话

【反模式提醒】
- 避免：直接大段介绍人物背景
- 避免：场景与情节脱节
```

**步骤2：创作**
AI根据推荐进行创作

**步骤3：验证**
```python
feedback = service.analyze_and_feedback(
    chapter_text="创作的内容...",
    target_recommendations=recommendation
)
```

**输出**：
```
【质量报告】
- 技法检测：8个
- 质量分：0.85
- 匹配率：75%
- 判定：pass
```

---

## 文件结构

```
inkcore-v5/
├── nc_api.py              # 基础API服务
├── nc_integration.py      # NC深度集成（本文档）
├── test_nc_api.py         # 测试脚本
└── NC_INTEGRATION.md     # 使用指南
```

---

## 下一步

1. **NC集成**：让NC能够调用Inkcore的推荐API
2. **CLI封装**：提供命令行工具
3. **Web界面**：可视化工作流
4. **迭代优化**：根据实际使用反馈改进
