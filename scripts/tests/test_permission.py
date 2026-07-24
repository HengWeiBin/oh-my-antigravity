import sys
import json
import os
import unittest
from unittest.mock import patch, MagicMock

# Import check_permission from pre_tool_use
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(f"{os.environ.get("USERPROFILE")}/.gemini/config/plugins/oh-my-antigravity/scripts"))

from pre_tool_use import check_permission

class TestOmoConstraints(unittest.TestCase):
    def setUp(self):        
        # Dynamically construct conversation IDs to avoid literal matches in transcript history
        self.sub_cid = "sub" + "agent" + "-" + "999"
        self.orch_cid = "or" + "ch" + "-" + "999"
        self.brain_dir = os.path.abspath(os.path.dirname(__file__) + "/../../../../antigravity/brain")
        os.makedirs(self.brain_dir, exist_ok=True)
        
    @patch("pre_tool_use.os.listdir")
    def test_orchestrator_product_code_denied_or_ask(self, mock_listdir):
        # Mock empty brain dir so caller is not identified as subagent
        mock_listdir.return_value = []
        
        # When caller is NOT a subagent (no other conversation links to self.orch_cid)
        # Writing to source code directly should result in "ask"
        res = check_permission(
            tool_name="write_to_file",
            file_path="src/app.py",
            conversation_id=self.orch_cid,
            brain_dir=self.brain_dir
        )
        self.assertEqual(res["permissionDecision"], "ask")
        self.assertIn("Lead Orchestrator agents do not edit source code directly", res["permissionDecisionReason"])

    @patch("pre_tool_use.os.listdir")
    def test_orchestrator_allowed_paths(self, mock_listdir):
        # Mock empty brain dir
        mock_listdir.return_value = []
        
        # Orchestrator is allowed to write to plans, omo, agents
        for path in [
            "plans/plan.md", 
            ".omo/boulder.json", 
            ".agents/hooks.json",
            "task_list.md"
        ]:
            res = check_permission(
                tool_name="write_to_file",
                file_path=path,
                conversation_id=self.orch_cid,
                brain_dir=self.brain_dir
            )
            self.assertEqual(res["permissionDecision"], "allow", f"Failed on path: {path}")

    @patch("pre_tool_use.os.listdir")
    @patch("pre_tool_use.os.path.isdir")
    @patch("pre_tool_use.os.path.exists")
    @patch("builtins.open")
    def test_subagent_omo_deny(self, mock_open, mock_exists, mock_isdir, mock_listdir):
        # Mock other conversation transcript containing the subagent's cid
        mock_listdir.return_value = ["some-parent-id"]
        mock_isdir.return_value = True
        mock_exists.return_value = True
        
        mock_file = MagicMock()
        
        # Mock file line iteration with JSONL steps
        step_n = json.dumps({
            "type": "message",
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "name": "invoke_subagent",
                        "input": {
                            "Subagents": [
                                {
                                    "TypeName": "hephaestus",
                                    "Role": "Deep Worker",
                                    "Prompt": "Do work"
                                }
                            ]
                        }
                    }
                ]
            }
        })
        step_n_plus_1 = json.dumps({
            "type": "message",
            "message": {
                "role": "toolResult",
                "toolName": "invoke_subagent",
                "content": json.dumps([
                    {
                        "conversationId": self.sub_cid
                    }
                ])
            }
        })
        
        mock_file.__iter__.return_value = [step_n, step_n_plus_1]
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Subagent writing to .omo/plans/plan.md should be denied
        res = check_permission(
            tool_name="write_to_file",
            file_path=".omo/plans/plan.md",
            conversation_id=self.sub_cid,
            brain_dir=self.brain_dir
        )
        self.assertEqual(res["permissionDecision"], "deny")
        self.assertIn("Subagents (workers) are forbidden from modifying .omo/", res["permissionDecisionReason"])

        # Subagent writing to .omo/drafts/draft.md should be denied
        res = check_permission(
            tool_name="write_to_file",
            file_path=".omo/drafts/draft.md",
            conversation_id=self.sub_cid,
            brain_dir=self.brain_dir
        )
        self.assertEqual(res["permissionDecision"], "deny")
        self.assertIn("Subagents (workers) are forbidden from modifying .omo/", res["permissionDecisionReason"])

        # Subagent writing to .omo/notepads/learnings.md should be allowed
        res = check_permission(
            tool_name="write_to_file",
            file_path=".omo/notepads/learnings.md",
            conversation_id=self.sub_cid,
            brain_dir=self.brain_dir
        )
        self.assertEqual(res["permissionDecision"], "allow")

        # Subagent writing to .omo/boulder.json should be allowed
        res = check_permission(
            tool_name="write_to_file",
            file_path=".omo/boulder.json",
            conversation_id=self.sub_cid,
            brain_dir=self.brain_dir
        )
        self.assertEqual(res["permissionDecision"], "allow")

        # Subagent writing to .agents/ should be denied
        res = check_permission(
            tool_name="write_to_file",
            file_path=".agents/hooks.json",
            conversation_id=self.sub_cid,
            brain_dir=self.brain_dir
        )
        self.assertEqual(res["permissionDecision"], "deny")

        # Subagent writing to rules/ should be denied
        res = check_permission(
            tool_name="write_to_file",
            file_path="rules/oh-my-openagent-rules.md",
            conversation_id=self.sub_cid,
            brain_dir=self.brain_dir
        )
        self.assertEqual(res["permissionDecision"], "deny")

    @patch("pre_tool_use.os.listdir")
    @patch("pre_tool_use.os.path.isdir")
    @patch("pre_tool_use.os.path.exists")
    @patch("builtins.open")
    def test_subagent_source_code_allowed(self, mock_open, mock_exists, mock_isdir, mock_listdir):
        mock_listdir.return_value = ["some-parent-id"]
        mock_isdir.return_value = True
        mock_exists.return_value = True
        
        mock_file = MagicMock()
        
        # Mock file line iteration with JSONL steps
        step_n = json.dumps({
            "type": "message",
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "name": "invoke_subagent",
                        "input": {
                            "Subagents": [
                                {
                                    "TypeName": "hephaestus",
                                    "Role": "Deep Worker",
                                    "Prompt": "Do work"
                                }
                            ]
                        }
                    }
                ]
            }
        })
        step_n_plus_1 = json.dumps({
            "type": "message",
            "message": {
                "role": "toolResult",
                "toolName": "invoke_subagent",
                "content": json.dumps([
                    {
                        "conversationId": self.sub_cid
                    }
                ])
            }
        })
        
        mock_file.__iter__.return_value = [step_n, step_n_plus_1]
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Subagent writing to source code should be allowed (that's their job!)
        res = check_permission(
            tool_name="write_to_file",
            file_path="src/app.py",
            conversation_id=self.sub_cid,
            brain_dir=self.brain_dir
        )
        self.assertEqual(res["permissionDecision"], "allow")

if __name__ == "__main__":
    unittest.main()
