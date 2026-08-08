import os
import sys

# Add scripts directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from scripts.hooks.agent_usage_reminder import get_agent_usage_reminder_messages


def test_subagent_session():
    # If is_subagent is true, should return []
    payload = {"isSubagent": True, "invocationNum": 10}
    result = get_agent_usage_reminder_messages(payload)
    assert result == []

def test_main_session_before_start():
    # invocationNum = 0, should return []
    payload = {"invocationNum": 0}
    result = get_agent_usage_reminder_messages(payload)
    assert result == []

def test_main_session_first_reminder():
    # invocationNum = 5, should return reminder
    payload = {"invocationNum": 5}
    result = get_agent_usage_reminder_messages(payload)
    assert len(result) == 1
    assert "AGENT USAGE REMINDER" in result[0]["ephemeralMessage"]

def test_main_session_second_reminder():
    # invocationNum = 15, should return reminder
    payload = {"invocationNum": 15}
    result = get_agent_usage_reminder_messages(payload)
    assert len(result) == 1
    assert "AGENT USAGE REMINDER" in result[0]["ephemeralMessage"]

def test_main_session_no_reminder_interval():
    # invocationNum = 12, should return []
    payload = {"invocationNum": 12}
    result = get_agent_usage_reminder_messages(payload)
    assert result == []
