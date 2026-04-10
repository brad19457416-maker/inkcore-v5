# 墨芯 5.0 技法提取存储规范

## 目录结构

```
inkcore-v5/
├── novels/                          # 小说数据目录
│   ├── {novel_name}/                # 单部小说目录
│   │   ├── chapters/                # 章节原文
│   │   │   ├── ch_0001_*.txt
│   │   │   ├── ch_0002_*.txt
│   │   │   └── index.json           # 章节索引
│   │   ├── techniques/              # 章节技法提取结果
│   │   │   ├── ch_0001_*_techniques.json
│   │   │   └── ch_0002_*_techniques.json
│   │   └── reports/                 # 汇总报告
│   │       ├── progress_report.json # 进度报告
│   │       ├── final_report.json    # 最终汇总报告
│   │       └── final_report.md      # Markdown格式报告
│   └── ...
├── palace/                          # Palace 数据存储
│   ├── novels/                      # 小说元数据
│   ├── techniques/                  # 技法记录
│   └── tunnels/                     # 技法关联
├── tools/                           # 工具脚本
│   ├── split_chapters.py            # 章节分割工具
│   └── batch_extract.py             # 批量提取工具
└── skills/                          # 技能层代码
```

## 文件命名规范

### 章节文件
- 格式: `ch_{序号}_{章节标题}.txt`
- 示例: `ch_0001_第一章 钟楼街的游行.txt`
- 序号: 4位数字，从0001开始

### 技法提取结果文件
- 格式: `{章节文件名}_techniques.json`
- 示例: `ch_0001_第一章 钟楼街的游行_techniques.json`

## 技法提取结果数据结构

```json
{
  "chapter": "章节标题",
  "file": "原始文件名",
  "status": "success|failed",
  "techniques_count": 3,
  "techniques": [
    {
      "name": "技法名称",
      "category": "plot|character|scene|...",
      "example": "原文示例片段",
      "analysis": {
        "definition": "技法定义",
        "scenario": "应用场景",
        "effect": "效果分析",
        "applicability": "可借鉴性"
      },
      "confidence": 0.85
    }
  ],
  "timestamp": "ISO8601时间戳",
  "storage": {
    "stored": true,
    "technique_ids": ["..."]
  }
}
```

## 报告数据结构

### 进度报告 (progress_report.json)
```json
{
  "novel": "小说名称",
  "timestamp": "生成时间",
  "progress": {
    "total": 总章节数,
    "processed": 已处理数,
    "failed": 失败数
  },
  "recent_results": [...]
}
```

### 最终报告 (final_report.json)
```json
{
  "novel": "小说名称",
  "generated_at": "生成时间",
  "summary": {
    "total_chapters": 总章节数,
    "processed": 成功数,
    "failed": 失败数,
    "total_techniques": 技法总数
  },
  "category_distribution": {
    "plot": 数量,
    "character": 数量
  },
  "technique_frequency": {
    "技法名称": 出现次数
  },
  "chapter_results": [...]
}
```

## 当前处理状态

### 《间客》
- 总章节: 1083章
- 已处理: 前100章
- 发现技法: 166个
- 技法分布:
  - scene (场景): 52个
  - character (人物): 69个
  - plot (情节): 45个

### 《将夜》
- 总章节: 1121章
- 已处理: 待开始
- 发现技法: 待提取

## 使用方法

### 1. 章节分割
```bash
python3 tools/split_chapters.py <源文件> <输出目录>
```

### 2. 批量技法提取
```bash
# 提取全部章节
python3 tools/batch_extract.py 间客

# 提取指定范围
python3 tools/batch_extract.py 间客 --start 1 --end 100

# 指定批次大小
python3 tools/batch_extract.py 间客 --batch 20
```

## 后续工作

1. 继续完成《间客》剩余章节的技法提取
2. 开始《将夜》的技法提取
3. 完善技法分类体系（解决 'scene' 类别问题）
4. 增加更精细的技法分析维度
5. 建立技法间的关联和演进分析
