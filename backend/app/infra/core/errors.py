class AppError(Exception):
    status_code = 400
    detail = "Application error"

    def __init__(self, detail: str | None = None):
        if detail:
            self.detail = detail


class NotFoundError(AppError):
    status_code = 404
    detail = "Resource not found"


class UnauthorizedError(AppError):
    status_code = 401
    detail = "Unauthorized"


class ConflictError(AppError):
    status_code = 409
    detail = "Conflict"