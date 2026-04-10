"""
墨芯 v5.0 - Scheduler 单元测试
"""

import asyncio
import unittest
from datetime import datetime, timedelta

from scheduler.core import (
    InkCoreScheduler,
    PriorityTaskQueue,
    SchedulerWorker,
    CronManager,
    Task,
    ScheduledJob,
    TaskPriority,
    TaskStatus,
    CronExpressionError
)


class TestTask(unittest.TestCase):
    """测试 Task"""
    
    def test_creation(self):
        """测试创建任务"""
        task = Task(
            task_id="test_001",
            name="测试任务",
            func=lambda: "result",
            priority=TaskPriority.HIGH
        )
        
        self.assertEqual(task.task_id, "test_001")
        self.assertEqual(task.name, "测试任务")
        self.assertEqual(task.priority, TaskPriority.HIGH)
        self.assertEqual(task.status, TaskStatus.PENDING)
    
    def test_priority_comparison(self):
        """测试优先级比较"""
        from datetime import datetime
        
        now = datetime.now()
        
        task_high = Task("1", "高", lambda: None, priority=TaskPriority.HIGH, created_at=now)
        task_low = Task("2", "低", lambda: None, priority=TaskPriority.LOW, created_at=now)
        
        # 高优先级应该小于低优先级（在堆中排前面）
        self.assertTrue(task_high < task_low)
    
    def test_to_dict(self):
        """测试转换为字典"""
        task = Task(
            task_id="test_001",
            name="测试任务",
            func=lambda: None,
            status=TaskStatus.COMPLETED
        )
        
        data = task.to_dict()
        
        self.assertEqual(data["task_id"], "test_001")
        self.assertEqual(data["status"], "completed")


class TestPriorityTaskQueue(unittest.TestCase):
    """测试 PriorityTaskQueue"""
    
    def setUp(self):
        self.queue = PriorityTaskQueue()
    
    def test_put_and_get(self):
        """测试添加和获取任务"""
        async def run_test():
            task = Task("1", "测试", lambda: None)
            
            await self.queue.put(task)
            
            retrieved = await self.queue.get()
            
            self.assertEqual(retrieved.task_id, "1")
            self.assertEqual(retrieved.status, TaskStatus.QUEUED)
        
        asyncio.run(run_test())
    
    def test_priority_order(self):
        """测试优先级顺序"""
        async def run_test():
            # 添加不同优先级的任务
            task_low = Task("1", "低", lambda: None, priority=TaskPriority.LOW)
            task_high = Task("2", "高", lambda: None, priority=TaskPriority.HIGH)
            task_normal = Task("3", "普通", lambda: None, priority=TaskPriority.NORMAL)
            
            await self.queue.put(task_low)
            await self.queue.put(task_high)
            await self.queue.put(task_normal)
            
            # 应该按优先级获取
            first = await self.queue.get()
            second = await self.queue.get()
            third = await self.queue.get()
            
            self.assertEqual(first.priority, TaskPriority.HIGH)
            self.assertEqual(second.priority, TaskPriority.NORMAL)
            self.assertEqual(third.priority, TaskPriority.LOW)
        
        asyncio.run(run_test())
    
    def test_cancel(self):
        """测试取消任务"""
        async def run_test():
            task = Task("1", "测试", lambda: None)
            
            await self.queue.put(task)
            
            # 取消任务
            cancelled = await self.queue.cancel("1")
            
            self.assertTrue(cancelled)
            self.assertEqual(task.status, TaskStatus.CANCELLED)
            
            # 获取任务时应该跳过被取消的
            result = await self.queue.get()
            self.assertIsNone(result)
        
        asyncio.run(run_test())
    
    def test_get_stats(self):
        """测试获取统计"""
        async def run_test():
            task1 = Task("1", "高", lambda: None, priority=TaskPriority.HIGH)
            task2 = Task("2", "普通", lambda: None, priority=TaskPriority.NORMAL)
            
            await self.queue.put(task1)
            await self.queue.put(task2)
            
            stats = self.queue.get_stats()
            
            self.assertEqual(stats["total"], 2)
            self.assertEqual(stats["by_priority"]["HIGH"], 1)
            self.assertEqual(stats["by_priority"]["NORMAL"], 1)
        
        asyncio.run(run_test())


