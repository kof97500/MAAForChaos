import unittest
from pathlib import Path

from czn_automation.config import load_config


class InputConfigTestCase(unittest.TestCase):
    def test_input_validation_defaults(self) -> None:
        root_dir = Path(__file__).resolve().parents[1]
        config = load_config(root_dir / "config" / "app.example.json")

        self.assertEqual(config.input_validation.post_click_wait_ms, 1200)
        self.assertEqual(config.input_validation.click_point.x, 1840)
        self.assertEqual(config.input_validation.click_point.y, 54)
