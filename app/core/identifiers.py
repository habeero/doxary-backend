from uuid import UUID, uuid4


def new_opaque_id() -> str:
    return str(uuid4())


def is_opaque_id(value: str) -> bool:
    try:
        UUID(value)
    except (ValueError, TypeError, AttributeError):
        return False
    return True
