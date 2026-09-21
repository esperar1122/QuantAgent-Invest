#!/usr/bin/env python3
"""
异步安全调度工具模块
提供在任意环境（包括已有事件循环的 FastAPI 异步服务中）安全运行异步协程的方法，
杜绝 'RuntimeError: This event loop is already running' 崩溃。
"""

import asyncio
import concurrent.futures
from typing import Any, Coroutine, TypeVar

T = TypeVar('T')


def run_async_safely(coro: Coroutine[Any, Any, T]) -> T:
    """
    安全地在同步上下文中执行异步协程并返回结果。
    
    兼容场景：
    1. 当前线程已有正在运行的事件循环（例如 FastAPI 请求处理器或后台任务中）：
       使用独立的线程池在干净的子线程中运行 asyncio.run(coro)，主线程安全等待结果。
    2. 当前线程没有事件循环或事件循环未在运行：
       直接使用 asyncio.run(coro) 或创建新循环运行。
    
    Args:
        coro: 待执行的异步协程
        
    Returns:
        协程执行结果
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # 当前线程中已有正在运行的事件循环，不能在此线程直接调用 loop.run_until_complete
        # 通过线程池调度至子线程独立运行
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    else:
        # 当前线程没有运行中的循环
        try:
            return asyncio.run(coro)
        except RuntimeError:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()
                asyncio.set_event_loop(None)
