"""Bundled demo incident data.

This fixture lets Nexora be demonstrated end-to-end without access to
real infrastructure. It is clearly labeled as demo data everywhere it
surfaces, in the UI and in the generated report.
"""

from __future__ import annotations

DEMO_INCIDENT_TITLE = "Django application returns 502 Bad Gateway"

DEMO_INCIDENT_DESCRIPTION = (
    "Users report that the production Django application is returning "
    "502 Bad Gateway errors starting approximately 10 minutes ago. "
    "Nginx is reachable but upstream requests are failing."
)

DEMO_LOG_TEXT = """\
2026-08-15 09:12:01 nginx: [error] connect() failed (111: Connection refused) while connecting to upstream
2026-08-15 09:12:01 nginx: upstream: "http://127.0.0.1:8000/"
2026-08-15 09:11:58 gunicorn[3341]: Traceback (most recent call last):
2026-08-15 09:11:58 gunicorn[3341]: ModuleNotFoundError: No module named 'config.settings'
2026-08-15 09:11:58 gunicorn[3341]: Worker failed to start.
2026-08-15 09:11:58 systemd: gunicorn.service: Failed with result 'exit-code'.
2026-08-15 09:11:59 systemd: gunicorn.service: Scheduled restart job, restart counter is at 3.
"""

DEMO_SERVICE_STATUS = {
    "nginx": "running",
    "gunicorn": "failed",
    "postgresql": "running",
}

DEMO_RESOURCE_METRICS = {
    "cpu_percent": 12.0,
    "memory_percent": 41.0,
    "disk_percent": 38.0,
}

DEMO_ENVIRONMENT_VARS = {
    "DJANGO_SETTINGS_MODULE": "",
    "DATABASE_URL": "postgres://app:***@localhost:5432/app",
    "SECRET_KEY": "***",
}

DEMO_REQUIRED_ENV_VARS = ["DJANGO_SETTINGS_MODULE", "DATABASE_URL", "SECRET_KEY"]

DEMO_TCP_CHECK = {"host": "127.0.0.1", "port": 8000, "reachable": False}


def get_demo_context() -> dict:
    """Return the full demo fixture bundle used by tools when use_demo_data is set."""
    return {
        "log_text": DEMO_LOG_TEXT,
        "services": DEMO_SERVICE_STATUS,
        "resources": DEMO_RESOURCE_METRICS,
        "env_vars": DEMO_ENVIRONMENT_VARS,
        "required_env_vars": DEMO_REQUIRED_ENV_VARS,
        "tcp_check": DEMO_TCP_CHECK,
    }
