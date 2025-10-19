"""
API中间件
提供请求日志、时间戳添加、CORS等功能
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from utils.logger import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 记录请求开始时间
        start_time = time.time()

        # 记录请求信息
        logger.info(
            f"请求开始 [{request_id}] {request.method} {request.url} - "
            f"客户端: {request.client.host if request.client else 'unknown'}"
        )

        # 设置时间戳
        from datetime import datetime
        request.state.timestamp = datetime.utcnow().isoformat()

        try:
            # 处理请求
            response = await call_next(request)

            # 计算处理时间
            process_time = time.time() - start_time

            # 记录响应信息
            logger.info(
                f"请求完成 [{request_id}] {request.method} {request.url} - "
                f"状态码: {response.status_code} - "
                f"处理时间: {process_time:.3f}s"
            )

            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time

            # 记录错误信息
            logger.error(
                f"请求异常 [{request_id}] {request.method} {request.url} - "
                f"错误: {str(e)} - "
                f"处理时间: {process_time:.3f}s"
            )

            # 重新抛出异常
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # API不需要缓存
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """简单的速率限制中间件"""

    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls  # 允许的请求数
        self.period = period  # 时间周期（秒）
        self.clients = {}  # 客户端请求记录

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 获取客户端IP
        client_ip = request.client.host if request.client else "unknown"

        # 获取当前时间
        current_time = time.time()

        # 清理过期记录
        self.clients = {
            ip: (requests, window_start)
            for ip, (requests, window_start) in self.clients.items()
            if current_time - window_start < self.period
        }

        # 检查客户端请求频率
        if client_ip in self.clients:
            requests, window_start = self.clients[client_ip]
            if current_time - window_start < self.period:
                if requests >= self.calls:
                    logger.warning(f"速率限制触发 - IP: {client_ip}")
                    return Response(
                        content='{"error": "请求过于频繁，请稍后重试"}',
                        status_code=429,
                        media_type="application/json"
                    )
                else:
                    self.clients[client_ip] = (requests + 1, window_start)
            else:
                self.clients[client_ip] = (1, current_time)
        else:
            self.clients[client_ip] = (1, current_time)

        return await call_next(request)


def setup_middleware(app):
    """设置中间件"""
    # 注意：顺序很重要，最后添加的中间件最先执行

    # 1. 安全头中间件（最外层）
    app.add_middleware(SecurityHeadersMiddleware)

    # 2. 速率限制中间件
    app.add_middleware(RateLimitMiddleware, calls=100, period=60)

    # 3. 请求日志中间件（最内层）
    app.add_middleware(RequestLoggingMiddleware)

    logger.info("中间件设置完成")