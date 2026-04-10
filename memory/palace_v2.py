"""
墨芯 v5.0 - PalaceV2 记忆层
基于 OpenViking 的 Context Database 封装
"""

from __future__ import annotations

import logging
import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Protocol, runtime_checkable

import yaml

# 配置日志
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# 枚举与常量
# ═══════════════════════════════════════════════════════════════════════════

class TechniqueCategory(Enum):
    """技法分类枚举"""
    CHARACTER = "character"      # 人物塑造
    PLOT = "plot"               # 情节设计
    PACING = "pacing"           # 节奏控制
    CATHARSIS = "catharsis"     # 爽点设计
    WORLD = "world"             # 世界观
    DIALOGUE = "dialogue"       # 对话设计
    OPENING = "opening"         # 开场技巧
    ENDING = "ending"           # 结尾技巧


# ═══════════════════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class TechniqueId:
    """
    技法ID值对象

    格式: {novel}-{category}-{chapter}-{sequence}
    示例: jiange-plot-ch1-001
    """
    novel: str
    category: TechniqueCategory
    chapter: str
    sequence: int

    def __str__(self) -> str:
        return f"{self.novel}-{self.category.value}-{self.chapter}-{self.sequence:03d}"

    @classmethod
    def from_string(cls, id_str: str) -> "TechniqueId":
        """从字符串解析ID"""
        parts = id_str.split("-")
        if len(parts) != 4:
            raise ValueError(f"Invalid TechniqueId format: {id_str}")
        return cls(
            novel=parts[0],
            category=TechniqueCategory(parts[1]),
            chapter=parts[2],
            sequence=int(parts[3])
        )


@dataclass
class TechniqueRecord:
    """
    技法记录数据类

    包含 L0/L1/L2 三层数据，按需加载
    """
    technique_id: TechniqueId
    name: str
    category: TechniqueCategory
    novel: str
    volume: str
    chapter: str

    # L0: 原始数据
    l0_original_text: str = ""           # 原文片段
    l0_source_location: str = ""         # 来源位置

    # L1: 结构化摘要
    l1_definition: str = ""              # 技法定义
    l1_scenario: str = ""                # 应用场景
    l1_effect: str = ""                  # 效果分析
    l1_applicability: str = ""           # 可借鉴性

    # L2: 索引标签
    l2_tags: List[str] = field(default_factory=list)
    l2_embedding_key: str = ""

    # 元数据
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # 关联
    related_techniques: List[str] = field(default_factory=list)

    def to_dict(self, tier: str = "all") -> Dict:
        """
        序列化为字典，支持按层级筛选

        Args:
            tier: "all" | "L0" | "L1" | "L2"
        """
        base = {
            "technique_id": str(self.technique_id),
            "name": self.name,
            "category": self.category.value,
            "novel": self.novel,
            "volume": self.volume,
            "chapter": self.chapter,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "related_techniques": self.related_techniques
        }

        if tier in ("all", "L0"):
            base["l0"] = {
                "original_text": self.l0_original_text[:200] + "..." if len(self.l0_original_text) > 200 else self.l0_original_text,
                "source_location": self.l0_source_location
            }

        if tier in ("all", "L1"):
            base["l1"] = {
                "definition": self.l1_definition,
                "scenario": self.l1_scenario,
                "effect": self.l1_effect,
                "applicability": self.l1_applicability
            }

        if tier in ("all", "L2"):
            base["l2"] = {
                "tags": self.l2_tags,
                "embedding_key": self.l2_embedding_key
            }

        return base


@dataclass
class Tunnel:
    """技法关联（隧道）"""
    from_id: str
    to_id: str
    relation: str          # precedes | follows | similar | contrasts
    confidence: float
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


# ═══════════════════════════════════════════════════════════════════════════
# 协议与接口
# ═══════════════════════════════════════════════════════════════════════════

@runtime_checkable
class PalaceStorage(Protocol):
    """存储接口协议，允许未来替换实现"""

    def write(self, path: str, content: any, tier: str = "L1", metadata: Dict = None) -> str:
        ...

    def read(self, path: str, tier: str = "L1") -> any:
        ...

    def search(self, query: str, path: str = "/", tier: str = "L1", max_results: int = 10) -> List[Dict]:
        ...

    def glob(self, pattern: str) -> List[str]:
        ...

    def mkdir(self, path: str, exist_ok: bool = False) -> None:
        ...

    def exists(self, path: str) -> bool:
        ...

    def tier_context(self, tier: str):
        """上下文管理器，用于切换加载层级"""
        ...


