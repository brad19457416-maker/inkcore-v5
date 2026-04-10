"""
墨芯 v5.0 - Scheduler 调度层
优先级队列 + Cron 定时任务
"""

from __future__ import annotations

import asyncio
import heapq
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

# 可选的 APScheduler 导入
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.date import DateTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    AsyncIOScheduler = None
    CronTrigger = None
    DateTrigger = None
    IntervalTrigger = None

# 配置日志
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# 枚举与常量
# ═══════════════════════════════════════════════════════════════════════════

class TaskPriority(Enum):
    """任务优先级"""
    CRITICAL = 0    # 关键任务
    HIGH = 1        # 高优先级
    NORMAL = 2      # 普通优先级
    LOW = 3         # 低优先级
    BACKGROUND = 4  # 后台任务


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


# ═══════════════════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Task:
    """任务定义"""
    task_id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: Dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    retries: int = 0
    max_retries: int = 3
    
    # 用于优先级队列比较
    def __lt__(self, other: "Task") -> bool:
        """优先级队列比较：优先级数字小的在前，同优先级按创建时间"""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.created_at < other.created_at
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "priority": self.priority.name,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retries": self.retries,
            "max_retries": self.max_retries
        }


@dataclass
class ScheduledJob:
    """定时任务定义"""
    job_id: str
    name: str
    func: Callable
    trigger: str  # "cron" | "interval" | "date"
    trigger_args: Dict
    args: tuple = field(default_factory=tuple)
    kwargs: Dict = field(default_factory=dict)
    enabled: bool = True
    next_run_time: Optional[datetime] = None
    last_run_time: Optional[datetime] = None
    run_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "job_id": self.job_id,
            "name": self.name,
            "trigger": self.trigger,
            "trigger_args": self.trigger_args,
            "enabled": self.enabled,
            "next_run_time": self.next_run_time.isoformat() if self.next_run_time else None,
            "last_run_time": self.last_run_time.isoformat() if self.last_run_time else None,
            "run_count": self.run_count
        }


# ═══════════════════════════════════════════════════════════════════════════
# 优先级任务队列
# ═══════════════════════════════════════════════════════════════════════════

