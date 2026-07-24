from hooks.directory_agents_injector import get_directory_agents_messages

def test_no_agents_md(tmp_path):
    cwd = tmp_path / "src" / "deep"
    cwd.mkdir(parents=True)
    
    payload = {
        "cwd": str(cwd),
        "workspacePaths": [str(tmp_path)]
    }
    
    messages = get_directory_agents_messages(payload)
    assert len(messages) == 0

def test_agents_md_in_cwd(tmp_path):
    cwd = tmp_path / "src" / "deep"
    cwd.mkdir(parents=True)
    
    agents_file = cwd / "AGENTS.md"
    agents_file.write_text("Hello Deep", encoding="utf-8")
    
    payload = {
        "cwd": str(cwd),
        "workspacePaths": [str(tmp_path)]
    }
    
    messages = get_directory_agents_messages(payload)
    assert len(messages) == 1
    assert "Hello Deep" in messages[0]["ephemeralMessage"]
    assert str(cwd) in messages[0]["ephemeralMessage"]

def test_agents_md_in_parent(tmp_path):
    cwd = tmp_path / "src" / "deep"
    cwd.mkdir(parents=True)
    
    parent_dir = tmp_path / "src"
    agents_file = parent_dir / "AGENTS.md"
    agents_file.write_text("Hello Parent", encoding="utf-8")
    
    payload = {
        "cwd": str(cwd),
        "workspacePaths": [str(tmp_path)]
    }
    
    messages = get_directory_agents_messages(payload)
    assert len(messages) == 1
    assert "Hello Parent" in messages[0]["ephemeralMessage"]
    assert str(parent_dir) in messages[0]["ephemeralMessage"]

def test_agents_md_in_cwd_and_parent(tmp_path):
    cwd = tmp_path / "src" / "deep"
    cwd.mkdir(parents=True)
    
    parent_dir = tmp_path / "src"
    
    (cwd / "AGENTS.md").write_text("Deep", encoding="utf-8")
    (parent_dir / "AGENTS.md").write_text("Parent", encoding="utf-8")
    
    payload = {
        "cwd": str(cwd),
        "workspacePaths": [str(tmp_path)]
    }
    
    messages = get_directory_agents_messages(payload)
    assert len(messages) == 2
    # Reverse order: Shallowest first, Deepest last
    assert "Parent" in messages[0]["ephemeralMessage"]
    assert "Deep" in messages[1]["ephemeralMessage"]

def test_large_agents_md(tmp_path):
    cwd = tmp_path / "src"
    cwd.mkdir(parents=True)
    
    large_content = "A" * 5000
    (cwd / "AGENTS.md").write_text(large_content, encoding="utf-8")
    
    payload = {
        "cwd": str(cwd),
        "workspacePaths": [str(tmp_path)]
    }
    
    messages = get_directory_agents_messages(payload)
    assert len(messages) == 1
    msg_content = messages[0]["ephemeralMessage"]
    assert len(msg_content) < 5000
    assert "... [truncated]" in msg_content
    # Total length should be approx length of prefix + 4096 + length of "... [truncated]"
    assert "A" * 4096 in msg_content
    assert "A" * 4097 not in msg_content

def test_more_than_3_agents_md(tmp_path):
    d1 = tmp_path / "d1"
    d2 = d1 / "d2"
    d3 = d2 / "d3"
    d4 = d3 / "d4"
    d5 = d4 / "d5"
    d5.mkdir(parents=True)
    
    (d1 / "AGENTS.md").write_text("Level 1", encoding="utf-8")
    (d2 / "AGENTS.md").write_text("Level 2", encoding="utf-8")
    (d3 / "AGENTS.md").write_text("Level 3", encoding="utf-8")
    (d4 / "AGENTS.md").write_text("Level 4", encoding="utf-8")
    (d5 / "AGENTS.md").write_text("Level 5", encoding="utf-8")
    
    payload = {
        "cwd": str(d5),
        "workspacePaths": [str(tmp_path)]
    }
    
    messages = get_directory_agents_messages(payload)
    assert len(messages) == 3
    # Reverse order: d3, d4, d5 (Level 3, Level 4, Level 5) because it walks up from d5
    # Walks up: d5 -> d4 -> d3. That's 3 items. Stops there.
    # Reverses: d3, d4, d5
    assert "Level 3" in messages[0]["ephemeralMessage"]
    assert "Level 4" in messages[1]["ephemeralMessage"]
    assert "Level 5" in messages[2]["ephemeralMessage"]

def test_empty_payload(tmp_path):
    assert get_directory_agents_messages({}) == []
    assert get_directory_agents_messages({"cwd": None}) == []
    assert get_directory_agents_messages({"cwd": ""}) == []
