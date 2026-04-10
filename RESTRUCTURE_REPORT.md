# 墨芯 5.0 技法存储重构报告

**执行时间**: 2026-04-10  
**小说**: 《间客》  
**处理章节**: 200章

---

## 一、重构前的问题

### 原逐章存储方案
```
techniques/
├── ch_0001_第一章_xxx_techniques.json
├── ch_0002_第二章_xxx_techniques.json
├── ... (200个文件)
└── ch_0200_第两百章_xxx_techniques.json
```

**问题**:
- 文件数量爆炸：200章 = 200个文件
- 跨章查询困难：想找"悬念设置"的所有示例？需要遍历200个文件
- 重复存储：每章都存小说名、时间戳等元数据
- 聚合分析慢：统计某类技法频率需要读取所有文件

---

## 二、重构后的三维聚合存储

### 新存储结构
```
techniques/
├── library/
│   └── technique_definitions.json    # 技法定义库 (16KB)
│
├── by_category/                      # 按类别聚合
│   ├── plot.json                     # 情节类技法 (124KB)
│   ├── character.json                # 人物类技法 (88KB)
│   ├── scene.json                    # 场景类技法 (104KB)
│   ├── emotion.json                  # 情感类技法 (24KB)
│   ├── pacing.json                   # 节奏类技法 (20KB)
│   ├── dialogue.json                 # 对话类技法 (20KB)
│   └── theme.json                    # 主题类技法 (32KB)
│
├── by_chapter/                       # 按批次聚合
│   ├── batch_0001_0100.json          # 第1-100章 (128KB)
│   └── batch_0101_0200.json          # 第101-200章 (436KB)
│
├── index/                            # 索引层
│   ├── technique_chapter_map.json    # 技法→章节映射 (12KB)
│   ├── chapter_technique_map.json    # 章节→技法映射 (20KB)
│   └── examples_bank.json            # 精选示例库 (48KB)
│
└── migration_report.json             # 迁移报告
```

---

## 三、新结构的优势

### 3.1 按类别聚合 (by_category/)

**适用场景**: 学习某种技法如何使用

**查询速度**: ⭐⭐⭐⭐⭐ (直接打开单个文件)

**示例**: 想学"悬念设置"
```python
import json

with open('by_category/plot.json', 'r') as f:
    data = json.load(f)

# 直接获取所有悬念设置的示例
suspense = data['techniques']['悬念设置']
print(f"共 {suspense['occurrences']} 个示例")

for ex in suspense['examples'][:3]:
    print(f"第{ex['chapter']}章: {ex['context'][:100]}...")
```

### 3.2 按批次聚合 (by_chapter/)

**适用场景**: 查看某章的所有技法

**查询速度**: ⭐⭐⭐⭐⭐ (直接打开对应批次文件)

**示例**: 查看第150章的技法
```python
with open('by_chapter/batch_0101_0200.json', 'r') as f:
    data = json.load(f)

# 找到第150章
for ch in data['chapters']:
    if ch['chapter_number'] == 150:
        print(f"技法: {ch['techniques']}")
```

### 3.3 索引层 (index/)

**适用场景**: 快速查找和交叉分析

**technique_chapter_map.json** - 技法出现在哪些章节：
```json
{
  "危机开场": {
    "chapters": [1, 3, 5, 8, 12, ...],
    "count": 87
  },
  "悬念设置": {
    "chapters": [2, 4, 6, 9, ...],
    "count": 80
  }
}
```

**chapter_technique_map.json** - 某章使用了哪些技法：
```json
{
  "50": {
    "chapter": 50,
    "techniques": ["悬念设置", "环境描写", "人物出场"]
  }
}
```

**examples_bank.json** - 高质量示例库(置信度≥0.9)：
- 精选287个高质量示例
- 按类别和技法分类
- 方便快速学习和参考

---

## 四、技法定义库

`library/technique_definitions.json` 包含20种技法的完整定义：

