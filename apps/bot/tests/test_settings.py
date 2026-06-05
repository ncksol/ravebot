import importlib


def reload_settings(
    monkeypatch, announcement_chat_id=None, interval=None, first_run=None
):
    required_env = {
        "BOT_TOKEN": "dummy-token",
        "ADMIN_ID": "123456",
        "TEAMUP_API_KEY": "dummy-teamup-api-key",
        "TEAMUP_CALENDAR_KEY": "dummy-calendar-key",
        "TEAMUP_CALENDAR_READER_KEY": "dummy-reader-key",
        "TEAMUP_SUBCALENDAR_ID": "dummy-subcalendar-id",
        "RA_QUERY_TEMPLATE_PATH": "graphql_query_template.json",
    }
    for key, value in required_env.items():
        monkeypatch.setenv(key, value)

    if announcement_chat_id is None:
        monkeypatch.delenv("ANNOUNCEMENT_CHAT_ID", raising=False)
    else:
        monkeypatch.setenv("ANNOUNCEMENT_CHAT_ID", announcement_chat_id)

    if interval is None:
        monkeypatch.delenv("ANNOUNCEMENT_INTERVAL_SECONDS", raising=False)
    else:
        monkeypatch.setenv("ANNOUNCEMENT_INTERVAL_SECONDS", interval)

    if first_run is None:
        monkeypatch.delenv("ANNOUNCEMENT_FIRST_RUN_SECONDS", raising=False)
    else:
        monkeypatch.setenv("ANNOUNCEMENT_FIRST_RUN_SECONDS", first_run)

    import settings

    return importlib.reload(settings)


def test_announcement_configuration_defaults_when_chat_not_configured(monkeypatch):
    settings = reload_settings(monkeypatch)

    assert settings.AnnouncementConfiguration.chat_id is None
    assert settings.AnnouncementConfiguration.interval_seconds == 3600
    assert settings.AnnouncementConfiguration.first_run_seconds == 60


def test_announcement_configuration_parses_environment(monkeypatch):
    settings = reload_settings(
        monkeypatch,
        announcement_chat_id="-1001234567890",
        interval="1800",
        first_run="15",
    )

    assert settings.AnnouncementConfiguration.chat_id == -1001234567890
    assert settings.AnnouncementConfiguration.interval_seconds == 1800
    assert settings.AnnouncementConfiguration.first_run_seconds == 15


def test_announcement_configuration_chat_id_empty_string_results_in_none(monkeypatch):
    settings = reload_settings(monkeypatch, announcement_chat_id="")

    assert settings.AnnouncementConfiguration.chat_id is None


def test_announcement_configuration_malformed_integer_raises_value_error(monkeypatch):
    import pytest

    with pytest.raises(ValueError):
        reload_settings(monkeypatch, interval="not-a-number")