class PriorityTaskQueue:
    """
    优先级任务队列
    
    基于堆实现，支持：
    - 优先级排序
    - 任务取消
    - 任务状态跟踪
    """
    
    def __init__(self):
        self._queue: List[Task] = []
        self._task_map: Dict[str, Task] = {}
        self._lock = asyncio.Lock()
        self.logger = logging.getLogger(__name__)
    
    async def put(self, task: Task) -> None:
        """
        添加任务到队列
        
        Args:
            task: 任务对象
        """
        async with self._lock:
            if task.task_id in self._task_map:
                self.logger.warning(f"Task {task.task_id} already in queue, skipping")
                return
            
            task.status = TaskStatus.QUEUED
            heapq.heappush(self._queue, task)
            self._task_map[task.task_id] = task
            
            self.logger.debug(f"Task {task.task_id} added to queue with priority {task.priority.name}")
    
    async def get(self) -> Optional[Task]:
        """
        获取最高优先级任务
        
        Returns:
            任务对象，如果队列为空则返回 None
        """
        async with self._lock:
            while self._queue:
                task = heapq.heappop(self._queue)
                
                # 检查任务是否被取消
                if task.status == TaskStatus.CANCELLED:
                    del self._task_map[task.task_id]
                    continue
                
                del self._task_map[task.task_id]
                return task
            
            return None
    
    async def cancel(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功取消
        """
        async with self._lock:
            task = self._task_map.get(task_id)
            if task and task.status in (TaskStatus.PENDING, TaskStatus.QUEUED):
                task.status = TaskStatus.CANCELLED
                return True
            return False
    
    async def peek(self, n: int = 1) -> List[Task]:
        """
        查看队列前 N 个任务（不移除）
        
        Args:
            n: 查看数量
        """
        async with self._lock:
            # 获取前n个（不弹出）
            return self._queue[:n]
    
    def __len__(self) -> int:
        """队列长度"""
        return len(self._queue)
    
    def get_stats(self) -> Dict:
        """获取队列统计"""
        stats = {
            "total": len(self._queue),
            "by_priority": {},
            "by_status": {}
        }
        
        for task in self._queue:
            # 按优先级统计
            priority = task.priority.name
            stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1
            
            # 按状态统计
            status = task.status.value
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
        
        return stats


# ═══════════════════════════════════════════════════════════════════════════
# 工作线程
# ═══════════════════════════════════════════════════════════════════════════

class SchedulerWorker:
    """
    调度工作线程
    
    从优先级队列获取任务并执行
    """
    
    def __init__(self, queue: PriorityTaskQueue, worker_id: str = None):
        self.queue = queue
        self.worker_id = worker_id or f"worker_{uuid.uuid4().hex[:8]}"
        self.running = False
        self.current_task: Optional[Task] = None
        self.logger = logging.getLogger(f"{__name__}.{self.worker_id}")
    
    async def start(self) -> None:
        """启动工作线程"""
        self.running = True
        self.logger.info(f"Worker {self.worker_id} started")
        
        while self.running:
            try:
                # 获取任务
                task = await self.queue.get()
                
                if task is None:
                    # 队列为空，等待一段时间
                    await asyncio.sleep(0.1)
                    continue
                
                # 执行任务
                await self._execute_task(task)
                
            except Exception as e:
                self.logger.error(f"Worker error: {e}")
    
    async def _execute_task(self, task: Task) -> None:
        """执行单个任务"""
        self.current_task = task
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        self.logger.info(f"Executing task {task.task_id}: {task.name}")
        
        try:
            # 执行函数
            if asyncio.iscoroutinefunction(task.func):
                result = await task.func(*task.args, **task.kwargs)
            else:
                result = task.func(*task.args, **task.kwargs)
            
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            
            self.logger.info(f"Task {task.task_id} completed")
            
        except Exception as e:
            task.error = str(e)
            task.retries += 1
            
            if task.retries < task.max_retries:
                # 重试
                task.status = TaskStatus.PENDING
                await self.queue.put(task)
                self.logger.warning(f"Task {task.task_id} failed, retrying ({task.retries}/{task.max_retries})")
            else:
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now()
                self.logger.error(f"Task {task.task_id} failed after {task.max_retries} retries: {e}")
        
        finally:
            self.current_task = None
    
    def stop(self) -> None:
        """停止工作线程"""
        self.running = False
        self.logger.info(f"Worker {self.worker_id} stopped")


# ═══════════════════════════════════════════════════════════════════════════
# Cron 管理器
# ═══════════════════════════════════════════════════════════════════════════

class CronManager:
    """
    Cron 定时任务管理器
    
    基于 APScheduler 的定时任务管理
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler() if APSCHEDULER_AVAILABLE else None
        self.jobs: Dict[str, ScheduledJob] = {}
        self.logger = logging.getLogger(__name__)
    
    def start(self) -> None:
        """启动调度器"""
        if self.scheduler:
            self.scheduler.start()
            self.logger.info("Cron scheduler started")
        else:
            self.logger.warning("APScheduler not available, cron jobs disabled")
    
    def shutdown(self, wait: bool = True) -> None:
        """关闭调度器"""
        if self.scheduler:
            self.scheduler.shutdown(wait=wait)
            self.logger.info("Cron scheduler shutdown")
    
    def add_cron_job(self,
                    name: str,
                    func: Callable,
                    cron_expression: str,
                    args: tuple = None,
                    kwargs: Dict = None,
                    timezone: str = "Asia/Shanghai") -> str:
        """
        添加 Cron 任务
        
        Args:
            name: 任务名称
            func: 执行函数
            cron_expression: Cron 表达式 (e.g., "0 9 * * *")
            args: 位置参数
            kwargs: 关键字参数
            timezone: 时区
            
        Returns:
            job_id
        """
        if not APSCHEDULER_AVAILABLE:
            self.logger.warning(f"APScheduler not available, cannot add cron job: {name}")
            # 返回一个模拟的 job_id
            job_id = f"cron_{name}_{uuid.uuid4().hex[:8]}"
            return job_id
        
        job_id = f"cron_{name}_{uuid.uuid4().hex[:8]}"
        
        # 解析 cron 表达式
        parts = cron_expression.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {cron_expression}")
        
        trigger = CronTrigger(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            day_of_week=parts[4],
            timezone=timezone
        )
        
        # 添加任务到 APScheduler
        job = self.scheduler.add_job(
            func=func,
            trigger=trigger,
            args=args or (),
            kwargs=kwargs or {},
            id=job_id,
            name=name
        )
        
        # 记录任务
        scheduled_job = ScheduledJob(
            job_id=job_id,
            name=name,
            func=func,
            trigger="cron",
            trigger_args={"expression": cron_expression, "timezone": timezone},
            args=args or (),
            kwargs=kwargs or {}
        )
        
        self.jobs[job_id] = scheduled_job
        
        self.logger.info(f"Added cron job {job_id}: {name}")
        
        return job_id
    
    def add_interval_job(self,
                        name: str,
                        func: Callable,
                        seconds: int = 0,
                        minutes: int = 0,
                        hours: int = 0,
                        days: int = 0,
                        args: tuple = None,
                        kwargs: Dict = None) -> str:
        """
        添加间隔任务
        
        Args:
            name: 任务名称
            func: 执行函数
            seconds/minutes/hours/days: 间隔时间
            args: 位置参数
            kwargs: 关键字参数
            
        Returns:
            job_id
        """
        if not APSCHEDULER_AVAILABLE:
            self.logger.warning(f"APScheduler not available, cannot add interval job: {name}")
            job_id = f"interval_{name}_{uuid.uuid4().hex[:8]}"
            return job_id
        
        job_id = f"interval_{name}_{uuid.uuid4().hex[:8]}"
        
        trigger = IntervalTrigger(
            seconds=seconds,
            minutes=minutes,
            hours=hours,
            days=days
        )
        
        job = self.scheduler.add_job(
            func=func,
            trigger=trigger,
            args=args or (),
            kwargs=kwargs or {},
            id=job_id,
            name=name
        )
        
        scheduled_job = ScheduledJob(
            job_id=job_id,
            name=name,
            func=func,
            trigger="interval",
            trigger_args={"seconds": seconds, "minutes": minutes, "hours": hours, "days": days},
            args=args or (),
            kwargs=kwargs or {}
        )
        
        self.jobs[job_id] = scheduled_job
        
        self.logger.info(f"Added interval job {job_id}: {name}")
        
        return job_id
    
    def add_one_time_job(self,
                        name: str,
                        func: Callable,
                        run_date: datetime,
                        args: tuple = None,
                        kwargs: Dict = None) -> str:
        """
        添加一次性任务
        
        Args:
            name: 任务名称
            func: 执行函数
            run_date: 执行时间
            args: 位置参数
            kwargs: 关键字参数
            
        Returns:
            job_id
        """
        if not APSCHEDULER_AVAILABLE:
            self.logger.warning(f"APScheduler not available, cannot add one-time job: {name}")
            job_id = f"date_{name}_{uuid.uuid4().hex[:8]}"
            return job_id
        
        job_id = f"date_{name}_{uuid.uuid4().hex[:8]}"
        
        trigger = DateTrigger(run_date=run_date)
        
        job = self.scheduler.add_job(
            func=func,
            trigger=trigger,
            args=args or (),
            kwargs=kwargs or {},
            id=job_id,
            name=name
        )
        
        scheduled_job = ScheduledJob(
            job_id=job_id,
            name=name,
            func=func,
            trigger="date",
            trigger_args={"run_date": run_date.isoformat()},
            args=args or (),
            kwargs=kwargs or {}
        )
        
        self.jobs[job_id] = scheduled_job
        
        self.logger.info(f"Added one-time job {job_id}: {name}")
        
        return job_id
    
    def remove_job(self, job_id: str) -> bool:
        """
        移除任务
        
        Args:
            job_id: 任务ID
            
        Returns:
            是否成功移除
        """
        if not APSCHEDULER_AVAILABLE:
            if job_id in self.jobs:
                del self.jobs[job_id]
            return True
            
        try:
            self.scheduler.remove_job(job_id)
            if job_id in self.jobs:
                del self.jobs[job_id]
            self.logger.info(f"Removed job {job_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove job {job_id}: {e}")
            return False
    
    def pause_job(self, job_id: str) -> bool:
        """暂停任务"""
        if not APSCHEDULER_AVAILABLE:
            if job_id in self.jobs:
                self.jobs[job_id].enabled = False
            return True
            
        try:
            self.scheduler.pause_job(job_id)
            if job_id in self.jobs:
                self.jobs[job_id].enabled = False
            return True
        except Exception:
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """恢复任务"""
        if not APSCHEDULER_AVAILABLE:
            if job_id in self.jobs:
                self.jobs[job_id].enabled = True
            return True
            
        try:
            self.scheduler.resume_job(job_id)
            if job_id in self.jobs:
                self.jobs[job_id].enabled = True
            return True
        except Exception:
            return False
    
    def list_jobs(self) -> List[Dict]:
        """列出所有任务"""
        return [job.to_dict() for job in self.jobs.values()]
    
    def get_job(self, job_id: str) -> Optional[ScheduledJob]:
        """获取任务信息"""
        return self.jobs.get(job_id)


# ═══════════════════════════════════════════════════════════════════════════
# 主调度器
# ═══════════════════════════════════════════════════════════════════════════

class InkCoreScheduler:
    """
    墨芯调度器
    
    整合优先级队列和 Cron 定时任务
    """
    
    def __init__(self, num_workers: int = 3):
        """
        初始化调度器
        
        Args:
            num_workers: 工作线程数量
        """
        self.queue = PriorityTaskQueue()
        self.cron_manager = CronManager()
        self.workers: List[SchedulerWorker] = []
        self.num_workers = num_workers
        self.running = False
        self.logger = logging.getLogger(__name__)
        
        # 创建工作者
        for i in range(num_workers):
            worker = SchedulerWorker(self.queue, f"worker_{i}")
            self.workers.append(worker)
    
    async def start(self) -> None:
        """启动调度器"""
        if self.running:
            return
        
        self.running = True
        
        # 启动 Cron 调度器
        self.cron_manager.start()
        
        # 启动工作者
        worker_tasks = [
            asyncio.create_task(worker.start())
            for worker in self.workers
        ]
        
        self.logger.info(f"Scheduler started with {self.num_workers} workers")
        
        # 等待所有工作者
        await asyncio.gather(*worker_tasks)
    
    def stop(self) -> None:
        """停止调度器"""
        if not self.running:
            return
        
        self.running = False
        
        # 停止工作者
        for worker in self.workers:
            worker.stop()
        
        # 停止 Cron 调度器
        self.cron_manager.shutdown()
        
        self.logger.info("Scheduler stopped")
    
    async def submit(self,
                    name: str,
                    func: Callable,
                    args: tuple = None,
                    kwargs: Dict = None,
                    priority: TaskPriority = TaskPriority.NORMAL,
                    max_retries: int = 3) -> str:
        """
        提交任务到队列
        
        Args:
            name: 任务名称
            func: 执行函数
            args: 位置参数
            kwargs: 关键字参数
            priority: 优先级
            max_retries: 最大重试次数
            
        Returns:
            task_id
        """
        task_id = f"task_{name}_{uuid.uuid4().hex[:8]}"
        
        task = Task(
            task_id=task_id,
            name=name,
            func=func,
            args=args or (),
            kwargs=kwargs or {},
            priority=priority,
            max_retries=max_retries
        )
        
        await self.queue.put(task)
        
        self.logger.info(f"Submitted task {task_id}: {name} (priority: {priority.name})")
        
        return task_id
    
    def schedule_cron(self,
                     name: str,
                     func: Callable,
                     cron_expression: str,
                     args: tuple = None,
                     kwargs: Dict = None) -> str:
        """
        调度 Cron 任务
        
        Args:
            name: 任务名称
            func: 执行函数
            cron_expression: Cron 表达式
            args: 位置参数
            kwargs: 关键字参数
            
        Returns:
            job_id
        """
        return self.cron_manager.add_cron_job(
            name=name,
            func=func,
            cron_expression=cron_expression,
            args=args,
            kwargs=kwargs
        )
    
    def schedule_interval(self,
                         name: str,
                         func: Callable,
                         seconds: int = 0,
                         minutes: int = 0,
                         hours: int = 0,
                         days: int = 0,
                         args: tuple = None,
                         kwargs: Dict = None) -> str:
        """
        调度间隔任务
        
        Args:
            name: 任务名称
            func: 执行函数
            seconds/minutes/hours/days: 间隔时间
            args: 位置参数
            kwargs: 关键字参数
            
        Returns:
            job_id
        """
        return self.cron_manager.add_interval_job(
            name=name,
            func=func,
            seconds=seconds,
            minutes=minutes,
            hours=hours,
            days=days,
            args=args,
            kwargs=kwargs
        )
    
    def get_stats(self) -> Dict:
        """获取调度器统计"""
        return {
            "running": self.running,
            "queue": self.queue.get_stats(),
            "workers": {
                "total": len(self.workers),
                "active": sum(1 for w in self.workers if w.current_task is not None)
            },
            "cron_jobs": len(self.cron_manager.jobs)
        }


# ═══════════════════════════════════════════════════════════════════════════
# 异常定义
# ═══════════════════════════════════════════════════════════════════════════

class SchedulerError(Exception):
    """调度器基础异常"""
    pass


class TaskNotFoundError(SchedulerError):
    """任务未找到"""
    pass


class CronExpressionError(SchedulerError):
    """Cron 表达式错误"""
    pass


# ═══════════════════════════════════════════════════════════════════════════
# 模块入口
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    "InkCoreScheduler",
    "PriorityTaskQueue",
    "SchedulerWorker",
    "CronManager",
    "Task",
    "ScheduledJob",
    "TaskPriority",
    "TaskStatus",
    "SchedulerError",
    "TaskNotFoundError",
    "CronExpressionError"
]