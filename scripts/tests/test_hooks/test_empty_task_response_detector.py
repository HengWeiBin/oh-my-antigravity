from hooks.empty_task_response_detector import check_empty_task_response

WARNING_MSG = '⚠️ EMPTY SUBAGENT RESPONSE DETECTED: The subagent returned a very short or empty response. This is suspicious — the subagent may have failed silently. Please verify by checking the subagent transcript or re-dispatching with a more explicit task.'

def test_empty_string_response():
    assert check_empty_task_response('invoke_subagent', '') == WARNING_MSG

def test_none_response():
    assert check_empty_task_response('invoke_subagent', None) == WARNING_MSG

def test_done_only_response():
    assert check_empty_task_response('invoke_subagent', 'done completed ok yes') == WARNING_MSG

def test_substantial_content():
    content = "This is a substantial response that should exceed fifty meaningful characters easily once we count it up."
    assert check_empty_task_response('invoke_subagent', content) is None

def test_dict_output_meaningful():
    resp = {'output': "This is a substantial response that should exceed fifty meaningful characters easily once we count it up."}
    assert check_empty_task_response('invoke_subagent', resp) is None

def test_dict_empty_output():
    assert check_empty_task_response('invoke_subagent', {'output': ''}) == WARNING_MSG

def test_ignore_other_tools():
    assert check_empty_task_response('other_tool', '') is None
