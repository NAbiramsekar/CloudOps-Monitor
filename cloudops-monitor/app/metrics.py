from time import monotonic

from prometheus_client import Counter, Gauge, Histogram

APP_START_TIME = monotonic()

REQUEST_COUNT = Counter(
    "cloudops_http_requests_total",
    "Total HTTP requests processed by CloudOps Monitor.",
    ["method", "path", "status_code"],
)
REQUEST_DURATION = Histogram(
    "cloudops_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "path"],
)
ERROR_COUNT = Counter(
    "cloudops_http_errors_total",
    "Total HTTP responses with status code >= 500.",
    ["method", "path", "status_code"],
)
APP_UPTIME = Gauge(
    "cloudops_application_uptime_seconds",
    "Application uptime in seconds.",
)


def update_uptime() -> float:
    uptime = monotonic() - APP_START_TIME
    APP_UPTIME.set(uptime)
    return uptime
