from sqlalchemy.orm import Session

from app.usage.infrastructure.usage_event_record import UsageEventRecord


class SqlAlchemyUsageLedger:
    """Stages immutable usage records; callers own the transaction."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def append(self, event: UsageEventRecord) -> None:
        self._session.add(event)
