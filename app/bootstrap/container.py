from dataclasses import dataclass

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config.settings import Settings


@dataclass(frozen=True)
class Container:
    """Concrete infrastructure composed for one application instance."""

    settings: Settings
    engine: Engine
    session_factory: sessionmaker[Session]


def build_container(settings: Settings) -> Container:
    engine = create_engine(settings.resolved_database_url, pool_pre_ping=True)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    return Container(settings=settings, engine=engine, session_factory=session_factory)
