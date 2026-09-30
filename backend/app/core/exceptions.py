"""
业务异常与全局异常处理
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class BusinessException(Exception):
    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code


class NotFoundException(BusinessException):
    def __init__(self, message: str = "资源不存在"):
        super().__init__(message, code=404)


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(BusinessException)
    async def business_handler(request: Request, exc: BusinessException):
        return JSONResponse(status_code=exc.code, content={"code": exc.code, "message": exc.message})

    @app.exception_handler(Exception)
    async def global_handler(request: Request, exc: Exception):
        return JSONResponse(status_code=500, content={"code": 500, "message": f"服务器内部错误: {exc}"})
