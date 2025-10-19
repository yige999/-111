class AutoSaaSError(Exception):
    """AutoSaaS基础异常类"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class ScrapingError(AutoSaaSError):
    """数据抓取异常"""
    pass


class AnalysisError(AutoSaaSError):
    """AI分析异常"""
    pass


class DatabaseError(AutoSaaSError):
    """数据库操作异常"""
    pass


class ConfigurationError(AutoSaaSError):
    """配置错误异常"""
    pass


class APIError(AutoSaaSError):
    """API调用异常"""
    pass


class ValidationError(AutoSaaSError):
    """数据验证异常"""
    pass


class RateLimitError(APIError):
    """API限流异常"""
    pass


class AuthenticationError(APIError):
    """认证失败异常"""
    pass