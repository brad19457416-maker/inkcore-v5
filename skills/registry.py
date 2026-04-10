"""
墨芯 v5.0 - Skill System 技能层
SUPERPOWERS-inspired 强制工作流方法论
"""

from __future__ import annotations

import asyncio
import importlib
import inspect
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type

import yaml

# 配置日志
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# 枚举与常量
# ═══════════════════════════════════════════════════════════════════════════

class SkillStatus(Enum):
    """技能执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStep(Enum):
    """强制工作流步骤"""
    READ = "read"           # 读取输入
    EXTRACT = "extract"     # 提取信息
    VERIFY = "verify"       # 验证结果
    STORE = "store"         # 存储结果
    REPORT = "report"       # 生成报告


# ═══════════════════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class SkillMetadata:
    """技能元数据"""
    name: str
    description: str
    version: str
    author: str
    category: str
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    min_inkcore_version: str = "5.0.0"
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "category": self.category,
            "tags": self.tags,
            "dependencies": self.dependencies,
            "min_inkcore_version": self.min_inkcore_version
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SkillMetadata":
        return cls(**data)


@dataclass
class SkillContext:
    """技能执行上下文"""
    skill_id: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取上下文数据"""
        return self.output_data.get(key, self.input_data.get(key, default))
    
    def set(self, key: str, value: Any) -> None:
        """设置上下文数据"""
        self.output_data[key] = value


@dataclass
class SkillExecution:
    """技能执行记录"""
    execution_id: str
    skill_id: str
    status: SkillStatus
    context: SkillContext
    workflow_steps: List[Dict] = field(default_factory=list)
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# ═══════════════════════════════════════════════════════════════════════════
# 技能基类
# ═══════════════════════════════════════════════════════════════════════════

class BaseSkill(ABC):
    """
    技能基类
    
    所有技能必须继承此类，并实现 execute 方法
    """
    
    def __init__(self, skill_id: str, metadata: SkillMetadata, config: Dict = None):
        self.skill_id = skill_id
        self.metadata = metadata
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{skill_id}")
        
        # 工作流跟踪
        self._current_step: Optional[WorkflowStep] = None
        self._workflow_history: List[Dict] = []
    
    @abstractmethod
    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """
        执行技能
        
        Args:
            context: 执行上下文
            
        Returns:
            执行结果字典
        """
        pass
    
    def _step(self, step: WorkflowStep, data: Dict = None) -> None:
        """记录工作流步骤"""
        self._current_step = step
        self._workflow_history.append({
            "step": step.value,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        })
        self.logger.debug(f"Workflow step: {step.value}")
    
    def get_workflow_history(self) -> List[Dict]:
        """获取工作流历史"""
        return self._workflow_history.copy()


# ═══════════════════════════════════════════════════════════════════════════
# 内置技能实现
# ═══════════════════════════════════════════════════════════════════════════

