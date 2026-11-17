import pytest
from pydantic import ValidationError

from example_server.config import Settings


@pytest.fixture(autouse=True)
def clear_project_environment(monkeypatch):
    for name in (
        "GOVCODE_PROJECT_LOOKUP_ENABLED",
        "GOVCODE_PROJECT_CATALOG",
        "GOVCODE_PROJECT_SCHEMA",
        "GOVCODE_PROJECT_TABLE",
    ):
        monkeypatch.delenv(name, raising=False)


def test_project_lookup_is_disabled_by_default():
    settings = Settings(_env_file=None)

    assert settings.govcode_project_lookup_enabled is False


@pytest.mark.parametrize(
    "field",
    [
        "govcode_project_catalog",
        "govcode_project_schema",
        "govcode_project_table",
    ],
)
def test_enabled_lookup_requires_each_table_setting(field):
    values = {
        "govcode_project_lookup_enabled": True,
        "govcode_project_catalog": "test_catalog",
        "govcode_project_schema": "test_schema",
        "govcode_project_table": "test_projects",
    }
    values[field] = " "

    with pytest.raises(ValidationError, match=field.upper()):
        Settings(_env_file=None, **values)


def test_project_settings_load_from_environment(monkeypatch):
    monkeypatch.setenv("GOVCODE_PROJECT_LOOKUP_ENABLED", "true")
    monkeypatch.setenv("GOVCODE_PROJECT_CATALOG", "test_catalog")
    monkeypatch.setenv("GOVCODE_PROJECT_SCHEMA", "test_schema")
    monkeypatch.setenv("GOVCODE_PROJECT_TABLE", "test_projects")

    settings = Settings(_env_file=None)

    assert settings.govcode_project_lookup_enabled is True
    assert settings.govcode_project_catalog == "test_catalog"
    assert settings.govcode_project_schema == "test_schema"
    assert settings.govcode_project_table == "test_projects"