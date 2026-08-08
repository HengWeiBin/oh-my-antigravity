import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'hooks')))
from plan_format_validator import check_plan_format


def test_non_plan_file():
    tool_input = {
        'TargetFile': 'C:\\Users\\K20879\\.gemini\\config\\plugins\\oh-my-antigravity\\some_file.md',
        'CodeContent': '## TL;DR\n\n## Todos\n- [ ] Task\n\n## Dependency Matrix\n'
    }
    assert check_plan_format('write_to_file', tool_input, None) is None

def test_non_md_file():
    tool_input = {
        'TargetFile': '/path/to/.omo/plans/some_file.json',
        'CodeContent': '{}'
    }
    assert check_plan_format('write_to_file', tool_input, None) is None

def test_valid_plan():
    tool_input = {
        'TargetFile': '/path/to/.omo/plans/plan.md',
        'CodeContent': '## TL;DR\nsummary\n## Todos\n- [ ] Task\n## Dependency Matrix\nnone'
    }
    assert check_plan_format('write_to_file', tool_input, None) is None

def test_missing_tldr():
    tool_input = {
        'TargetFile': '/path/to/.omo/plans/plan.md',
        'CodeContent': '## Todos\n- [ ] Task\n## Dependency Matrix\n'
    }
    res = check_plan_format('write_to_file', tool_input, None)
    assert res is not None
    assert '## TL;DR' in res

def test_missing_todos():
    tool_input = {
        'TargetFile': '/path/to/.omo/plans/plan.md',
        'CodeContent': '## TL;DR\nsummary\n## Dependency Matrix\n'
    }
    res = check_plan_format('write_to_file', tool_input, None)
    assert res is not None
    assert '## Todos' in res

def test_missing_checkboxes():
    tool_input = {
        'TargetFile': '/path/to/.omo/plans/plan.md',
        'CodeContent': '## TL;DR\nsummary\n## Todos\nTask 1\n## Dependency Matrix\n'
    }
    res = check_plan_format('write_to_file', tool_input, None)
    assert res is not None
    assert 'Checkboxes' in res

def test_missing_multiple():
    tool_input = {
        'TargetFile': '/path/to/.omo/plans/plan.md',
        'CodeContent': 'just some text'
    }
    res = check_plan_format('write_to_file', tool_input, None)
    assert res is not None
    assert '## TL;DR' in res
    assert '## Todos' in res
    assert '## Dependency Matrix' in res

def test_replace_file_content_valid():
    import shutil
    temp_dir = tempfile.mkdtemp()
    plans_dir = os.path.join(temp_dir, '.omo', 'plans')
    os.makedirs(plans_dir)
    test_file = os.path.join(plans_dir, 'test_plan.md')
    
    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write('## TL;DR\nsummary\n## Todos\n- [ ] Task\n## Dependency Matrix\nnone')
            
        tool_input = {
            'TargetFile': test_file
        }
        
        assert check_plan_format('replace_file_content', tool_input, None) is None
        
    finally:
        shutil.rmtree(temp_dir)
