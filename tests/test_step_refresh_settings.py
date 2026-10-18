"""Tests for the StepRefreshSettings flow logic."""

from custom_components.idf_mobilite_assistant.steps.refresh_settings import (
    StepRefreshSettings,
)
import pytest


def _fake_entry(options=None):
    """Build a minimal config entry stand-in."""
    return type(
        "obj",
        (),
        {"entry_id": "entry1", "data": {}, "options": options or {}},
    )()


@pytest.mark.asyncio
async def test_refresh_settings_shows_form_with_defaults(flow_factory):
    """Ensure the form is shown with the default interval."""
    step = flow_factory(StepRefreshSettings)
    step.entry = _fake_entry()

    result = await step.async_step_refresh_settings()

    assert result["step_id"] == "refresh_settings"
    assert result["data_schema"] is not None


@pytest.mark.asyncio
async def test_refresh_settings_saves_options(flow_factory):
    """Ensure submitted values are stored in the config entry options."""
    step = flow_factory(StepRefreshSettings)
    step.entry = _fake_entry()

    result = await step.async_step_refresh_settings(
        {"scan_interval": 300, "night_pause": True}
    )

    assert result["step_id"] == "main_menu"
    assert step.entry.options["scan_interval"] == 300
    assert step.entry.options["night_pause"] is True


@pytest.mark.asyncio
async def test_refresh_settings_keeps_unrelated_options(flow_factory):
    """Ensure existing options are preserved when saving."""
    step = flow_factory(StepRefreshSettings)
    step.entry = _fake_entry({"something_else": "keep-me"})

    await step.async_step_refresh_settings({"scan_interval": 120, "night_pause": False})

    assert step.entry.options["something_else"] == "keep-me"
    assert step.entry.options["scan_interval"] == 120
