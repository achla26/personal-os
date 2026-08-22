from contextvars import ContextVar
import uuid

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="no_req_id")


def get_request_id() -> str:
    return request_id_ctx.get()


def set_request_id(req_id: str | None = None) -> str:
    new_id = req_id or f"req_{uuid.uuid4().hex[:12]}"
    request_id_ctx.set(new_id)
    return new_id