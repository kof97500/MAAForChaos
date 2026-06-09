import unittest
from pathlib import Path

from czn_automation.config import load_config


class InputConfigTestCase(unittest.TestCase):
    def test_input_validation_defaults(self) -> None:
        root_dir = Path(__file__).resolve().parents[1]
        config = load_config(root_dir / "config" / "app.example.json")

        self.assertEqual(config.input_validation.post_click_wait_ms, 400)
        self.assertEqual(config.input_validation.template_path, "resources/templates/kariesi_icon.png")
        self.assertEqual(config.input_validation.search_region.left, 1660)
        self.assertEqual(config.input_validation.search_region.top, 410)
        self.assertEqual(config.input_validation.search_region.width, 220)
        self.assertEqual(config.input_validation.search_region.height, 140)
        self.assertEqual(config.input_validation.search_step, 2)
        self.assertEqual(config.input_validation.success_template_path, "resources/templates/kariesi_page_header.png")
        self.assertEqual(config.input_validation.success_search_region.width, 360)
        self.assertEqual(config.input_validation.success_timeout_ms, 8000)
