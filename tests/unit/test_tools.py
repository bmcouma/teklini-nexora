from nexora.tools.application_tools import (
    EnvironmentVariableCheckInput,
    EnvironmentVariableCheckTool,
    FrameworkDetectionInput,
    FrameworkDetectionTool,
)
from nexora.tools.log_tools import LogAnalysisTool, LogParseInput
from nexora.tools.system_tools import ResourceInspectionTool, ResourceMetricsInput


def test_log_analysis_reports_unavailable_for_empty_input():
    result = LogAnalysisTool().execute(LogParseInput(log_text=""), "INC-TEST")
    assert result.data["unavailable"] is True


def test_log_analysis_detects_known_signals():
    log_text = "2026-01-01 error: connection refused while connecting to upstream"
    result = LogAnalysisTool().execute(LogParseInput(log_text=log_text), "INC-TEST")
    assert result.data["unavailable"] is False
    assert "connection_refused" in result.data["signals_detected"]


def test_framework_detection_finds_django():
    result = FrameworkDetectionTool().execute(
        FrameworkDetectionInput(log_text="django.core.exceptions.ImproperlyConfigured"), "INC-TEST"
    )
    assert "django" in result.data["frameworks_detected"]


def test_environment_variable_check_flags_missing_and_empty():
    result = EnvironmentVariableCheckTool().execute(
        EnvironmentVariableCheckInput(
            required_vars=["DATABASE_URL", "SECRET_KEY", "DJANGO_SETTINGS_MODULE"],
            provided_vars={"DATABASE_URL": "postgres://x", "DJANGO_SETTINGS_MODULE": ""},
        ),
        "INC-TEST",
    )
    assert "SECRET_KEY" in result.data["missing_vars"]
    assert "DJANGO_SETTINGS_MODULE" in result.data["empty_vars"]


def test_resource_inspection_flags_high_disk_usage():
    result = ResourceInspectionTool().execute(ResourceMetricsInput(disk_percent=95.0), "INC-TEST")
    assert result.data["warnings"]
    assert "Disk usage" in result.data["warnings"][0]


def test_resource_inspection_unavailable_without_any_metric():
    result = ResourceInspectionTool().execute(ResourceMetricsInput(), "INC-TEST")
    assert result.data["unavailable"] is True


def test_tool_execution_never_raises_and_captures_errors():
    class ExplodingTool(LogAnalysisTool):
        def run(self, payload):
            raise RuntimeError("boom")

    result = ExplodingTool().execute(LogParseInput(log_text="x"), "INC-TEST")
    assert result.success is False
    assert "boom" in result.error
