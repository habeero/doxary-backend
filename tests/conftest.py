import pytest
from app import create_app
from app.core.database import Base


@pytest.fixture
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "DATABASE_URL": "sqlite+pysqlite:///:memory:",
            "TEMPORARY_INPUT_ROOT": tmp_path / "inputs",
        }
    )
    Base.metadata.create_all(application.extensions["doxary_container"].engine)
    return application


@pytest.fixture
def client(app):
    return app.test_client()
