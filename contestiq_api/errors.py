from __future__ import annotations

from fastapi import HTTPException


class APIError(Exception):
    def __init__(self, error_code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.status_code = status_code


def http_error(error: APIError) -> HTTPException:
    return HTTPException(
        status_code=error.status_code,
        detail={
            "status": "failed",
            "error_code": error.error_code,
            "message": error.message,
        },
    )
