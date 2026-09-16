import threading

from app.bootstrap.container import build_container
from app.core.config.settings import Settings
from app.intake.infrastructure.local_store import LocalTemporaryDocumentStore
from app.worker.runtime import AnalysisWorker


def main() -> None:
    settings = Settings.load()
    container = build_container(settings)
    stop = threading.Event()
    try:
        AnalysisWorker(
            container.session_factory,
            LocalTemporaryDocumentStore(settings.temporary_input_root),
            lease_seconds=settings.worker_lease_seconds,
            poll_interval_seconds=settings.worker_poll_interval_seconds,
            max_attempts=settings.worker_max_attempts,
            retry_delay_seconds=settings.worker_retry_delay_seconds,
        ).run(stop)
    except KeyboardInterrupt:
        stop.set()


if __name__ == "__main__":
    main()
