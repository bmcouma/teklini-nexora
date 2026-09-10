"""Evaluation dataset.

Each case pairs a realistic incident input with the expected
classification and root-cause signal, so the evaluation harness can
check the workflow's output against a known-good answer without needing
a live LLM judge for the deterministic parts of the pipeline.
"""

from __future__ import annotations

from pydantic import BaseModel

from nexora.models.incident import IncidentCategory


class EvaluationCase(BaseModel):
    case_id: str
    title: str
    description: str
    logs: str | None = None
    expected_category: IncidentCategory
    expected_root_cause_keyword: str


EVALUATION_CASES: list[EvaluationCase] = [
    EvaluationCase(
        case_id="eval-01",
        title="Django application returns 502 Bad Gateway",
        description="Users report 502 errors. Nginx is reachable but upstream requests fail.",
        logs=(
            "nginx: [error] connect() failed (111: Connection refused) while connecting to upstream\n"
            "gunicorn[3341]: ModuleNotFoundError: No module named 'config.settings'\n"
            "gunicorn[3341]: Worker failed to start.\n"
        ),
        expected_category=IncidentCategory.NETWORK,
        expected_root_cause_keyword="failed to start",
    ),
    EvaluationCase(
        case_id="eval-02",
        title="DNS misconfiguration",
        description="The application cannot resolve the hostname of its payment gateway.",
        logs="socket.gaierror: [Errno -2] Name or service not known\n",
        expected_category=IncidentCategory.UNKNOWN,
        expected_root_cause_keyword="dns",
    ),
    EvaluationCase(
        case_id="eval-03",
        title="PostgreSQL connection failure",
        description="The API cannot connect to its PostgreSQL database.",
        logs="psycopg2.OperationalError: could not connect to server: Connection refused\n",
        expected_category=IncidentCategory.DATABASE,
        expected_root_cause_keyword="connect",
    ),
    EvaluationCase(
        case_id="eval-04",
        title="Disk full on application host",
        description="The application host has run out of disk space and writes are failing.",
        logs="OSError: [Errno 28] No space left on device\n",
        expected_category=IncidentCategory.UNKNOWN,
        expected_root_cause_keyword="disk",
    ),
    EvaluationCase(
        case_id="eval-05",
        title="Expired TLS certificate",
        description="Clients report SSL errors connecting to the API over HTTPS.",
        logs="SSL: CERTIFICATE_VERIFY_FAILED certificate has expired\n",
        expected_category=IncidentCategory.NETWORK,
        expected_root_cause_keyword="tls",
    ),
    EvaluationCase(
        case_id="eval-06",
        title="Nginx upstream mismatch",
        description="Nginx is returning 504 Gateway Timeout for all requests to the API service.",
        logs="nginx: [error] upstream timed out (110: Connection timed out) while reading response header\n",
        expected_category=IncidentCategory.NETWORK,
        expected_root_cause_keyword="timing out",
    ),
    EvaluationCase(
        case_id="eval-07",
        title="Incorrect environment variable",
        description="The application fails to start because a required configuration value is missing.",
        logs="config error: missing environment variable DATABASE_URL\n",
        expected_category=IncidentCategory.UNKNOWN,
        expected_root_cause_keyword="configuration",
    ),
    EvaluationCase(
        case_id="eval-08",
        title="API timeout problem",
        description="Requests to the third-party billing API are timing out intermittently.",
        logs="httpx.ReadTimeout: The read operation timed out\n",
        expected_category=IncidentCategory.API,
        expected_root_cause_keyword="timing out",
    ),
    EvaluationCase(
        case_id="eval-09",
        title="Docker container crash",
        description="The worker container keeps exiting shortly after startup.",
        logs="worker_1 exited with code 137\nsystemd: worker.service: Failed with result 'exit-code'.\n",
        expected_category=IncidentCategory.INFRASTRUCTURE,
        expected_root_cause_keyword="failed to start",
    ),
    EvaluationCase(
        case_id="eval-10",
        title="Authentication configuration problem",
        description="All login attempts are failing with 401 Unauthorized since the last deployment.",
        logs="401 Unauthorized\nauthentication failed: invalid credentials\n",
        expected_category=IncidentCategory.AUTHENTICATION,
        expected_root_cause_keyword="authentication",
    ),
]
