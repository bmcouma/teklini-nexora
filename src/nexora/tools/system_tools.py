"""System-level diagnostic tools.

Nexora does not have a standing agent installed on customer
infrastructure in this version. These tools operate strictly on data the
user has explicitly provided (uploaded status output, resource metrics)
or, when `use_demo_data` is set, on the bundled demo fixture. They never
claim to have observed a live system unless that data was actually
supplied.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from nexora.tools.base import BaseTool


class ServiceStatusInput(BaseModel):
    """Structured service status, either user-supplied or demo fixture data."""

    services: dict[str, str] | None = None  # e.g. {"nginx": "running", "gunicorn": "failed"}


class ServiceStatusTool(BaseTool[ServiceStatusInput, dict]):
    name = "service_status_inspection"
    description = "Reports on service status data explicitly supplied by the user or demo fixture."

    def run(self, payload: ServiceStatusInput) -> dict[str, Any]:
        if not payload.services:
            return {
                "unavailable": True,
                "unavailable_reason": (
                    "No service status data was provided. Nexora has no live agent on this "
                    "host and cannot query service state directly."
                ),
            }
        failed = [name for name, status in payload.services.items() if status.lower() != "running"]
        return {
            "unavailable": False,
            "services": payload.services,
            "failed_services": failed,
        }


class ResourceMetricsInput(BaseModel):
    cpu_percent: float | None = None
    memory_percent: float | None = None
    disk_percent: float | None = None


class ResourceInspectionTool(BaseTool[ResourceMetricsInput, dict]):
    name = "resource_inspection"
    description = "Evaluates CPU, memory, and disk metrics explicitly supplied by the user or demo fixture."

    CPU_WARN = 85.0
    MEMORY_WARN = 90.0
    DISK_WARN = 90.0

    def run(self, payload: ResourceMetricsInput) -> dict[str, Any]:
        if payload.cpu_percent is None and payload.memory_percent is None and payload.disk_percent is None:
            return {
                "unavailable": True,
                "unavailable_reason": "No resource metrics were provided.",
            }

        warnings = []
        if payload.cpu_percent is not None and payload.cpu_percent >= self.CPU_WARN:
            warnings.append(f"CPU usage at {payload.cpu_percent}% exceeds the {self.CPU_WARN}% threshold.")
        if payload.memory_percent is not None and payload.memory_percent >= self.MEMORY_WARN:
            warnings.append(
                f"Memory usage at {payload.memory_percent}% exceeds the {self.MEMORY_WARN}% threshold."
            )
        if payload.disk_percent is not None and payload.disk_percent >= self.DISK_WARN:
            warnings.append(f"Disk usage at {payload.disk_percent}% exceeds the {self.DISK_WARN}% threshold.")

        return {
            "unavailable": False,
            "cpu_percent": payload.cpu_percent,
            "memory_percent": payload.memory_percent,
            "disk_percent": payload.disk_percent,
            "warnings": warnings,
        }
