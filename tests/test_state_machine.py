import logging
import unittest
from pathlib import Path

from czn_automation.config import load_config
from czn_automation.runtime.context import RunContext
from czn_automation.runtime.progress import ProgressReporter
from czn_automation.state_machine.kariesi_flow import KariesiEntryStateMachine, KariesiState


class KariesiEntryStateMachineTestCase(unittest.TestCase):
    def test_unknown_state_falls_back_to_failed(self) -> None:
        root_dir = Path(__file__).resolve().parents[1]
        config = load_config(root_dir / "config" / "app.example.json")
        logger = logging.getLogger(f"state_machine_test_logger_{id(self)}")
        logger.handlers.clear()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.NullHandler())
        context = RunContext(
            root_dir=root_dir,
            logger=logger,
            progress=ProgressReporter(),
            config=config,
        )

        flow = KariesiEntryStateMachine(context)
        result_state = flow._handle_state(KariesiState.SUCCESS)

        self.assertEqual(result_state, KariesiState.FAILED)
        self.assertIn("未实现的状态处理器", flow.failure_reason)