| 技法 | 类别 | 定义 | 本书出现 |
|------|------|------|---------|
| 危机开场 | 情节 | 以紧张场景或冲突作为开篇 | 87次 |
| 悬念设置 | 情节 | 通过信息不对称激发好奇心 | 80次 |
| 伏笔埋设 | 情节 | 前面暗示后续事件 | 10次 |
| 高潮爆发 | 情节 | 情节冲突达到顶点 | 22次 |
| 环境描写 | 场景 | 通过环境建立世界观 | 72次 |
| 环境铺垫 | 场景 | 为后续情节做准备的环境描写 | 52次 |
| 氛围营造 | 场景 | 营造特定情感氛围 | 35次 |
| 空间转换 | 场景 | 场景切换推进叙事 | 15次 |
| 人物出场 | 人物 | 新角色首次登场 | 39次 |
| 内心独白 | 人物 | 展示人物内心想法 | 27次 |
| 性格刻画 | 人物 | 通过言行展示性格 | 1次 |
| 群像描写 | 人物 | 同时展现多个角色 | 22次 |
| 群像刻画 | 人物 | 细致刻画群体中的角色 | 69次 |
| 情感铺垫 | 情感 | 为情感爆发做准备 | 5次 |
| 情绪爆发 | 情感 | 人物情感的强烈释放 | 29次 |
| 温情描写 | 情感 | 温暖柔和的情感瞬间 | 0次 |
| 快节奏 | 节奏 | 加快叙事节奏 | 25次 |
| 慢节奏 | 节奏 | 放缓叙事节奏 | 2次 |
| 场景切换 | 节奏 | 不同场景间转换 | 0次 |
| 对话推进 | 对话 | 通过对话推动情节 | 26次 |
| 潜台词 | 对话 | 言外之意的对话 | 0次 |
| 哲学思辨 | 主题 | 探讨人生价值等主题 | 44次 |
| 社会隐喻 | 主题 | 通过故事映射现实 | 4次 |

每种技法包含：
- 完整定义和使用场景
- 使用方法和技巧
- 相关技法推荐
- 本书统计数据

---

## 五、使用指南

### 场景1: 学习某种技法
```python
# 打开对应类别文件
with open('by_category/plot.json', 'r') as f:
    data = json.load(f)

# 查看具体技法
suspense = data['techniques']['悬念设置']
for ex in suspense['examples']:
    print(f"第{ex['chapter']}章: {ex['context']}")
```

### 场景2: 查看技法定义
```python
with open('library/technique_definitions.json', 'r') as f:
    defs = json.load(f)

# 查看定义
print(defs['techniques']['危机开场']['definition'])
print(defs['techniques']['危机开场']['how_to_use'])
```

### 场景3: 查找使用某技法的所有章节
```python
with open('index/technique_chapter_map.json', 'r') as f:
    data = json.load(f)

# 找到使用"危机开场"的所有章节
chapters = data['techniques']['危机开场']['chapters']
print(f"危机开场出现在: {chapters}")
```

### 场景4: 查看某章使用了什么技法
```python
with open('index/chapter_technique_map.json', 'r') as f:
    data = json.load(f)

# 查看第50章
print(data['chapters']['50']['techniques'])
```

### 场景5: 参考高质量示例
```python
with open('index/examples_bank.json', 'r') as f:
    data = json.load(f)

# 查看情节类的高质量示例
plot_examples = data['categories']['plot']['techniques']
for tech, examples in plot_examples.items():
    print(f"\n{tech}:")
    for ex in examples[:3]:
        print(f"  第{ex['chapter']}章: {ex['context'][:100]}...")
```

---

## 六、统计摘要

| 指标 | 数值 |
|------|------|
| 处理章节 | 200章 |
| 技法总数 | 666个 |
| 平均每章 | 3.3个技法 |
| 技法类别 | 7大类 |
| 独特技法 | 20种 |
| 高质量示例 | 287个 |

### 类别分布
- 情节类: 199个 (29.9%)
- 场景类: 174个 (26.1%)
- 人物类: 158个 (23.7%)
- 主题类: 48个 (7.2%)
- 情感类: 34个 (5.1%)
- 节奏类: 27个 (4.1%)
- 对话类: 26个 (3.9%)

---

## 七、后续工作

1. **继续处理剩余章节**: 间客还有883章待处理
2. **启动《将夜》技法提取**: 1121章等待处理
3. **定期更新聚合数据**: 每处理100章重新生成聚合文件

---

**重构完成时间**: 2026-04-10 09:05  
**新结构文件数**: 13个 (原为200个)  
**存储效率提升**: 93.5% 文件数减少