class AnalyzeNovelSkill(BaseSkill):
    """
    分析小说章节技能
    
    工作流：read → extract → verify → store → report
    """
    
    def __init__(self, palace=None, orchestrator=None):
        metadata = SkillMetadata(
            name="analyze_novel",
            description="分析小说章节，提取写作技法",
            version="1.0.0",
            author="inkcore",
            category="analysis",
            tags=["novel", "analysis", "technique"]
        )
        super().__init__("analyze_novel", metadata)
        self.palace = palace
        self.orchestrator = orchestrator
    
    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """执行分析工作流"""
        # Step 1: READ - 读取输入
        self._step(WorkflowStep.READ, {"novel": context.get("novel_name")})
        
        novel_name = context.get("novel_name")
        volume = context.get("volume", "")
        chapter = context.get("chapter", "")
        chapter_text = context.get("chapter_text", "")
        
        if not all([novel_name, chapter, chapter_text]):
            raise SkillValidationError("Missing required fields: novel_name, chapter, chapter_text")
        
        # Step 2: EXTRACT - 提取技法
        self._step(WorkflowStep.EXTRACT)
        
        if self.orchestrator:
            # 使用 Agent Core 进行分析
            from agents.core import ChapterInput
            
            chapter_input = ChapterInput(
                novel_name=novel_name,
                volume=volume,
                chapter=chapter,
                chapter_text=chapter_text
            )
            
            report = await self.orchestrator.analyze_chapter(chapter_input)
            
            techniques = [t.to_dict() for t in report.techniques]
            raw_result = {
                "techniques": techniques,
                "summary": report.summary,
                "metadata": report.metadata
            }
        else:
            # 简化版分析（无 Agent Core）
            raw_result = await self._simple_extract(chapter_text)
        
        # Step 3: VERIFY - 验证
        self._step(WorkflowStep.VERIFY, {"technique_count": len(raw_result.get("techniques", []))})
        
        verified_result = self._verify_techniques(raw_result, chapter_text)
        
        # Step 4: STORE - 存储到 Palace
        self._step(WorkflowStep.STORE)
        
        if self.palace:
            from memory.palace_v2 import TechniqueId, TechniqueCategory
            
            tech_ids = self.palace.mine_chapter(
                novel_name=novel_name,
                volume=volume,
                chapter=chapter,
                chapter_text=chapter_text,
                extracted_techniques=verified_result["techniques"]
            )
            
            storage_result = {
                "stored": True,
                "technique_ids": [str(tid) for tid in tech_ids]
            }
        else:
            storage_result = {"stored": False, "reason": "Palace not available"}
        
        # Step 5: REPORT - 生成报告
        self._step(WorkflowStep.REPORT)
        
        final_report = {
            "novel": novel_name,
            "chapter": chapter,
            "techniques_count": len(verified_result["techniques"]),
            "techniques": verified_result["techniques"],
            "storage": storage_result,
            "workflow_history": self.get_workflow_history()
        }
        
        context.set("report", final_report)
        
        return final_report
    
    async def _simple_extract(self, text: str) -> Dict:
        """简化版技法提取（用于测试）"""
        techniques = []
        
        # 简单的规则检测
        # 检测危机开场/氛围营造
        crisis_keywords = ["雨夜", "游行", "危机", "冲突", "镇压", "紧张"]
        if any(kw in text for kw in crisis_keywords):
            techniques.append({
                "name": "危机开场",
                "category": "plot",
                "example": text[:100].replace('\n', ' '),
                "analysis": {
                    "definition": "以危机或紧张场景作为故事开端",
                    "scenario": "需要立即吸引读者注意力",
                    "effect": "建立紧张感和期待",
                    "applicability": "适用于科幻、政治题材"
                },
                "confidence": 0.75
            })
        
        # 检测环境描写
        env_keywords = ["星球", "街道", "建筑", "风景", "原野"]
        if any(kw in text for kw in env_keywords):
            techniques.append({
                "name": "环境铺垫",
                "category": "scene",
                "example": text[:100].replace('\n', ' '),
                "analysis": {
                    "definition": "通过环境描写建立故事背景",
                    "scenario": "需要让读者理解故事发生的世界",
                    "effect": "营造氛围，建立世界观",
                    "applicability": "科幻、奇幻类作品"
                },
                "confidence": 0.8
            })
        
        # 检测人物塑造
        char_keywords = ["副局长", "少年", "记者", "警察", "群众"]
        if any(kw in text for kw in char_keywords):
            techniques.append({
                "name": "群像刻画",
                "category": "character",
                "example": text[:80].replace('\n', ' '),
                "analysis": {
                    "definition": "通过多个人物展现社会图景",
                    "scenario": "需要展现复杂的社会关系",
                    "effect": "增强故事的真实感和层次感",
                    "applicability": "社会派、现实主义作品"
                },
                "confidence": 0.7
            })
        
        return {"techniques": techniques}
    
    def _verify_techniques(self, raw_result: Dict, original_text: str) -> Dict:
        """验证提取的技法"""
        techniques = raw_result.get("techniques", [])
        verified = []
        
        for tech in techniques:
            # 基础验证
            if not tech.get("name"):
                continue
            if tech.get("confidence", 0) < 0.5:
                continue
            
            verified.append(tech)
        
        return {"techniques": verified}


class SearchTechniqueSkill(BaseSkill):
    """
    搜索技法技能
    
    从 Palace 中检索相关技法
    """
    
    def __init__(self, palace=None):
        metadata = SkillMetadata(
            name="search_technique",
            description="搜索写作技法",
            version="1.0.0",
            author="inkcore",
            category="query",
            tags=["search", "technique", "palace"]
        )
        super().__init__("search_technique", metadata)
        self.palace = palace
    
    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """执行搜索"""
        # READ
        self._step(WorkflowStep.READ)
        
        query = context.get("query", "")
        novel = context.get("novel")
        category = context.get("category")
        max_results = context.get("max_results", 10)
        
        if not query:
            raise SkillValidationError("Query is required")
        
        # EXTRACT (搜索)
        self._step(WorkflowStep.EXTRACT, {"query": query})
        
        if self.palace:
            from memory.palace_v2 import TechniqueCategory
            
            cat_enum = None
            if category:
                try:
                    cat_enum = TechniqueCategory(category)
                except ValueError:
                    pass
            
            records = self.palace.search(
                query=query,
                novel=novel,
                category=cat_enum,
                max_results=max_results
            )
            
            results = [r.to_dict() for r in records]
        else:
            results = []
        
        # REPORT
        self._step(WorkflowStep.REPORT, {"result_count": len(results)})
        
        result = {
            "query": query,
            "results_count": len(results),
            "results": results
        }
        
        context.set("search_result", result)
        
        return result


