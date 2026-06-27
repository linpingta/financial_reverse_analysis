# -*- coding: utf-8 -*-
"""
异步任务管理器
"""
import uuid
from threading import Thread, Lock
from datetime import datetime
from typing import Dict, Any, Callable, Optional


class TaskManager:
    """异步任务管理器"""
    
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.lock = Lock()
    
    def create_task(self, func: Callable, *args, **kwargs) -> str:
        """
        创建异步任务
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            task_id: 任务ID
        """
        task_id = str(uuid.uuid4())
        
        with self.lock:
            self.tasks[task_id] = {
                'status': 'pending',
                'progress': 0,
                'start_time': datetime.now(),
                'end_time': None,
                'result': None,
                'error': None,
                'message': '',
                'current_item': ''
            }
        
        thread = Thread(target=self._run_task, args=(task_id, func, args, kwargs))
        thread.daemon = True
        thread.start()
        
        return task_id
    
    def _run_task(self, task_id: str, func: Callable, args: tuple, kwargs: dict):
        """
        执行任务（内部方法）
        
        Args:
            task_id: 任务ID
            func: 要执行的函数
            args: 函数参数
            kwargs: 函数关键字参数
        """
        with self.lock:
            self.tasks[task_id]['status'] = 'running'
        
        try:
            result = func(*args, **kwargs)
            with self.lock:
                self.tasks[task_id]['status'] = 'completed'
                self.tasks[task_id]['result'] = result
                self.tasks[task_id]['end_time'] = datetime.now()
                self.tasks[task_id]['progress'] = 100
        except Exception as e:
            with self.lock:
                self.tasks[task_id]['status'] = 'failed'
                self.tasks[task_id]['error'] = str(e)
                self.tasks[task_id]['end_time'] = datetime.now()
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        查询任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务信息字典，如果任务不存在则返回None
        """
        with self.lock:
            return self.tasks.get(task_id)
    
    def update_progress(self, task_id: str, progress: int, message: str = '', current_item: str = ''):
        """
        更新任务进度
        
        Args:
            task_id: 任务ID
            progress: 进度百分比（0-100）
            message: 进度消息
            current_item: 当前处理项
        """
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id]['progress'] = min(100, max(0, progress))
                if message:
                    self.tasks[task_id]['message'] = message
                if current_item:
                    self.tasks[task_id]['current_item'] = current_item
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功取消
        """
        with self.lock:
            if task_id in self.tasks and self.tasks[task_id]['status'] == 'pending':
                self.tasks[task_id]['status'] = 'cancelled'
                self.tasks[task_id]['end_time'] = datetime.now()
                return True
            return False
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """
        清理旧任务
        
        Args:
            max_age_hours: 最大保留时间（小时）
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        with self.lock:
            task_ids_to_remove = [
                task_id for task_id, task_info in self.tasks.items()
                if task_info.get('end_time') and task_info['end_time'] < cutoff_time
            ]
            
            for task_id in task_ids_to_remove:
                del self.tasks[task_id]
    
    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有任务
        
        Returns:
            所有任务字典
        """
        with self.lock:
            return dict(self.tasks)


task_manager = TaskManager()