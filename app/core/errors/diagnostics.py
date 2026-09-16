MAX_DIAGNOSTIC_LENGTH = 128


def bound_diagnostic(value: str | None) -> str | None:
    """Keep internal diagnostics within the persistence column contract."""
    if value is None:
        return None
    return value[:MAX_DIAGNOSTIC_LENGTH]