class CompareWorksSkill(BaseSkill):
    """
    对比作品技能
    
    对比多部作品的技法使用差异
    """
    
    def __init__(self, palace=None):
        metadata = SkillMetadata(
            name="compare_works",
            description="对比多部作品的写作技法",
            version="1.0.0",
            author="inkcore",
            category="analysis",
            tags=["compare", "multi-novel", "analysis"]
        )
        super().__init__("compare_works", metadata)
        self.palace = palace
    
    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """执行对比分析"""
        # READ
        self._step(WorkflowStep.READ)
        
        novels = context.get("novels", [])
        category = context.get("category")
        
        if len(novels) < 2:
            raise SkillValidationError("At least 2 novels required for comparison")
        
        # EXTRACT
        self._step(WorkflowStep.EXTRACT, {"novels": novels})
        
        comparison = {}
        
        for novel in novels:
            if self.palace:
                # 统计各技法类型数量
                stats = {"total": 0, "by_category": {}}
                comparison[novel] = stats
            else:
                comparison[novel] = {"error": "Palace not available"}
        
        # REPORT
        self._step(WorkflowStep.REPORT)
        
        result = {
            "novels": novels,
            "comparison": comparison
        }
        
        context.set("comparison", result)
        
        return result


# ═══════════════════════════════════════════════════════════════════════════
# 技能注册表
# ═══════════════════════════════════════════════════════════════════════════