class TestSchedulerWorker(unittest.TestCase):
    """测试 SchedulerWorker"""
    
    def setUp(self):
        self.queue = PriorityTaskQueue()
        self.worker = SchedulerWorker(self.queue, "test_worker")
    
    def test_execute_sync_task(self):
        """测试执行同步任务"""
        async def run_test():
            results = []
            
            def sync_task():
                results.append("executed")
                return "result"
            
            task = Task("1", "同步任务", sync_task)
            await self.queue.put(task)
            
            # 执行一次任务获取
            retrieved = await self.queue.get()
            await self.worker._execute_task(retrieved)
            
            self.assertEqual(retrieved.status, TaskStatus.COMPLETED)
            self.assertEqual(retrieved.result, "result")
            self.assertEqual(results, ["executed"])
        
        asyncio.run(run_test())
    
    def test_execute_async_task(self):
        """测试执行异步任务"""
        async def run_test():
            async def async_task():
                await asyncio.sleep(0.01)
                return "async_result"
            
            task = Task("1", "异步任务", async_task)
            await self.queue.put(task)
            
            retrieved = await self.queue.get()
            await self.worker._execute_task(retrieved)
            
            self.assertEqual(retrieved.status, TaskStatus.COMPLETED)
            self.assertEqual(retrieved.result, "async_result")
        
        asyncio.run(run_test())
    
    def test_task_failure_and_retry(self):
        """测试任务失败和重试"""
        async def run_test():
            call_count = [0]
            
            def failing_task():
                call_count[0] += 1
                raise ValueError("Task failed")
            
            task = Task("1", "失败任务", failing_task, max_retries=2)
            await self.queue.put(task)
            
            retrieved = await self.queue.get()
            await self.worker._execute_task(retrieved)
            
            # 任务应该被重新放回队列（因为还有重试次数）
            self.assertEqual(retrieved.status, TaskStatus.PENDING)
            self.assertEqual(retrieved.retries, 1)
        
        asyncio.run(run_test())


class TestCronManager(unittest.TestCase):
    """测试 CronManager"""
    
    def setUp(self):
        self.cron = CronManager()
    
    def test_add_cron_job(self):
        """测试添加 Cron 任务"""
        def test_func():
            pass
        
        job_id = self.cron.add_cron_job(
            name="每日任务",
            func=test_func,
            cron_expression="0 9 * * *"
        )
        
        self.assertTrue(job_id.startswith("cron_"))
        self.assertIn(job_id, self.cron.jobs)
    
    def test_add_interval_job(self):
        """测试添加间隔任务"""
        def test_func():
            pass
        
        job_id = self.cron.add_interval_job(
            name="间隔任务",
            func=test_func,
            minutes=5
        )
        
        self.assertTrue(job_id.startswith("interval_"))
        self.assertIn(job_id, self.cron.jobs)
        self.assertEqual(self.cron.jobs[job_id].trigger, "interval")
    
    def test_add_one_time_job(self):
        """测试添加一次性任务"""
        def test_func():
            pass
        
        run_time = datetime.now() + timedelta(hours=1)
        
        job_id = self.cron.add_one_time_job(
            name="一次性任务",
            func=test_func,
            run_date=run_time
        )
        
        self.assertTrue(job_id.startswith("date_"))
        self.assertIn(job_id, self.cron.jobs)
    
    def test_invalid_cron_expression(self):
        """测试无效的 Cron 表达式"""
        def test_func():
            pass
        
        with self.assertRaises(ValueError):
            self.cron.add_cron_job(
                name="无效任务",
                func=test_func,
                cron_expression="invalid"
            )
    
    def test_list_jobs(self):
        """测试列出任务"""
        def test_func():
            pass
        
        self.cron.add_cron_job(name="任务1", func=test_func, cron_expression="0 0 * * *")
        self.cron.add_interval_job(name="任务2", func=test_func, minutes=10)
        
        jobs = self.cron.list_jobs()
        
        self.assertEqual(len(jobs), 2)


class TestInkCoreScheduler(unittest.TestCase):
    """测试 InkCoreScheduler"""
    
    def setUp(self):
        self.scheduler = InkCoreScheduler(num_workers=2)
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(len(self.scheduler.workers), 2)
        self.assertFalse(self.scheduler.running)
    
    def test_submit_task(self):
        """测试提交任务"""
        async def run_test():
            def test_func():
                return "result"
            
            task_id = await self.scheduler.submit(
                name="测试任务",
                func=test_func,
                priority=TaskPriority.HIGH
            )
            
            self.assertTrue(task_id.startswith("task_"))
            self.assertEqual(len(self.scheduler.queue), 1)
        
        asyncio.run(run_test())
    
    def test_schedule_cron(self):
        """测试调度 Cron 任务"""
        def test_func():
            pass
        
        job_id = self.scheduler.schedule_cron(
            name="定时任务",
            func=test_func,
            cron_expression="0 0 * * *"
        )
        
        self.assertTrue(job_id.startswith("cron_"))
    
    def test_schedule_interval(self):
        """测试调度间隔任务"""
        def test_func():
            pass
        
        job_id = self.scheduler.schedule_interval(
            name="间隔任务",
            func=test_func,
            minutes=30
        )
        
        self.assertTrue(job_id.startswith("interval_"))
    
    def test_get_stats(self):
        """测试获取统计"""
        stats = self.scheduler.get_stats()
        
        self.assertIn("running", stats)
        self.assertIn("queue", stats)
        self.assertIn("workers", stats)
        self.assertIn("cron_jobs", stats)


if __name__ == "__main__":
    # 配置日志
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # 运行测试
    unittest.main(verbosity=2)