# ═══════════════════════════════════════════════════════════════════════════
# 存储实现
# ═══════════════════════════════════════════════════════════════════════════

class FileSystemStorage:
    """
    文件系统存储实现（简化版，用于开发和测试）

    生产环境应替换为 OpenViking 的实现
    """

    def __init__(self, base_path: str):
        self.base_path = Path(base_path).expanduser()
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._current_tier = "L1"

    def _full_path(self, path: str) -> Path:
        """获取完整路径"""
        # 移除开头的 /
        clean_path = path.lstrip("/")
        return self.base_path / clean_path

    def write(self, path: str, content: any, tier: str = "L1", metadata: Dict = None) -> str:
        """写入数据"""
        full_path = self._full_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # 根据内容类型选择序列化方式
        if isinstance(content, str):
            data = content
        elif isinstance(content, (dict, list)):
            data = json.dumps(content, ensure_ascii=False, indent=2)
        else:
            data = str(content)

        # 写入文件
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(data)

        # 同时写入元数据
        if metadata:
            meta_path = full_path.with_suffix(full_path.suffix + ".meta")
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

        logger.debug(f"Written to {path} (tier: {tier})")
        return str(full_path)

    def read(self, path: str, tier: str = "L1") -> any:
        """读取数据"""
        full_path = self._full_path(path)

        if not full_path.exists():
            raise FileNotFoundError(f"Path not found: {path}")

        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 尝试解析为 JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return content

    def search(self, query: str, path: str = "/", tier: str = "L1", max_results: int = 10) -> List[Dict]:
        """
        简单搜索实现（基于文件名和内容匹配）
        
        生产环境应使用向量检索
        """
        search_path = self._full_path(path)
        results = []
        
        if not search_path.exists():
            return results
        
        # 递归搜索
        for file_path in search_path.rglob("*"):
            if file_path.is_file() and not file_path.suffix.endswith(".meta"):
                matched = False
                
                # 检查文件名匹配
                if query.lower() in file_path.name.lower():
                    matched = True
                
                # 检查内容匹配
                if not matched:
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content_str = f.read()
                            if query.lower() in content_str.lower():
                                matched = True
                    except Exception:
                        pass
                
                if matched:
                    try:
                        content = self.read(str(file_path.relative_to(self.base_path)))
                        results.append({
                            "path": str(file_path.relative_to(self.base_path)),
                            "content": content,
                            "metadata": self._read_metadata(file_path)
                        })
                    except Exception as e:
                        logger.warning(f"Failed to read {file_path}: {e}")
                
                if len(results) >= max_results:
                    break
        
        return results

    def _read_metadata(self, file_path: Path) -> Dict:
        """读取元数据"""
        meta_path = file_path.with_suffix(file_path.suffix + ".meta")
        if meta_path.exists():
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def glob(self, pattern: str) -> List[str]:
        """模式匹配"""
        # 简单的 glob 实现
        search_pattern = pattern.lstrip("/")
        base = self.base_path

        # 处理 /**/ 模式
        if "**/" in search_pattern:
            parts = search_pattern.split("**/")
            base = base / parts[0]
            pattern_end = parts[1] if len(parts) > 1 else "*"

            results = []
            for file_path in base.rglob(pattern_end):
                if file_path.is_file():
                    results.append("/" + str(file_path.relative_to(self.base_path)))
            return results

        # 简单模式
        results = []
        for file_path in base.glob(search_pattern):
            if file_path.is_file():
                results.append("/" + str(file_path.relative_to(self.base_path)))
        return results

    def mkdir(self, path: str, exist_ok: bool = False) -> None:
        """创建目录"""
        full_path = self._full_path(path)
        full_path.mkdir(parents=True, exist_ok=exist_ok)

    def exists(self, path: str) -> bool:
        """检查路径是否存在"""
        return self._full_path(path).exists()

    def tier_context(self, tier: str):
        """层级上下文管理器（简化实现）"""
        class TierContext:
            def __enter__(ctx_self):
                ctx_self.old_tier = self._current_tier
                self._current_tier = tier
                return ctx_self

            def __exit__(ctx_self, *args):
                self._current_tier = ctx_self.old_tier
                return False

        return TierContext()


# ═══════════════════════════════════════════════════════════════════════════
# 主类: InkCorePalaceV2
# ═══════════════════════════════════════════════════════════════════════════

import json  # 需要在文件顶部导入


