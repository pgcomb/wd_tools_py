import concurrent.futures
import functools
import asyncio


class ThreadPoolManager:
    def __init__(self, max_workers=None):
        """
        初始化线程池管理器
        :param max_workers: 线程池的最大线程数
        """
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    def run_in_thread_pool(self):
        """
        装饰器：将函数提交到线程池中执行，并返回结果
        :return: 装饰后的函数
        """

        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # 将函数提交到线程池
                future = self.thread_pool.submit(func, *args, **kwargs)
                return future

            return wrapper

        return decorator

    def sync2async_thread(self, func):
        """
        装饰器：将函数提交到线程池中执行，并返回结果
        :param func: 需要装饰的函数
        :return: 装饰后的函数
        """

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 将函数提交到线程池
            return await asyncio.wrap_future(self.thread_pool.submit(func, *args, **kwargs))

        return wrapper

    def shutdown(self, wait=True):
        """
        关闭线程池
        :param wait: 是否等待所有任务完成后再关闭
        """
        self.thread_pool.shutdown(wait=wait)
