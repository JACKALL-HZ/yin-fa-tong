"""自定义异常基类"""


class AppException(Exception):
    """业务异常基类"""

    def __init__(self, code: int = 400, message: str = "请求错误"):
        self.code = code
        self.message = message
        self.status_code = code if 100 <= code < 600 else 400
        super().__init__(self.message)


class NotFoundException(AppException):
    """资源不存在"""

    def __init__(self, message: str = "资源不存在"):
        super().__init__(code=404, message=message)


class UnauthorizedException(AppException):
    """未授权"""

    def __init__(self, message: str = "未授权访问"):
        super().__init__(code=401, message=message)


class ForbiddenException(AppException):
    """禁止访问"""

    def __init__(self, message: str = "无权限访问"):
        super().__init__(code=403, message=message)


class BadRequestException(AppException):
    """请求参数错误"""

    def __init__(self, message: str = "请求参数错误"):
        super().__init__(code=400, message=message)


class ConflictException(AppException):
    """资源冲突（如号源已抢完）"""

    def __init__(self, message: str = "资源冲突"):
        super().__init__(code=409, message=message)