class InkCorePalaceV2:
    """
    墨芯记忆宫殿 v2

    基于 OpenViking 的 Context Database，提供小说技法专用的存储和检索
    """

    # 类常量
    DEFAULT_BASE_PATH = "~/.inkcore/palace"
    MAX_TUNNEL_DEPTH = 3
    DEFAULT_SEARCH_LIMIT = 10

    def __init__(self, base_path: str = None, db: PalaceStorage = None):
        """
        初始化 Palace

        Args:
            base_path: 数据库路径
            db: 可选的存储实现（用于测试注入）
        """
        self.base_path = Path(base_path or self.DEFAULT_BASE_PATH).expanduser()

        # 如果没有提供存储实现，使用文件系统存储
        if db is None:
            self.db: PalaceStorage = FileSystemStorage(str(self.base_path))
        else:
            self.db = db

        # 初始化目录结构
        self._init_directory_structure()

        logger.info(f"Palace initialized at {self.base_path}")

    def _init_directory_structure(self) -> None:
        """初始化标准目录结构"""
        directories = [
            # 记忆层
            "/memories/novels",
            "/memories/user-prefs",
            "/memories/sessions",
            "/memories/tunnels",

            # 资源层
            "/resources/raw-novels",
            "/resources/corpora",
            "/resources/embeddings",

            # 技能层
            "/skills/extraction",
            "/skills/analysis",
            "/skills/report",
        ]

        for dir_path in directories:
            try:
                self.db.mkdir(dir_path, exist_ok=True)
            except Exception as e:
                logger.warning(f"Failed to create directory {dir_path}: {e}")

    # ═══════════════════════════════════════════════════════════
    # 核心 API: 存入 (Mine)
    # ═══════════════════════════════════════════════════════════

    def mine_chapter(self,
                     novel_name: str,
                     volume: str,
                     chapter: str,
                     chapter_text: str,
                     extracted_techniques: List[Dict]) -> List[TechniqueId]:
        """
        分析章节并存入 Palace

        Args:
            novel_name: 作品名称
            volume: 卷号
            chapter: 章节
            chapter_text: 完整章节文本
            extracted_techniques: 提取的技法列表

        Returns:
            创建的技法ID列表
        """
        # 验证输入
        self._validate_chapter_input(novel_name, volume, chapter, chapter_text)

        # 保存原始章节
        chapter_path = self._save_raw_chapter(novel_name, volume, chapter, chapter_text)

        # 保存每个技法
        technique_ids = []
        for i, tech_data in enumerate(extracted_techniques):
            try:
                tech_id = self._save_technique(
                    novel=novel_name,
                    volume=volume,
                    chapter=chapter,
                    sequence=i,
                    tech_data=tech_data,
                    chapter_path=chapter_path
                )
                technique_ids.append(tech_id)
            except Exception as e:
                logger.warning(f"Failed to save technique {i}: {e}")
                continue

        # 建立关联
        if len(technique_ids) > 1:
            self._build_tunnels(novel_name, technique_ids, extracted_techniques)

        logger.info(f"Mined chapter {chapter} of {novel_name}, saved {len(technique_ids)} techniques")

        return technique_ids

    def _validate_chapter_input(self, novel: str, volume: str,
                                chapter: str, text: str) -> None:
        """验证章节输入数据"""
        if not novel:
            raise ValueError("Novel name cannot be empty")
        if not volume:
            raise ValueError("Volume cannot be empty")
        if not chapter:
            raise ValueError("Chapter cannot be empty")
        if not text or len(text) < 100:
            raise ValueError(f"Chapter text too short: {len(text)} chars")

    def _save_raw_chapter(self, novel: str, volume: str,
                          chapter: str, text: str) -> str:
        """保存原始章节"""
        chapter_path = f"/resources/raw-novels/{novel}/{volume}/{chapter}.txt"

        # 计算文本指纹
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]

        content = {
            "text": text,
            "metadata": {
                "novel": novel,
                "volume": volume,
                "chapter": chapter,
                "char_count": len(text),
                "word_count": len(text) // 2,
                "hash": text_hash,
                "ingested_at": datetime.now().isoformat()
            }
        }

        self.db.write(chapter_path, content, tier="L0")

        return chapter_path

    def _build_tunnels(self, novel: str, technique_ids: list, techniques_data: list) -> None:
        """
        建立技法间的关联

        简单实现：相邻技法建立关联
        """
        for i in range(len(technique_ids) - 1):
            from_id = technique_ids[i]
            to_id = technique_ids[i + 1]

            try:
                self.create_tunnel(
                    from_id=from_id,
                    to_id=to_id,
                    relation="follows",
                    confidence=0.7,
                    metadata={"auto_created": True}
                )
            except Exception as e:
                logger.warning(f"Failed to create tunnel from {from_id} to {to_id}: {e}")

    def _save_technique(self,
                        novel: str,
                        volume: str,
                        chapter: str,
                        sequence: int,
                        tech_data: Dict,
                        chapter_path: str) -> TechniqueId:
        """保存单个技法"""
        category = TechniqueCategory(tech_data["category"])

        tech_id = TechniqueId(
            novel=novel,
            category=category,
            chapter=chapter,
            sequence=sequence
        )

        base_path = f"/memories/novels/{novel}/{category.value}"

        # L0
        self._save_technique_l0(base_path, tech_id, tech_data, chapter_path)

        # L1
        self._save_technique_l1(base_path, tech_id, tech_data, volume)

        # L2
        self._save_technique_l2(base_path, tech_id, tech_data)

        return tech_id

    def _save_technique_l0(self, base_path: str, tech_id: TechniqueId,
                           tech_data: Dict, source_path: str) -> None:
        """保存 L0 - 原始文本"""
        self.db.mkdir(f"{base_path}/L0", exist_ok=True)

        content = {
            "text": tech_data.get("example", ""),
            "source": source_path,
            "technique_id": str(tech_id),
            "name": tech_data.get("name", "")
        }

        self.db.write(
            f"{base_path}/L0/{tech_id}.json",
            content,
            tier="L0",
            metadata={"technique_id": str(tech_id)}
        )

    def _save_technique_l1(self, base_path: str, tech_id: TechniqueId,
                           tech_data: Dict, volume: str) -> None:
        """保存 L1 - 结构化摘要"""
        self.db.mkdir(f"{base_path}/L1", exist_ok=True)

        analysis = tech_data.get("analysis", {})

        content = {
            "technique_id": str(tech_id),
            "name": tech_data.get("name", ""),
            "category": tech_id.category.value,
            "volume": volume,
            "chapter": tech_id.chapter,
            "definition": analysis.get("definition", ""),
            "scenario": analysis.get("scenario", ""),
            "effect": analysis.get("effect", ""),
            "applicability": analysis.get("applicability", ""),
            "created_at": datetime.now().isoformat()
        }

        self.db.write(
            f"{base_path}/L1/{tech_id}.json",
            content,
            tier="L1",
            metadata={"technique_id": str(tech_id)}
        )

    def _save_technique_l2(self, base_path: str, tech_id: TechniqueId,
                           tech_data: Dict) -> None:
        """保存 L2 - 索引标签"""
        self.db.mkdir(f"{base_path}/L2", exist_ok=True)

        analysis = tech_data.get("analysis", {})

        tags = [
            tech_id.category.value,
            tech_data.get("name", ""),
            analysis.get("subtype", ""),
            analysis.get("mood", ""),
            analysis.get("target_audience", "")
        ]
        tags = [t for t in tags if t]

        content = {
            "technique_id": str(tech_id),
            "tags": tags,
            "embedding_key": str(tech_id)
        }

        self.db.write(
            f"{base_path}/L2/{tech_id}.json",
            content,
            tier="L2",
            metadata={"technique_id": str(tech_id)}
        )

    # ═══════════════════════════════════════════════════════════
    # 核心 API: 检索 (Search)
    # ═══════════════════════════════════════════════════════════

    def search(self,
               query: str,
               novel: Optional[str] = None,
               category: Optional[TechniqueCategory] = None,
               tier: str = "L1",
               max_results: int = 10) -> List[TechniqueRecord]:
        """
        检索技法

        Args:
            query: 查询文本
            novel: 可选，限定作品
            category: 可选，限定技法类型
            tier: 加载层级
            max_results: 最大结果数
        """
        search_path = self._build_search_path(novel, category)

        with self.db.tier_context(tier):
            results = self.db.search(
                query=query,
                path=search_path,
                max_results=max_results
            )

        records = []
        for result in results:
            try:
                record = self._search_result_to_record(result, tier)
                if record:
                    records.append(record)
            except Exception as e:
                logger.warning(f"Failed to convert search result: {e}")
                continue

        return records

    def _build_search_path(self, novel: Optional[str],
                          category: Optional[TechniqueCategory]) -> str:
        """构建检索路径"""
        path = "/memories"
        if novel:
            path = f"{path}/novels/{novel}"
        if category:
            path = f"{path}/{category.value}"
        return path

    def _search_result_to_record(self, result: Dict, tier: str) -> Optional[TechniqueRecord]:
        """将搜索结果转换为 TechniqueRecord"""
        try:
            content = result.get("content", {})

            if isinstance(content, str):
                content = json.loads(content)

            tech_id_str = content.get("technique_id", "")
            if not tech_id_str:
                return None

            tech_id = TechniqueId.from_string(tech_id_str)

            return TechniqueRecord(
                technique_id=tech_id,
                name=content.get("name", ""),
                category=tech_id.category,
                novel=tech_id.novel,
                volume=content.get("volume", ""),
                chapter=tech_id.chapter,
                l0_original_text=content.get("text", "") if tier == "L0" else "",
                l1_definition=content.get("definition", "") if tier in ("L1", "all") else "",
                l1_scenario=content.get("scenario", ""),
                l1_effect=content.get("effect", ""),
                l1_applicability=content.get("applicability", ""),
                l2_tags=content.get("tags", []) if tier in ("L2", "all") else [],
                metadata=result.get("metadata", {}),
                created_at=datetime.fromisoformat(content.get("created_at", datetime.now().isoformat()))
            )
        except Exception as e:
            logger.error(f"Failed to parse record: {e}")
            return None

    # ═══════════════════════════════════════════════════════════
    # 核心 API: 图遍历 (Graph Traversal)
    # ═══════════════════════════════════════════════════════════

    def traverse(self,
                 technique_id: TechniqueId | str,
                 relation_type: Optional[str] = None,
                 max_hops: int = 2) -> List[TechniqueRecord]:
        """
        图遍历 - 发现关联技法

        Args:
            technique_id: 起始技法ID
            relation_type: 可选，限定关系类型
            max_hops: 最大遍历深度
        """
        if isinstance(technique_id, str):
            tech_id = TechniqueId.from_string(technique_id)
        else:
            tech_id = technique_id

        visited = {str(tech_id)}
        frontier = [(tech_id, 0)]
        results = []

        while frontier:
            current_id, depth = frontier.pop(0)

            if depth >= max_hops:
                continue

            related = self._find_related(str(current_id), relation_type)

            for rel_id, relation in related:
                if rel_id in visited:
                    continue

                visited.add(rel_id)

                record = self._load_by_id(rel_id)
                if record:
                    record.metadata["relation"] = relation
                    record.metadata["hop_distance"] = depth + 1
                    results.append(record)

                    frontier.append((TechniqueId.from_string(rel_id), depth + 1))

        results.sort(key=lambda r: r.metadata.get("hop_distance", 999))
        return results

    def _find_related(self, tech_id_str: str,
                     relation_type: Optional[str]) -> List[tuple]:
        """查找关联技法"""
        tunnel_files = self.db.glob(f"/memories/tunnels/*{tech_id_str}*.json")

        related = []
        for tunnel_file in tunnel_files:
            try:
                tunnel_data = self.db.read(tunnel_file)

                if relation_type and tunnel_data.get("relation") != relation_type:
                    continue

                if tunnel_data["from"] == tech_id_str:
                    related.append((tunnel_data["to"], tunnel_data.get("relation", "unknown")))
                elif tunnel_data["to"] == tech_id_str:
                    related.append((tunnel_data["from"], tunnel_data.get("relation", "unknown")))

            except Exception as e:
                logger.warning(f"Failed to read tunnel {tunnel_file}: {e}")
                continue

        return related

    def _load_by_id(self, tech_id_str: str, tier: str = "L1") -> Optional[TechniqueRecord]:
        """通过ID加载技法"""
        try:
            tech_id = TechniqueId.from_string(tech_id_str)
            path = f"/memories/novels/{tech_id.novel}/{tech_id.category.value}/L1/{tech_id_str}.json"

            content = self.db.read(path, tier="L1")

            return self._search_result_to_record(
                {"content": content, "metadata": {"technique_id": tech_id_str}},
                tier
            )
        except Exception as e:
            logger.error(f"Failed to load technique {tech_id_str}: {e}")
            return None

    def create_tunnel(self,
                      from_id: TechniqueId | str,
                      to_id: TechniqueId | str,
                      relation: str,
                      confidence: float = 0.8,
                      metadata: Dict = None) -> str:
        """创建技法关联"""
        if isinstance(from_id, TechniqueId):
            from_id = str(from_id)
        if isinstance(to_id, TechniqueId):
            to_id = str(to_id)

        tunnel_data = {
            "from": from_id,
            "to": to_id,
            "relation": relation,
            "confidence": confidence,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        tunnel_name = f"{from_id}_to_{to_id}_{relation}.json"
        tunnel_path = f"/memories/tunnels/{tunnel_name}"

        self.db.write(tunnel_path, tunnel_data)

        return tunnel_path

    # ═══════════════════════════════════════════════════════════
    # 用户偏好与会话管理
    # ═══════════════════════════════════════════════════════════

    def record_user_pref(self, key: str, value: any,
                        category: str = "general") -> None:
        """记录用户偏好"""
        pref_path = f"/memories/user-prefs/{category}/{key}.json"

        self.db.mkdir(f"/memories/user-prefs/{category}", exist_ok=True)

        data = {
            "value": value,
            "updated_at": datetime.now().isoformat(),
            "access_count": 0
        }

        try:
            existing = self.db.read(pref_path)
            data["access_count"] = existing.get("access_count", 0)
        except FileNotFoundError:
            pass

        self.db.write(pref_path, data)

    def get_user_pref(self, key: str, default: any = None,
                     category: str = "general") -> any:
        """获取用户偏好"""
        pref_path = f"/memories/user-prefs/{category}/{key}.json"

        try:
            data = self.db.read(pref_path)
            data["access_count"] = data.get("access_count", 0) + 1
            data["last_accessed"] = datetime.now().isoformat()
            self.db.write(pref_path, data)

            return data.get("value", default)
        except FileNotFoundError:
            return default

    def save_session(self, session_id: str,
                    trajectory: List[Dict],
                    auto_extract_memory: bool = True) -> Dict:
        """保存会话轨迹"""
        session_path = f"/memories/sessions/{session_id}"
        self.db.mkdir(session_path, exist_ok=True)

        self.db.write(
            f"{session_path}/trajectory.json",
            {
                "trajectory": trajectory,
                "saved_at": datetime.now().isoformat(),
                "interaction_count": len(trajectory)
            }
        )

        extracted_memories = {}

        if auto_extract_memory:
            extracted_memories = self._extract_session_memories(trajectory)

            for mem_key, mem_value in extracted_memories.items():
                memory_path = f"{session_path}/extracted-memories/{mem_key}.json"
                self.db.mkdir(f"{session_path}/extracted-memories", exist_ok=True)
                self.db.write(memory_path, {
                    "value": mem_value,
                    "extracted_at": datetime.now().isoformat()
                })

        return extracted_memories

    def _extract_session_memories(self, trajectory: List[Dict]) -> Dict:
        """从会话中提取长期记忆"""
        memories = {}

        # 统计技法类型偏好
        category_counts = {}
        for turn in trajectory:
            if turn.get("action") == "search":
                cat = turn.get("params", {}).get("category")
                if cat:
                    category_counts[cat] = category_counts.get(cat, 0) + 1

        if category_counts:
            top_category = max(category_counts, key=category_counts.get)
            memories["preferred_category"] = top_category

        # 统计关注作品
        novel_counts = {}
        for turn in trajectory:
            novel = turn.get("params", {}).get("novel")
            if novel:
                novel_counts[novel] = novel_counts.get(novel, 0) + 1

        if novel_counts:
            memories["frequent_novels"] = sorted(
                novel_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]

        return memories

    # ═══════════════════════════════════════════════════════════
    # 工具方法
    # ═══════════════════════════════════════════════════════════

    def get_stats(self) -> Dict:
        """获取 Palace 统计信息"""
        novels = self.db.glob("/memories/novels/*")

        return {
            "novels": len(novels),
            "base_path": str(self.base_path),
            "initialized_at": datetime.now().isoformat()
        }


# ═══════════════════════════════════════════════════════════════════════════
# 异常定义
# ═══════════════════════════════════════════════════════════════════════════

class PalaceError(Exception):
    """Palace 基础异常"""
    pass


class PalaceInitError(PalaceError):
    """初始化错误"""
    pass


class PalaceStorageError(PalaceError):
    """存储错误"""
    pass


class ValidationError(PalaceError):
    """数据验证错误"""
    pass


class TechniqueNotFoundError(PalaceError):
    """技法不存在"""
    pass


# ═══════════════════════════════════════════════════════════════════════════
# 模块入口
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    "InkCorePalaceV2",
    "TechniqueId",
    "TechniqueRecord",
    "TechniqueCategory",
    "Tunnel",
    "PalaceStorage",
    "FileSystemStorage",
    "PalaceError",
    "ValidationError",
    "TechniqueNotFoundError"
]