"""
墨芯 v5.0 - Agent Core 智能体层
基于 OpenClaw sessions_spawn 的子Agent并行架构
"""

from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

# 配置日志
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# 枚举与常量
# ═══════════════════════════════════════════════════════════════════════════

class AgentStatus(Enum):
    """Agent 状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExtractionDomain(Enum):
    """提取领域"""
    CHARACTER = "character"      # 人物塑造
    PLOT = "plot"               # 情节设计
    PACING = "pacing"           # 节奏控制
    CATHARSIS = "catharsis"     # 爽点设计


# ═══════════════════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class AgentTask:
    """Agent 任务"""
    task_id: str
    agent_type: str
    input_data: Dict[str, Any]
    status: AgentStatus = AgentStatus.PENDING
    result: Optional[Dict] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "agent_type": self.agent_type,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


@dataclass
class ChapterInput:
    """章节输入数据"""
    novel_name: str
    volume: str
    chapter: str
    chapter_text: str
    metadata: Dict = field(default_factory=dict)


@dataclass
class ExtractedTechnique:
    """提取的技法"""
    name: str
    category: str
    example: str
    definition: str = ""
    scenario: str = ""
    effect: str = ""
    applicability: str = ""
    confidence: float = 0.8
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "category": self.category,
            "example": self.example,
            "analysis": {
                "definition": self.definition,
                "scenario": self.scenario,
                "effect": self.effect,
                "applicability": self.applicability
            },
            "confidence": self.confidence,
            "metadata": self.metadata
        }


@dataclass
class AnalysisReport:
    """分析报告"""
    novel_name: str
    volume: str
    chapter: str
    techniques: List[ExtractedTechnique]
    summary: str = ""
    metadata: Dict = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "novel_name": self.novel_name,
            "volume": self.volume,
            "chapter": self.chapter,
            "techniques_count": len(self.techniques),
            "techniques": [t.to_dict() for t in self.techniques],
            "summary": self.summary,
            "metadata": self.metadata,
            "generated_at": self.generated_at.isoformat()
        }


# ═══════════════════════════════════════════════════════════════════════════
# Agent 基类
# ═══════════════════════════════════════════════════════════════════════════

class BaseAgent(ABC):
    """Agent 基类"""
    
    def __init__(self, agent_id: str, config: Dict = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.status = AgentStatus.PENDING
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
    
    @abstractmethod
    async def execute(self, task: AgentTask) -> Dict:
        """执行任务"""
        pass
    
    async def run(self, task: AgentTask) -> Dict:
        """运行任务（包装执行）"""
        self.status = AgentStatus.RUNNING
        task.status = AgentStatus.RUNNING
        task.started_at = datetime.now()
        
        try:
            result = await self.execute(task)
            task.result = result
            task.status = AgentStatus.COMPLETED
            self.status = AgentStatus.COMPLETED
            self.logger.info(f"Task {task.task_id} completed successfully")
            return result
            
        except Exception as e:
            task.error = str(e)
            task.status = AgentStatus.FAILED
            self.status = AgentStatus.FAILED
            self.logger.error(f"Task {task.task_id} failed: {e}")
            raise
        
        finally:
            task.completed_at = datetime.now()


# ═══════════════════════════════════════════════════════════════════════════
# ReadAgent - 阅读Agent
# ═══════════════════════════════════════════════════════════════════════════

class ReadAgent(BaseAgent):
    """
    阅读Agent - 预处理章节内容
    
    职责：
    1. 分词、分段
    2. 识别对话、场景边界
    3. 提取基础元数据
    4. 输出结构化章节数据
    """
    
    def __init__(self, agent_id: str = "read_agent", config: Dict = None):
        super().__init__(agent_id, config)
    
    async def execute(self, task: AgentTask) -> Dict:
        """执行阅读分析"""
        input_data = task.input_data
        chapter_text = input_data.get("chapter_text", "")
        
        self.logger.info(f"Reading chapter: {len(chapter_text)} chars")
        
        # 基础分词（简化版，实际应使用专业分词器）
        words = self._tokenize(chapter_text)
        
        # 分段
        paragraphs = self._segment_paragraphs(chapter_text)
        
        # 识别场景
        scenes = self._extract_scenes(chapter_text)
        
        # 识别对话
        dialogues = self._extract_dialogues(chapter_text)
        
        # 提取角色提及
        characters = self._extract_character_mentions(chapter_text)
        
        return {
            "word_count": len(words),
            "paragraph_count": len(paragraphs),
            "scene_count": len(scenes),
            "dialogue_count": len(dialogues),
            "characters_mentioned": characters,
            "scenes": scenes,
            "dialogues": dialogues[:5],  # 只返回前5个作为示例
            "metadata": {
                "processed_at": datetime.now().isoformat(),
                "processor": "read_agent"
            }
        }
    
    def _tokenize(self, text: str) -> List[str]:
        """简单分词（基于字符和标点）"""
        import re
        # 简单的中文分词：按标点分割，保留词语
        tokens = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z]+|\d+|[，。！？；：""''（）]', text)
        return tokens
    
    def _segment_paragraphs(self, text: str) -> List[str]:
        """分段"""
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        return paragraphs
    
    def _extract_scenes(self, text: str) -> List[Dict]:
        """提取场景（基于段落和关键词）"""
        scenes = []
        paragraphs = self._segment_paragraphs(text)
        
        scene_markers = ["春风亭", "书院", "长安", "朝堂", "边塞"]
        
        for i, para in enumerate(paragraphs):
            for marker in scene_markers:
                if marker in para:
                    scenes.append({
                        "index": i,
                        "location": marker,
                        "preview": para[:50] + "..." if len(para) > 50 else para
                    })
                    break
        
        return scenes
    
    def _extract_dialogues(self, text: str) -> List[Dict]:
        """提取对话"""
        import re
        dialogues = []
        
        # 匹配引号内的内容
        patterns = [
            r'["""]([^"""]+)["""]',  # 中文引号
            r'[""]([^""]+)[""]',      # 英文引号
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches[:10]:  # 限制数量
                dialogues.append({
                    "content": match,
                    "length": len(match)
                })
        
        return dialogues
    
    def _extract_character_mentions(self, text: str) -> List[str]:
        """提取角色提及"""
        # 常见角色名（简化版，实际应使用NER）
        common_names = ["宁缺", "桑桑", "夫子", "君陌", "陈皮皮", "叶红鱼", "莫山山"]
        mentions = []
        
        for name in common_names:
            if name in text:
                mentions.append(name)
        
        return mentions


# ═══════════════════════════════════════════════════════════════════════════
# ExtractAgents - 并行提取Agent
# ═══════════════════════════════════════════════════════════════════════════

class CharacterAgent(BaseAgent):
    """
    人物塑造提取Agent
    
    提取内容：
    - 角色出场方式
    - 性格刻画手法
    - 人物关系铺垫
    - 成长弧线设计
    """
    
    def __init__(self, agent_id: str = "character_agent", config: Dict = None):
        super().__init__(agent_id, config)
        self.domain = ExtractionDomain.CHARACTER
    
    async def execute(self, task: AgentTask) -> Dict:
        """执行人物塑造提取"""
        input_data = task.input_data
        text = input_data.get("chapter_text", "")
        scenes = input_data.get("scenes", [])
        
        self.logger.info("Extracting character techniques")
        
        techniques = []
        
        # 检测角色出场手法
        if self._detect_character_introduction(text):
            techniques.append(ExtractedTechnique(
                name="角色出场铺垫",
                category="character",
                example=self._extract_intro_example(text),
                definition="通过环境或他人对话引入新角色",
                scenario="新角色首次出场",
                effect="建立角色第一印象，制造期待",
                applicability="适用于重要配角出场"
            ))
        
        # 检测性格刻画
        if self._detect_characterization(text):
            techniques.append(ExtractedTechnique(
                name="行动刻画性格",
                category="character",
                example=self._extract_action_example(text),
                definition="通过角色的行为选择展示性格",
                scenario="需要快速建立角色形象",
                effect="性格特征具体可感，避免直白叙述",
                applicability="通用，尤其适合主角"
            ))
        
        return {
            "domain": self.domain.value,
            "techniques": [t.to_dict() for t in techniques],
            "count": len(techniques),
            "metadata": {"confidence_threshold": 0.7}
        }
    
    def _detect_character_introduction(self, text: str) -> bool:
        """检测角色出场铺垫"""
        intro_patterns = ["据说", "传闻", "听人说", "那位", "有个叫"]
        return any(p in text for p in intro_patterns)
    
    def _extract_intro_example(self, text: str) -> str:
        """提取出场示例"""
        lines = text.split('。')
        for line in lines:
            if any(p in line for p in ["据说", "传闻", "那位"]):
                return line.strip()[:100]
        return text[:100]
    
    def _detect_characterization(self, text: str) -> bool:
        """检测性格刻画"""
        action_words = ["拔刀", "冷笑", "沉默", "抬头", "转身"]
        return any(w in text for w in action_words)
    
    def _extract_action_example(self, text: str) -> str:
        """提取行动示例"""
        lines = text.split('。')
        for line in lines:
            if any(w in line for w in ["拔刀", "冷笑", "转身"]):
                return line.strip()[:100]
        return text[:100]


class PlotAgent(BaseAgent):
    """
    情节设计提取Agent
    
    提取内容：
    - 冲突设计
    - 悬念铺设
    - 转折技巧
    - 伏笔埋设
    """
    
    def __init__(self, agent_id: str = "plot_agent", config: Dict = None):
        super().__init__(agent_id, config)
        self.domain = ExtractionDomain.PLOT
    
    async def execute(self, task: AgentTask) -> Dict:
        """执行情节设计提取"""
        input_data = task.input_data
        text = input_data.get("chapter_text", "")
        
        self.logger.info("Extracting plot techniques")
        
        techniques = []
        
        # 检测危机开场
        if self._detect_crisis_opening(text):
            techniques.append(ExtractedTechnique(
                name="危机开场",
                category="plot",
                example=self._extract_crisis_example(text),
                definition="以危机场景作为故事开端",
                scenario="需要立即吸引读者注意力",
                effect="建立紧张感，展示主角能力",
                applicability="适用于玄幻、武侠等类型"
            ))
        
        # 检测悬念铺设
        if self._detect_suspense(text):
            techniques.append(ExtractedTechnique(
                name="悬念铺设",
                category="plot",
                example=self._extract_suspense_example(text),
                definition="在情节中埋下未解之谜",
                scenario="需要维持读者兴趣",
                effect="激发读者好奇心，推动阅读",
                applicability="章节结尾或情节转折点"
            ))
        
        return {
            "domain": self.domain.value,
            "techniques": [t.to_dict() for t in techniques],
            "count": len(techniques)
        }
    
    def _detect_crisis_opening(self, text: str) -> bool:
        """检测危机开场"""
        crisis_words = ["杀", "死", "危机", "危险", "逃", "追杀", "雨夜"]
        return sum(1 for w in crisis_words if w in text) >= 2
    
    def _extract_crisis_example(self, text: str) -> str:
        """提取危机示例"""
        lines = text.split('。')
        for line in lines[:3]:  # 前3句
            if any(w in line for w in ["杀", "雨夜", "刀"]):
                return line.strip()[:100]
        return text[:100]
    
    def _detect_suspense(self, text: str) -> bool:
        """检测悬念"""
        suspense_patterns = ["为什么", "怎么回事", "是谁", "难道", "究竟"]
        return any(p in text for p in suspense_patterns)
    
    def _extract_suspense_example(self, text: str) -> str:
        """提取悬念示例"""
        lines = text.split('。')
        for line in lines:
            if any(p in line for p in ["为什么", "怎么回事", "究竟"]):
                return line.strip()[:100]
        return text[:100]


class PacingAgent(BaseAgent):
    """
    节奏控制提取Agent
    
    提取内容：
    - 详略控制
    - 张弛交替
    - 章节结构设计
    - 节奏转折点
    """
    
    def __init__(self, agent_id: str = "pacing_agent", config: Dict = None):
        super().__init__(agent_id, config)
        self.domain = ExtractionDomain.PACING
    
    async def execute(self, task: AgentTask) -> Dict:
        """执行节奏控制提取"""
        input_data = task.input_data
        text = input_data.get("chapter_text", "")
        
        self.logger.info("Extracting pacing techniques")
        
        techniques = []
        
        # 检测快节奏动作场景
        if self._detect_fast_pacing(text):
            techniques.append(ExtractedTechnique(
                name="短句快节奏",
                category="pacing",
                example=self._extract_fast_example(text),
                definition="使用短句和连续动作营造紧迫感",
                scenario="战斗、追逐等动作场景",
                effect="加快阅读节奏，增强紧张感",
                applicability="动作场景、危机时刻"
            ))
        
        # 检测节奏转换
        if self._detect_pacing_shift(text):
            techniques.append(ExtractedTechnique(
                name="张弛转换",
                category="pacing",
                example=self._extract_shift_example(text),
                definition="在紧张与舒缓之间切换",
                scenario="避免读者疲劳",
                effect="调节阅读体验，突出重点场景",
                applicability="长章节或复杂情节"
            ))
        
        return {
            "domain": self.domain.value,
            "techniques": [t.to_dict() for t in techniques],
            "count": len(techniques)
        }
    
    def _detect_fast_pacing(self, text: str) -> bool:
        """检测快节奏"""
        short_sentences = text.count('。') > len(text) / 50
        action_density = sum(1 for w in ["刀", "剑", "打", "杀", "闪", "躲"] if w in text)
        return short_sentences and action_density > 3
    
    def _extract_fast_example(self, text: str) -> str:
        """提取快节奏示例"""
        lines = text.split('。')
        for line in lines:
            if len(line) < 20 and any(w in line for w in ["刀", "剑", "闪"]):
                return line.strip()[:100]
        return text[:100]
    
    def _detect_pacing_shift(self, text: str) -> bool:
        """检测节奏转换"""
        first_half = text[:len(text)//2]
        second_half = text[len(text)//2:]
        
        first_action = sum(1 for w in ["杀", "打", "战"] if w in first_half)
        second_calm = sum(1 for w in ["坐", "想", "说", "看"] if w in second_half)
        
        return first_action > 2 and second_calm > 2
    
    def _extract_shift_example(self, text: str) -> str:
        """提取转换示例"""
        mid = len(text) // 2
        return text[mid-50:mid+50]


class CatharsisAgent(BaseAgent):
    """
    爽点设计提取Agent
    
    提取内容：
    - 打脸/反转
    - 实力展示
    - 情感释放
    - 期待兑现
    """
    
    def __init__(self, agent_id: str = "catharsis_agent", config: Dict = None):
        super().__init__(agent_id, config)
        self.domain = ExtractionDomain.CATHARSIS
    
    async def execute(self, task: AgentTask) -> Dict:
        """执行爽点设计提取"""
        input_data = task.input_data
        text = input_data.get("chapter_text", "")
        
        self.logger.info("Extracting catharsis techniques")
        
        techniques = []
        
        # 检测打脸场景
        if self._detect_face_slap(text):
            techniques.append(ExtractedTechnique(
                name="反杀打脸",
                category="catharsis",
                example=self._extract_face_slap_example(text),
                definition="主角反杀轻视自己的对手",
                scenario="反派轻视主角后被反杀",
                effect="满足读者对公平的期待，产生爽感",
                applicability="装逼打脸类情节"
            ))
        
        # 检测实力展示
        if self._detect_power_display(text):
            techniques.append(ExtractedTechnique(
                name="实力震慑",
                category="catharsis",
                example=self._extract_power_example(text),
                definition="主角展示隐藏实力震惊他人",
                scenario="需要建立主角威望时",
                effect="满足读者对主角强大的期待",
                applicability="实力 reveal 场景"
            ))
        
        return {
            "domain": self.domain.value,
            "techniques": [t.to_dict() for t in techniques],
            "count": len(techniques)
        }
    
    def _detect_face_slap(self, text: str) -> bool:
        """检测打脸场景"""
        patterns = ["冷笑", "不屑", "你以为", "就凭你", "找死", "后悔"]
        return sum(1 for p in patterns if p in text) >= 2
    
    def _extract_face_slap_example(self, text: str) -> str:
        """提取打脸示例"""
        lines = text.split('。')
        for line in lines:
            if any(p in line for p in ["冷笑", "不屑", "后悔"]):
                return line.strip()[:100]
        return text[:100]
    
    def _detect_power_display(self, text: str) -> bool:
        """检测实力展示"""
        power_words = ["境界", "实力", "修为", "震惊", "不敢置信", "怎么可能"]
        return sum(1 for w in power_words if w in text) >= 2
    
    def _extract_power_example(self, text: str) -> str:
        """提取实力展示示例"""
        lines = text.split('。')
        for line in lines:
            if any(w in line for w in ["震惊", "不敢置信", "境界"]):
                return line.strip()[:100]
        return text[:100]


# ═══════════════════════════════════════════════════════════════════════════
# VerifyAgent - 验证Agent
# ═══════════════════════════════════════════════════════════════════════════

class VerifyAgent(BaseAgent):
    """
    验证Agent - 验证提取结果质量
    
    职责：
    1. 检查技法定义是否清晰
    2. 验证原文引用准确性
    3. 评估可借鉴性
    4. 去重和合并
    """
    
    def __init__(self, agent_id: str = "verify_agent", config: Dict = None):
        super().__init__(agent_id, config)
        self.min_confidence = config.get("min_confidence", 0.6) if config else 0.6
    
    async def execute(self, task: AgentTask) -> Dict:
        """执行验证"""
        input_data = task.input_data
        raw_techniques = input_data.get("raw_techniques", [])
        original_text = input_data.get("chapter_text", "")
        
        self.logger.info(f"Verifying {len(raw_techniques)} techniques")
        
        verified = []
        rejected = []
        
        for tech in raw_techniques:
            result = self._verify_single(tech, original_text)
            if result["valid"]:
                verified.append(tech)
            else:
                rejected.append({
                    "technique": tech,
                    "reason": result["reason"]
                })
        
        # 去重
        deduplicated = self._deduplicate(verified)
        
        return {
            "verified_count": len(deduplicated),
            "rejected_count": len(rejected),
            "techniques": deduplicated,
            "rejected": rejected,
            "quality_score": self._calculate_quality_score(deduplicated)
        }
    
    def _verify_single(self, technique: Dict, original_text: str) -> Dict:
        """验证单个技法"""
        # 检查必需字段
        required_fields = ["name", "category", "example", "analysis"]
        for field in required_fields:
            if field not in technique or not technique[field]:
                return {"valid": False, "reason": f"Missing field: {field}"}
        
        # 检查原文引用是否存在于文本中
        example = technique.get("example", "")
        if example and len(example) > 5:
            # 简化检查：示例中的关键词是否在原文中
            keywords = set(example[:20].split())  # 取前20字符的关键词
            if not any(kw in original_text for kw in keywords if len(kw) > 1):
                return {"valid": False, "reason": "Example not found in original text"}
        
        # 检查置信度
        confidence = technique.get("confidence", 0.8)
        if confidence < self.min_confidence:
            return {"valid": False, "reason": f"Confidence too low: {confidence}"}
        
        # 检查分析完整性
        analysis = technique.get("analysis", {})
        analysis_fields = ["definition", "scenario", "effect", "applicability"]
        empty_fields = sum(1 for f in analysis_fields if not analysis.get(f))
        if empty_fields >= 3:
            return {"valid": False, "reason": "Analysis too incomplete"}
        
        return {"valid": True}
    
    def _deduplicate(self, techniques: List[Dict]) -> List[Dict]:
        """去重"""
        seen_names = set()
        deduplicated = []
        
        for tech in techniques:
            name = tech.get("name", "")
            if name not in seen_names:
                seen_names.add(name)
                deduplicated.append(tech)
        
        return deduplicated
    
    def _calculate_quality_score(self, techniques: List[Dict]) -> float:
        """计算质量分数"""
        if not techniques:
            return 0.0
        
        scores = []
        for tech in techniques:
            score = 0.0
            # 分析完整性
            analysis = tech.get("analysis", {})
            score += sum(0.25 for f in ["definition", "scenario", "effect", "applicability"] 
                        if analysis.get(f))
            # 置信度
            score += tech.get("confidence", 0.8) * 0.2
            scores.append(min(score, 1.0))
        
        return sum(scores) / len(scores)


# ═══════════════════════════════════════════════════════════════════════════
# ReportAgent - 报告Agent
# ═══════════════════════════════════════════════════════════════════════════

class ReportAgent(BaseAgent):
    """
    报告Agent - 生成分析报告
    
    职责：
    1. 汇总所有技法
    2. 生成可读性报告
    3. 格式化输出（Markdown/JSON）
    """
    
    def __init__(self, agent_id: str = "report_agent", config: Dict = None):
        super().__init__(agent_id, config)
        self.output_format = config.get("format", "markdown") if config else "markdown"
    
    async def execute(self, task: AgentTask) -> Dict:
        """执行报告生成"""
        input_data = task.input_data
        novel_name = input_data.get("novel_name", "Unknown")
        volume = input_data.get("volume", "")
        chapter = input_data.get("chapter", "")
        techniques = input_data.get("techniques", [])
        
        self.logger.info(f"Generating report for {len(techniques)} techniques")
        
        # 分类统计
        by_category = self._categorize(techniques)
        
        # 生成摘要
        summary = self._generate_summary(novel_name, chapter, techniques, by_category)
        
        # 生成报告
        if self.output_format == "markdown":
            report = self._generate_markdown(novel_name, volume, chapter, techniques, by_category)
        else:
            report = self._generate_json(novel_name, volume, chapter, techniques, by_category)
        
        return {
            "format": self.output_format,
            "summary": summary,
            "report": report,
            "stats": {
                "total": len(techniques),
                "by_category": {k: len(v) for k, v in by_category.items()}
            }
        }
    
    def _categorize(self, techniques: List[Dict]) -> Dict[str, List[Dict]]:
        """按类别分类"""
        categories = {}
        for tech in techniques:
            cat = tech.get("category", "unknown")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(tech)
        return categories
    
    def _generate_summary(self, novel: str, chapter: str, 
                         techniques: List[Dict], by_category: Dict) -> str:
        """生成摘要"""
        total = len(techniques)
        if total == 0:
            return f"《{novel}》{chapter} 未检测到明显写作技法。"
        
        cat_names = {
            "character": "人物塑造",
            "plot": "情节设计",
            "pacing": "节奏控制",
            "catharsis": "爽点设计"
        }
        
        cat_summary = ", ".join([
            f"{cat_names.get(k, k)}({len(v)}项)" 
            for k, v in by_category.items()
        ])
        
        return f"《{novel}》{chapter} 共识别 {total} 项写作技法：{cat_summary}。"
    
    def _generate_markdown(self, novel: str, volume: str, chapter: str,
                          techniques: List[Dict], by_category: Dict) -> str:
        """生成 Markdown 报告"""
        lines = [
            f"# 《{novel}》技法分析报告",
            "",
            f"**卷册**: {volume}  ",
            f"**章节**: {chapter}  ",
            f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  ",
            "",
            "## 概览",
            "",
            f"本章节共识别 **{len(techniques)}** 项写作技法：",
            ""
        ]
        
        cat_names = {
            "character": "人物塑造",
            "plot": "情节设计",
            "pacing": "节奏控制",
            "catharsis": "爽点设计"
        }
        
        # 按类别输出
        for cat, cat_techniques in by_category.items():
            cat_name = cat_names.get(cat, cat)
            lines.extend([
                f"## {cat_name}",
                ""
            ])
            
            for i, tech in enumerate(cat_techniques, 1):
                analysis = tech.get("analysis", {})
                lines.extend([
                    f"### {i}. {tech.get('name', '未命名')}",
                    "",
                    f"**原文示例**: {tech.get('example', 'N/A')}",
                    "",
                    f"**定义**: {analysis.get('definition', 'N/A')}",
                    "",
                    f"**应用场景**: {analysis.get('scenario', 'N/A')}",
                    "",
                    f"**效果**: {analysis.get('effect', 'N/A')}",
                    "",
                    f"**可借鉴性**: {analysis.get('applicability', 'N/A')}",
                    "",
                    "---",
                    ""
                ])
        
        return "\n".join(lines)
    
    def _generate_json(self, novel: str, volume: str, chapter: str,
                      techniques: List[Dict], by_category: Dict) -> str:
        """生成 JSON 报告"""
        data = {
            "novel": novel,
            "volume": volume,
            "chapter": chapter,
            "generated_at": datetime.now().isoformat(),
            "techniques_count": len(techniques),
            "techniques": techniques,
            "by_category": by_category
        }
        return json.dumps(data, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════════════════
# Orchestrator - 智能体编排器
# ═══════════════════════════════════════════════════════════════════════════

class AgentOrchestrator:
    """
    智能体编排器
    
    协调 ReadAgent → 4 ExtractAgents → VerifyAgent → ReportAgent 的工作流
    支持并行执行和结果聚合
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化 Agent
        self.read_agent = ReadAgent("read_agent", self.config.get("read_agent"))
        self.character_agent = CharacterAgent("character_agent", self.config.get("character_agent"))
        self.plot_agent = PlotAgent("plot_agent", self.config.get("plot_agent"))
        self.pacing_agent = PacingAgent("pacing_agent", self.config.get("pacing_agent"))
        self.catharsis_agent = CatharsisAgent("catharsis_agent", self.config.get("catharsis_agent"))
        self.verify_agent = VerifyAgent("verify_agent", self.config.get("verify_agent"))
        self.report_agent = ReportAgent("report_agent", self.config.get("report_agent"))
        
        # 任务历史
        self.task_history: List[AgentTask] = []
    
    async def analyze_chapter(self, chapter_input: ChapterInput) -> AnalysisReport:
        """
        分析章节的主入口
        
        工作流:
        1. ReadAgent 预处理
        2. 4个 ExtractAgent 并行提取
        3. VerifyAgent 验证
        4. ReportAgent 生成报告
        """
        self.logger.info(f"Starting analysis for {chapter_input.novel_name} {chapter_input.chapter}")
        
        # Step 1: ReadAgent 预处理
        read_task = AgentTask(
            task_id=f"read_{chapter_input.chapter}",
            agent_type="read_agent",
            input_data={
                "novel_name": chapter_input.novel_name,
                "chapter_text": chapter_input.chapter_text
            }
        )
        
        read_result = await self.read_agent.run(read_task)
        self.task_history.append(read_task)
        
        # Step 2: 4个 ExtractAgent 并行执行
        extract_tasks = []
        
        for agent, agent_type in [
            (self.character_agent, "character_agent"),
            (self.plot_agent, "plot_agent"),
            (self.pacing_agent, "pacing_agent"),
            (self.catharsis_agent, "catharsis_agent")
        ]:
            task = AgentTask(
                task_id=f"{agent_type}_{chapter_input.chapter}",
                agent_type=agent_type,
                input_data={
                    "novel_name": chapter_input.novel_name,
                    "chapter_text": chapter_input.chapter_text,
                    "scenes": read_result.get("scenes", []),
                    "characters": read_result.get("characters_mentioned", [])
                }
            )
            extract_tasks.append((agent, task))
        
        # 并行执行
        extract_results = await asyncio.gather(*[
            self._run_extract_agent(agent, task)
            for agent, task in extract_tasks
        ])
        
        # 收集所有技法
        all_techniques = []
        for result in extract_results:
            if result and "techniques" in result:
                all_techniques.extend(result["techniques"])
        
        self.logger.info(f"Extracted {len(all_techniques)} raw techniques")
        
        # Step 3: VerifyAgent 验证
        verify_task = AgentTask(
            task_id=f"verify_{chapter_input.chapter}",
            agent_type="verify_agent",
            input_data={
                "raw_techniques": all_techniques,
                "chapter_text": chapter_input.chapter_text
            }
        )
        
        verify_result = await self.verify_agent.run(verify_task)
        self.task_history.append(verify_task)
        
        verified_techniques = verify_result.get("techniques", [])
        self.logger.info(f"Verified {len(verified_techniques)} techniques")
        
        # Step 4: ReportAgent 生成报告
        report_task = AgentTask(
            task_id=f"report_{chapter_input.chapter}",
            agent_type="report_agent",
            input_data={
                "novel_name": chapter_input.novel_name,
                "volume": chapter_input.volume,
                "chapter": chapter_input.chapter,
                "techniques": verified_techniques
            }
        )
        
        report_result = await self.report_agent.run(report_task)
        self.task_history.append(report_task)
        
        # 构建最终报告
        techniques_objects = [
            ExtractedTechnique(
                name=t.get("name", ""),
                category=t.get("category", ""),
                example=t.get("example", ""),
                definition=t.get("analysis", {}).get("definition", ""),
                scenario=t.get("analysis", {}).get("scenario", ""),
                effect=t.get("analysis", {}).get("effect", ""),
                applicability=t.get("analysis", {}).get("applicability", ""),
                confidence=t.get("confidence", 0.8)
            )
            for t in verified_techniques
        ]
        
        return AnalysisReport(
            novel_name=chapter_input.novel_name,
            volume=chapter_input.volume,
            chapter=chapter_input.chapter,
            techniques=techniques_objects,
            summary=report_result.get("summary", ""),
            metadata={
                "quality_score": verify_result.get("quality_score", 0),
                "rejected_count": verify_result.get("rejected_count", 0)
            }
        )
    
    async def _run_extract_agent(self, agent: BaseAgent, task: AgentTask) -> Dict:
        """运行提取Agent（带错误处理）"""
        try:
            result = await agent.run(task)
            self.task_history.append(task)
            return result
        except Exception as e:
            self.logger.error(f"Extract agent {agent.agent_id} failed: {e}")
            return {"techniques": [], "error": str(e)}
    
    def get_task_history(self) -> List[Dict]:
        """获取任务历史"""
        return [task.to_dict() for task in self.task_history]
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        status_counts = {}
        for task in self.task_history:
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_tasks": len(self.task_history),
            "status_distribution": status_counts
        }


# ═══════════════════════════════════════════════════════════════════════════
# 异常定义
# ═══════════════════════════════════════════════════════════════════════════

class AgentError(Exception):
    """Agent 基础异常"""
    pass


class OrchestratorError(AgentError):
    """编排器异常"""
    pass


class AgentExecutionError(AgentError):
    """Agent 执行异常"""
    pass


# ═══════════════════════════════════════════════════════════════════════════
# 模块入口
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    "AgentOrchestrator",
    "ReadAgent",
    "CharacterAgent",
    "PlotAgent",
    "PacingAgent",
    "CatharsisAgent",
    "VerifyAgent",
    "ReportAgent",
    "AgentTask",
    "ChapterInput",
    "ExtractedTechnique",
    "AnalysisReport",
    "AgentStatus",
    "ExtractionDomain",
    "BaseAgent",
    "AgentError",
    "OrchestratorError"
]