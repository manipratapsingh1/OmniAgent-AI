from time import time

from fastapi import APIRouter, Request, Response
from starlette.responses import PlainTextResponse

# Make prometheus optional — don't hard-fail if package not installed
try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
    METRICS_ENABLED = True
except Exception:
    METRICS_ENABLED = False

router = APIRouter()

# Basic HTTP metrics
if METRICS_ENABLED:
    HTTP_REQUESTS = Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "http_status"],
    )

    HTTP_LATENCY = Histogram(
        "http_request_latency_seconds",
        "HTTP request latency",
        ["method", "endpoint"],
    )

    # Retrieval/chat-specific metrics
    RETRIEVAL_REQUESTS = Counter(
        "retrieval_requests_total",
        "Total retrieval requests",
        ["endpoint"],
    )

    RETRIEVAL_LATENCY = Histogram(
        "retrieval_request_latency_seconds",
        "Retrieval request latency",
        ["endpoint"],
    )

    CHAT_REQUESTS = Counter(
        "chat_requests_total",
        "Total chat requests",
        ["endpoint"],
    )

    CHAT_LATENCY = Histogram(
        "chat_request_latency_seconds",
        "Chat request latency",
        ["endpoint"],
    )

    CHAT_FIRST_TOKEN_LATENCY = Histogram(
        "chat_first_token_latency_seconds",
        "Time to first token for chat streaming responses",
        ["endpoint"],
    )

    CHAT_PROMPT_TOKENS = Histogram(
        "chat_prompt_tokens",
        "Estimated prompt token count for chat generation",
        ["endpoint"],
    )

    CHAT_RESPONSE_TOKENS = Histogram(
        "chat_response_tokens",
        "Estimated response token count for chat generation",
        ["endpoint"],
    )
else:
    # No-op fallbacks
    class _NoopMetric:
        def labels(self, *a, **k):
            return self

        def observe(self, *a, **k):
            return None

        def inc(self, *a, **k):
            return None

    HTTP_REQUESTS = HTTP_LATENCY = RETRIEVAL_REQUESTS = RETRIEVAL_LATENCY = CHAT_REQUESTS = CHAT_LATENCY = CHAT_FIRST_TOKEN_LATENCY = CHAT_PROMPT_TOKENS = CHAT_RESPONSE_TOKENS = _NoopMetric()
    def generate_latest():
        return b""
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"


@router.get("/metrics")
def metrics() -> Response:
    """Expose Prometheus metrics (or empty payload when disabled)."""
    data = generate_latest()
    return PlainTextResponse(data, media_type=CONTENT_TYPE_LATEST)


def prometheus_middleware(app):
    """Create a simple ASGI middleware to record basic request metrics."""

    async def middleware(request: Request, call_next):
        start = time()
        method = request.method
        # use path as endpoint label (simple)
        endpoint = request.url.path

        response = await call_next(request)

        latency = time() - start
        status = str(response.status_code)

        try:
            HTTP_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)
            HTTP_REQUESTS.labels(method=method, endpoint=endpoint, http_status=status).inc()
        except Exception:
            # metrics must not break requests
            pass

        return response

    return middleware
