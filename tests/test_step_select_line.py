"""Tests for the SelectLineStep flow logic."""

from custom_components.idf_mobilite_assistant.steps.select_line import SelectLineStep
import pytest


@pytest.mark.asyncio
async def test_select_line_invalid_selection(flow_factory):
    """Ensure an invalid selection triggers an error."""
    step = flow_factory(SelectLineStep)
    step._line_results = [{"id": "A"}]

    result = await step.async_step_select_line({"selected_line": "B"})
    assert result["errors"]["base"] == "invalid_selection"


@pytest.mark.asyncio
async def test_select_line_first_entry_stores_messages_as_list(flow_factory):
    """Ensure the first message sensor is stored as a list, not a dict.

    Regression test: storing a dict made the second message impossible to add
    and broke entity creation (`msg["uuid"]` on string keys).
    """
    step = flow_factory(SelectLineStep)
    step.api_key = "FAKE"
    step._line_results = [
        {"id": "line:1", "code": "A", "commercial_mode": {"name": "RER"}}
    ]

    result = await step.async_step_select_line({"selected_line": "line:1"})

    assert result["type"] == "create_entry"
    assert isinstance(result["data"]["messages"], list)
    assert result["data"]["messages"][0]["line_id"] == "line:1"


@pytest.mark.asyncio
async def test_select_line_appends_to_existing_messages(flow_factory):
    """Ensure a second message sensor is appended to the existing list."""
    step = flow_factory(SelectLineStep)
    step.entry = type(
        "obj",
        (),
        {
            "entry_id": "entry1",
            "data": {"api_key": "FAKE", "messages": [{"uuid": "1"}]},
        },
    )()
    step._line_results = [
        {"id": "line:2", "code": "B", "commercial_mode": {"name": "RER"}}
    ]

    result = await step.async_step_select_line({"selected_line": "line:2"})

    assert result["step_id"] == "main_menu"
    assert len(step.entry.data["messages"]) == 2
    assert step.entry.data["messages"][1]["line_id"] == "line:2"
