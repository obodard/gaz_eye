"""Tests for agent/agent.py — tool functions and root_agent definition."""

from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Tool function return values (AC2)
# ---------------------------------------------------------------------------

class TestToolFunctions:
    """Each tool function returns {"ok": True} with valid arguments."""

    def test_submit_trip_all_params(self):
        """submit_trip with all params returns {"ok": True}."""
        from agent.agent import submit_trip

        result = submit_trip(
            origin="Montréal",
            destination="Duhamel",
            range_km=180.0,
            waypoints=["Grenville"],
        )
        assert result == {"ok": True}

    def test_submit_trip_optional_none(self):
        """submit_trip with optional params as None returns {"ok": True}."""
        from agent.agent import submit_trip

        result = submit_trip(origin="Montréal", destination="Québec")
        assert result == {"ok": True}

    def test_submit_trip_range_only(self):
        """submit_trip with range_km but no waypoints returns {"ok": True}."""
        from agent.agent import submit_trip

        result = submit_trip(origin="Montréal", destination="Duhamel", range_km=200.0)
        assert result == {"ok": True}

    def test_add_waypoint(self):
        """add_waypoint returns {"ok": True}."""
        from agent.agent import add_waypoint

        result = add_waypoint(waypoint="Grenville")
        assert result == {"ok": True}

    def test_filter_stations_by_area(self):
        """filter_stations_by_area returns {"ok": True}."""
        from agent.agent import filter_stations_by_area

        result = filter_stations_by_area(area_name="Lachute", lat=45.65, lng=-74.34)
        assert result == {"ok": True}

    def test_clear_filter(self):
        """clear_filter returns {"ok": True}."""
        from agent.agent import clear_filter

        result = clear_filter()
        assert result == {"ok": True}


# ---------------------------------------------------------------------------
# Agent definition (AC1)
# ---------------------------------------------------------------------------

class TestRootAgent:
    """root_agent is an Agent instance with correct name and model."""

    def test_root_agent_is_agent_instance(self):
        """root_agent should be an instance of google.adk.Agent."""
        from google.adk import Agent
        from agent.agent import root_agent

        assert isinstance(root_agent, Agent)

    def test_root_agent_name(self):
        """root_agent.name should be 'gaz_eye_assistant'."""
        from agent.agent import root_agent

        assert root_agent.name == "gaz_eye_assistant"

    def test_root_agent_model(self):
        """root_agent.model should be 'gemini-2.0-flash'."""
        from agent.agent import root_agent

        assert root_agent.model == "gemini-2.0-flash"


# ---------------------------------------------------------------------------
# System instruction (AC3)
# ---------------------------------------------------------------------------

class TestSystemInstruction:
    """SYSTEM_INSTRUCTION contains all five behavioral rules."""

    def test_instruction_contains_tool_call_rule(self):
        """Rule 1: always call a tool when intent matches."""
        from agent.agent import SYSTEM_INSTRUCTION

        assert "call a tool" in SYSTEM_INSTRUCTION.lower()

    def test_instruction_contains_clarifying_question_rule(self):
        """Rule 2: ask clarifying question for missing fields."""
        from agent.agent import SYSTEM_INSTRUCTION

        assert "clarifying question" in SYSTEM_INSTRUCTION.lower()

    def test_instruction_contains_language_rule(self):
        """Rule 3: respond in user's language."""
        from agent.agent import SYSTEM_INSTRUCTION

        assert "french" in SYSTEM_INSTRUCTION.lower()
        assert "english" in SYSTEM_INSTRUCTION.lower()

    def test_instruction_contains_confirmation_rule(self):
        """Rule 4: confirm action in 1-2 sentences."""
        from agent.agent import SYSTEM_INSTRUCTION

        assert "1–2 sentences" in SYSTEM_INSTRUCTION or "1-2 sentences" in SYSTEM_INSTRUCTION

    def test_instruction_contains_no_invention_rule(self):
        """Rule 5: do not invent station names, prices, or route details."""
        from agent.agent import SYSTEM_INSTRUCTION

        assert "invent" in SYSTEM_INSTRUCTION.lower()


# ---------------------------------------------------------------------------
# Package export (AC1)
# ---------------------------------------------------------------------------

class TestPackageExport:
    """agent/__init__.py exports root_agent."""

    def test_import_root_agent_from_package(self):
        """root_agent is importable from the agent package."""
        from agent import root_agent

        assert root_agent.name == "gaz_eye_assistant"
