import threading

from app.ai.openai_provider import OpenAIAnalysisExecutor
from app.bootstrap.container import build_container
from app.core.config.settings import Settings
from app.intake.infrastructure.local_store import LocalTemporaryDocumentStore
from app.worker.runtime import AnalysisWorker


def main() -> None:
    settings = Settings.load()
    container = build_container(settings)
    stop = threading.Event()
    executor = None
    if settings.ai_enabled:
        executor = OpenAIAnalysisExecutor(
            settings.openai_api_key or "",
            settings.ai_model,
            settings.ai_timeout_seconds,
            reasoning_effort=settings.ai_reasoning_effort,
        )
    try:
        AnalysisWorker(
            container.session_factory,
            LocalTemporaryDocumentStore(settings.temporary_input_root),
            executor,
            lease_seconds=settings.worker_lease_seconds,
            poll_interval_seconds=settings.worker_poll_interval_seconds,
            max_attempts=settings.worker_max_attempts,
            retry_delay_seconds=settings.worker_retry_delay_seconds,
        ).run(stop)
    except KeyboardInterrupt:
        stop.set()


if __name__ == "__main__":
    main()
