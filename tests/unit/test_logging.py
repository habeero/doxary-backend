import logging

from app.core.logging.configure import JsonFormatter


def test_structured_log_formatter_excludes_sensitive_extra_fields():
    record = logging.LogRecord("test", logging.INFO, "", 0, "request_completed", (), None)
    record.request_id = "request-id"
    record.raw_document_text = "secret document contents"

    rendered = JsonFormatter().format(record)

    assert "request-id" in rendered
    assert "secret document contents" not in rendered
