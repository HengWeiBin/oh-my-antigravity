import os
import sys
from unittest.mock import mock_open, patch

# Ensure project root and scripts directory are on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from hooks.keyword_detector import get_keyword_detector_messages


def test_start_work_keyword():
    payload = {"prompt": "I need to $start-work now."}
    with patch("os.path.isfile", return_value=True), patch("builtins.open", mock_open(read_data="Start work content")):
        msgs = get_keyword_detector_messages(payload)
        assert len(msgs) == 1
        assert "Start work content" in msgs[0]["ephemeralMessage"]
        assert "<skill-instruction>" in msgs[0]["ephemeralMessage"]


def test_ulw_alias():
    payload = {"prompt": "Let's $ulw this"}
    with patch("os.path.isfile", return_value=True), patch("builtins.open", mock_open(read_data="Ultrawork content")):
        msgs = get_keyword_detector_messages(payload)
        assert len(msgs) == 1
        assert "Ultrawork content" in msgs[0]["ephemeralMessage"]


def test_normal_text():
    payload = {"prompt": "Just normal text, no keywords here."}
    msgs = get_keyword_detector_messages(payload)
    assert len(msgs) == 0


def test_multiple_keywords():
    payload = {"prompt": "We should $start-work and then $debugging"}
    with patch("os.path.isfile", return_value=True), patch("builtins.open", mock_open(read_data="Content")):
        msgs = get_keyword_detector_messages(payload)
        assert len(msgs) == 2


def test_duplicate_keyword():
    payload = {"prompt": "$ulw $ulw $ultrawork"}
    with patch("os.path.isfile", return_value=True), patch("builtins.open", mock_open(read_data="Content")):
        msgs = get_keyword_detector_messages(payload)
        assert len(msgs) == 1


def test_unknown_keyword():
    payload = {"prompt": "Unknown $unknown keyword"}
    msgs = get_keyword_detector_messages(payload)
    assert len(msgs) == 0


def test_forwarded_report_ignored():
    payload = {"prompt": "[REPORT] ... $ultrawork"}
    msgs = get_keyword_detector_messages(payload)
    assert len(msgs) == 0

    payload_route = {"prompt": "[agent-a -> agent-b] Result: $ultrawork"}
    msgs_route = get_keyword_detector_messages(payload_route)
    assert len(msgs_route) == 0


def test_blockquote_ignored():
    payload = {"prompt": "> $ultrawork"}
    msgs = get_keyword_detector_messages(payload)
    assert len(msgs) == 0


def test_negation_english():
    for prompt in [
        "no $ultrawork",
        "don't use $start-work",
        "do not use $start-work",
        "don't run $start-work",
        "do not run $start-work",
        "without $ultrawork",
        "skip $ultrawork",
    ]:
        payload = {"prompt": prompt}
        msgs = get_keyword_detector_messages(payload)
        assert len(msgs) == 0


def test_negation_chinese():
    for prompt in [
        "不要使用 $ulw",
        "不使用 $start-work",
        "不要 $ultrawork",
        "別用 $ultrawork",
        "不用 $ultrawork",
        "忽略 $ulw",
        "不觸發 $start-work",
    ]:
        payload = {"prompt": prompt}
        msgs = get_keyword_detector_messages(payload)
        assert len(msgs) == 0


def test_mixed_valid_and_ignored():
    payload = {"prompt": "> $ultrawork\nPlease $start-work on this"}
    with patch("os.path.isfile", return_value=True), patch("builtins.open", mock_open(read_data="Start work content")):
        msgs = get_keyword_detector_messages(payload)
        assert len(msgs) == 1
        assert "Start work content" in msgs[0]["ephemeralMessage"]

