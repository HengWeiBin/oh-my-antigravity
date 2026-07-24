import sys
import os
import tempfile
import pytest
import shutil

scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from hooks.rules_injector import get_rules_messages  # noqa: E402

@pytest.fixture
def workspace():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_no_rules(workspace):
    payload = {"context": {"workspaceUri": f"file:///{workspace.replace(os.sep, '/')}"}}
    messages = get_rules_messages(payload)
    assert len(messages) == 0

def test_root_rules(workspace):
    with open(os.path.join(workspace, ".rules"), "w") as f:
        f.write("root rules")
    
    payload = {"context": {"workspaceUri": f"file:///{workspace.replace(os.sep, '/')}"}}
    messages = get_rules_messages(payload)
    assert len(messages) == 1
    assert "root rules" in messages[0]["ephemeralMessage"]

def test_glob_rules(workspace):
    os.makedirs(os.path.join(workspace, "rules"))
    with open(os.path.join(workspace, "rules", "test1.md"), "w") as f:
        f.write("glob rules test1")
        
    payload = {"context": {"workspaceUri": f"file:///{workspace.replace(os.sep, '/')}"}}
    messages = get_rules_messages(payload)
    assert len(messages) == 1
    assert "glob rules test1" in messages[0]["ephemeralMessage"]

def test_multiple_and_limit(workspace):
    os.makedirs(os.path.join(workspace, "rules"))
    for i in range(10):
        with open(os.path.join(workspace, "rules", f"test{i}.md"), "w") as f:
            f.write(f"rule {i}")
            
    payload = {"context": {"workspaceUri": f"file:///{workspace.replace(os.sep, '/')}"}}
    messages = get_rules_messages(payload)
    assert len(messages) == 5

def test_truncate_large_file(workspace):
    large_content = "A" * 3000
    with open(os.path.join(workspace, ".rules"), "w") as f:
        f.write(large_content)
        
    payload = {"context": {"workspaceUri": f"file:///{workspace.replace(os.sep, '/')}"}}
    messages = get_rules_messages(payload)
    assert len(messages) == 1
    content_in_msg = messages[0]["ephemeralMessage"].split(":\n\n")[1]
    assert len(content_in_msg) == 2048
