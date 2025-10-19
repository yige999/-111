"""
API异常处理
定义自定义异常和全局异常处理器
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from utils.logger import logger


class AutoSaaSError(Exception):
    """AutoSaaS Radar 基础异常类"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DatabaseError(AutoSaaSError):
    """数据库相关异常"""
    pass


class DataCollectorError(AutoSaaSError):
    """数据收集器异常"""
    pass


class GPTAnalyzerError(AutoSaaSError):
    """GPT分析器异常"""
    pass


class ValidationError(AutoSaaSError):
    """数据验证异常"""
    pass


async def autosaas_exception_handler(request: Request, exc: AutoSaaSError) -> JSONResponse:
    """AutoSaaS自定义异常处理器"""
    logger.error(f"AutoSaaS异常: {exc.message}, 详情: {exc.details}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "AutoSaaS Radar 内部错误",
            "message": exc.message,
            "details": exc.details,
            "timestamp": request.state.timestamp if hasattr(request.state, "timestamp") else None,
            "path": str(request.url.path)
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP异常处理器"""
    logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP {exc.status_code}",
            "message": exc.detail,
            "timestamp": request.state.timestamp if hasattr(request.state, "timestamp") else None,
            "path": str(request.url.path)
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """请求验证异常处理器"""
    logger.warning(f"请求验证失败: {exc.errors()}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "请求参数验证失败",
            "message": "请检查请求参数格式",
            "details": exc.errors(),
            "timestamp": request.state.timestamp if hasattr(request.state, "timestamp") else None,
            "path": str(request.url.path)
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""
    logger.error(f"未处理的异常: {type(exc).__name__}: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "服务器内部错误",
            "message": "发生了未预期的错误，请稍后重试",
            "timestamp": request.state.timestamp if hasattr(request.state, "timestamp") else None,
            "path": str(request.url.path)
        }
    )


def setup_exception_handlers(app):
    """设置异常处理器"""
    app.add_exception_handler(AutoSaaSError, autosaas_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("异常处理器设置完成")


class StandardAPIResponse:
    """标准API响应格式"""

    @staticmethod
    def success(data: Any = None, message: str = "操作成功") -> Dict[str, Any]:
        """成功响应"""
        return {
            "success": True,
            "message": message,
            "data": data,
            "timestamp": None  # 会在中间件中设置
        }

    @staticmethod
    def error(message: str, details: Optional[Dict[str, Any]] = None,
              error_code: Optional[str] = None) -> Dict[str, Any]:
        """错误响应"""
        return {
            "success": False,
            "message": message,
            "error_code": error_code,
            "details": details,
            "timestamp": None  # 会在中间件中设置
        }


def paginate_response(data: list, page: int, size: int, total: int) -> Dict[str, Any]:
    """分页响应格式"""
    total_pages = (total + size - 1) // size if size > 0 else 0

    return {
        "success": True,
        "data": data,
        "pagination": {
            "page": page,
            "size": size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        },
        "timestamp": None
    }