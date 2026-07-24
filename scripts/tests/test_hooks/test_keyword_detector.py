from unittest.mock import patch, mock_open

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
