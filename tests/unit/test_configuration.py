import pytest
from app import create_app
from pydantic import ValidationError


def test_factory_accepts_isolated_configuration_override():
    app = create_app({"TESTING": True, "DATABASE_URL": "sqlite+pysqlite:///:memory:"})

    assert app.config["TESTING"] is True


def test_production_requires_database_url():
    with pytest.raises(ValidationError, match="DATABASE_URL"):
        create_app({"APP_ENV": "production"})
