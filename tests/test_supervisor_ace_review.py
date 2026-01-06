
import json
import os
import shutil
import tempfile
import time
import unittest
from unittest.mock import MagicMock

# Import the SupervisorBrain class (assuming it's importable from where we run tests)
# We might need to adjust sys.path if running this directly
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from codingos.mcp.supervisor import SupervisorBrain, PipelinePhase, AgentInfo
from codingos.runtime.models import ArchitectureData

class TestSupervisorAceReview(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_root = os.path.join(self.test_dir, "fake_repo")
        os.makedirs(self.repo_root, exist_ok=True)
        self.memory_path = os.path.join(self.repo_root, ".gemini", "memory")
        
        # Initialize Primary Brain
        self.primary = SupervisorBrain(self.repo_root, self.memory_path, instance_role="PRIMARY")
        
        # Setup initial state for Phase 4
        self.primary.phase = PipelinePhase.PHASE_4_EXECUTION
        self.primary.architecture = ArchitectureData(
            current_state="Empty",
            expected_state="Full App",
            subtasks=[
                "Task 1: Setup DB",
                "Task 2: Create API"
            ]
        )
        self.primary.current_subtask_index = 0
        self.primary._primary_initialized = True
        
        # Satisfy bootstrap gating
        from codingos.mcp.supervisor import ManagerAction
        import time
        self.primary._spawn_count = 1
        self.primary._manager_actions = [
            ManagerAction(id="1", title="Scan rápido do repo (Context Scout)", instructions="", created_at=time.time(), status="done"),
            ManagerAction(id="2", title="Decidir pool e spawn", instructions="", created_at=time.time(), status="done")
        ]
        
        self.primary._persist()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_review_flow_and_ace(self):
        # 1. Worker claims task
        worker = SupervisorBrain(self.repo_root, self.memory_path, instance_role="WORKER_1")
        msg = worker.get_next_subtask()
        self.assertIn("Task 1", msg)
        
        # Verify claim
        self.primary._sync()
        self.assertEqual(self.primary._subtask_claims.get("0"), "WORKER_1")

        # 2. Worker reports completion
        # Expected behavior AFTER changes: marks as review_pending
        worker.report_subtask_success("Implemented DB schema")
        
        self.primary._sync()
        status = self.primary._get_subtask_status(0)
        self.assertEqual(status["status"], "review_pending")
        self.assertEqual(status["result_summary"], "Implemented DB schema")
        
        # 3. Reviewer Rejects
        reviewer = SupervisorBrain(self.repo_root, self.memory_path, instance_role="REVIEWER_1")
        
        # New API call we want to implement:
        result = reviewer.reject_subtask(0, "Missing indexes", ace_insight="Always add indexes on FKs")
        self.assertIn("REJEITADA", result)
        
        self.primary._sync()
        status = self.primary._get_subtask_status(0)
        self.assertEqual(status["status"], "rejected")
        
        # 4. Check ACE memory updated
        # We implemented a simplified list in state for this turn
        self.assertTrue(any("Always add indexes" in e["content"] for e in self.primary._ace_playbook))
        
        # 5. Worker retries
        # Worker should see the rejection reason and ACE insight in the new prompt
        msg = worker.get_next_subtask()
        self.assertIn("Missing indexes", msg) # Rejection reason
        self.assertIn("Always add indexes", msg) # ACE Insight
        
        # 6. Worker fixes and resubmits
        worker.report_subtask_success("Fixed indexes")
        
        # 7. Reviewer Approves
        reviewer.approve_subtask(0, "All good now", ace_insight="Great job on indexes")
        
        self.primary._sync()
        status = self.primary._get_subtask_status(0)
        self.assertEqual(status["status"], "approved")
        self.assertTrue(any("Great job" in e["content"] for e in self.primary._ace_playbook))

if __name__ == "__main__":
    unittest.main()
