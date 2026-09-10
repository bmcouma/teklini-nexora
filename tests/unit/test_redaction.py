from nexora.security.redaction import redact_secrets


def test_redacts_password_field():
    text = "config: password=SuperSecret123"
    redacted, matched = redact_secrets(text)
    assert "SuperSecret123" not in redacted
    assert "password_field" in matched


def test_redacts_aws_access_key():
    text = "Found key AKIAABCDEFGHIJKLMNOP in the log."
    redacted, matched = redact_secrets(text)
    assert "AKIAABCDEFGHIJKLMNOP" not in redacted
    assert "aws_access_key" in matched


def test_redacts_bearer_token():
    text = "Authorization: Bearer abcDEF1234567890xyzToken"
    redacted, matched = redact_secrets(text)
    assert "abcDEF1234567890xyzToken" not in redacted
    assert "bearer_token" in matched


def test_redacts_database_connection_string_credentials():
    text = "DATABASE_URL=postgresql://appuser:hunter2@db.internal:5432/prod"
    redacted, matched = redact_secrets(text)
    assert "hunter2" not in redacted
    assert "db_connection_string" in matched


def test_leaves_clean_text_unchanged():
    text = "nginx: [error] connect() failed while connecting to upstream"
    redacted, matched = redact_secrets(text)
    assert redacted == text
    assert matched == []


def test_empty_text_returns_empty_with_no_matches():
    redacted, matched = redact_secrets("")
    assert redacted == ""
    assert matched == []