class SkillRegistry:
    """
    技能注册表
    
    管理所有可用技能的注册、发现和加载
    """
    
    def __init__(self):
        self._skills: Dict[str, Type[BaseSkill]] = {}
        self._metadata: Dict[str, SkillMetadata] = {}
        self._executions: List[SkillExecution] = []
        self.logger = logging.getLogger(__name__)
    
    def register(self, skill_class: Type[BaseSkill], 
                 metadata: SkillMetadata = None) -> None:
        """
        注册技能
        
        Args:
            skill_class: 技能类
            metadata: 可选的元数据（如果技能类已有则不需要）
        """
        skill_id = skill_class.__name__
        
        if skill_id in self._skills:
            self.logger.warning(f"Skill {skill_id} already registered, overwriting")
        
        self._skills[skill_id] = skill_class
        
        if metadata:
            self._metadata[skill_id] = metadata
        
        self.logger.info(f"Registered skill: {skill_id}")
    
    def register_builtin_skills(self, palace=None, orchestrator=None) -> None:
        """注册内置技能"""
        self.register(AnalyzeNovelSkill, SkillMetadata(
            name="analyze_novel",
            description="分析小说章节，提取写作技法",
            version="1.0.0",
            author="inkcore",
            category="analysis",
            tags=["novel", "analysis", "technique"]
        ))
        
        self.register(SearchTechniqueSkill, SkillMetadata(
            name="search_technique",
            description="搜索写作技法",
            version="1.0.0",
            author="inkcore",
            category="query",
            tags=["search", "technique", "palace"]
        ))
        
        self.register(CompareWorksSkill, SkillMetadata(
            name="compare_works",
            description="对比多部作品的写作技法",
            version="1.0.0",
            author="inkcore",
            category="analysis",
            tags=["compare", "multi-novel", "analysis"]
        ))
        
        # 实例化内置技能并注入依赖
        self._builtin_instances = {
            "analyze_novel": AnalyzeNovelSkill(palace=palace, orchestrator=orchestrator),
            "search_technique": SearchTechniqueSkill(palace=palace),
            "compare_works": CompareWorksSkill(palace=palace)
        }
    
    def get(self, skill_id: str) -> Optional[BaseSkill]:
        """
        获取技能实例
        
        优先返回内置技能实例，其次返回新实例化的技能
        """
        # 首先检查内置实例
        if hasattr(self, '_builtin_instances') and skill_id in self._builtin_instances:
            return self._builtin_instances[skill_id]
        
        # 否则创建新实例
        skill_class = self._skills.get(skill_id)
        if skill_class:
            return skill_class()
        
        return None
    
    def get_metadata(self, skill_id: str) -> Optional[SkillMetadata]:
        """获取技能元数据"""
        return self._metadata.get(skill_id)
    
    def list_skills(self, category: str = None, tag: str = None) -> List[str]:
        """
        列出可用技能
        
        Args:
            category: 按类别筛选
            tag: 按标签筛选
        """
        skills = list(self._skills.keys())
        
        if category:
            skills = [
                sid for sid in skills
                if self._metadata.get(sid) and self._metadata[sid].category == category
            ]
        
        if tag:
            skills = [
                sid for sid in skills
                if self._metadata.get(sid) and tag in self._metadata[sid].tags
            ]
        
        return skills
    
    async def execute(self, skill_id: str, input_data: Dict) -> SkillExecution:
        """
        执行技能
        
        Args:
            skill_id: 技能ID
            input_data: 输入数据
            
        Returns:
            执行记录
        """
        skill = self.get(skill_id)
        
        if not skill:
            raise SkillNotFoundError(f"Skill not found: {skill_id}")
        
        execution_id = f"{skill_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        context = SkillContext(
            skill_id=skill_id,
            input_data=input_data
        )
        
        execution = SkillExecution(
            execution_id=execution_id,
            skill_id=skill_id,
            status=SkillStatus.PENDING,
            context=context,
            started_at=datetime.now()
        )
        
        self.logger.info(f"Executing skill: {skill_id}")
        
        try:
            execution.status = SkillStatus.RUNNING
            
            result = await skill.execute(context)
            
            execution.status = SkillStatus.COMPLETED
            execution.context.output_data = result
            execution.workflow_steps = skill.get_workflow_history()
            
            self.logger.info(f"Skill {skill_id} completed successfully")
            
        except Exception as e:
            execution.status = SkillStatus.FAILED
            execution.error = str(e)
            self.logger.error(f"Skill {skill_id} failed: {e}")
            raise
        
        finally:
            execution.completed_at = datetime.now()
            self._executions.append(execution)
        
        return execution
    
    def get_execution_history(self, skill_id: str = None, 
                             limit: int = 100) -> List[SkillExecution]:
        """获取执行历史"""
        executions = self._executions
        
        if skill_id:
            executions = [e for e in executions if e.skill_id == skill_id]
        
        return executions[-limit:]
    
    def load_skill_from_file(self, file_path: str) -> None:
        """
        从文件加载技能
        
        支持 .py 文件或包含 skill.yaml 的目录
        """
        path = Path(file_path)
        
        if path.is_file() and path.suffix == ".py":
            self._load_skill_from_python(path)
        elif path.is_dir():
            yaml_file = path / "skill.yaml"
            if yaml_file.exists():
                self._load_skill_from_yaml(yaml_file)
    
    def _load_skill_from_python(self, file_path: Path) -> None:
        """从 Python 文件加载技能"""
        # 动态导入模块
        spec = importlib.util.spec_from_file_location("skill", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 查找技能类
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, BaseSkill) and 
                obj is not BaseSkill):
                self.register(obj)
    
    def _load_skill_from_yaml(self, yaml_file: Path) -> None:
        """从 YAML 配置加载技能"""
        with open(yaml_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        metadata = SkillMetadata.from_dict(config.get("metadata", {}))
        
        # 这里可以进一步加载关联的 Python 代码
        self.logger.info(f"Loaded skill config from {yaml_file}")


# ═══════════════════════════════════════════════════════════════════════════
# 异常定义
# ═══════════════════════════════════════════════════════════════════════════

class SkillError(Exception):
    """技能基础异常"""
    pass


class SkillNotFoundError(SkillError):
    """技能未找到"""
    pass


class SkillValidationError(SkillError):
    """技能输入验证错误"""
    pass


class SkillExecutionError(SkillError):
    """技能执行错误"""
    pass


# ═══════════════════════════════════════════════════════════════════════════
# 模块入口
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    "SkillRegistry",
    "BaseSkill",
    "AnalyzeNovelSkill",
    "SearchTechniqueSkill",
    "CompareWorksSkill",
    "SkillMetadata",
    "SkillContext",
    "SkillExecution",
    "SkillStatus",
    "WorkflowStep",
    "SkillError",
    "SkillNotFoundError",
    "SkillValidationError"
]