import unittest
from pathlib import Path

from czn_automation.config import load_config


class InputConfigTestCase(unittest.TestCase):
    def test_input_validation_defaults(self) -> None:
        root_dir = Path(__file__).resolve().parents[1]
        config = load_config(root_dir / "config" / "app.example.json")

        self.assertEqual(config.input_validation.post_click_wait_ms, 400)
        self.assertEqual(config.input_validation.template_path, "resources/templates/kariesi_entry.png")
        self.assertEqual(config.input_validation.search_region.left, 1600)
        self.assertEqual(config.input_validation.search_region.top, 390)
        self.assertEqual(config.input_validation.search_region.width, 320)
        self.assertEqual(config.input_validation.search_region.height, 220)
        self.assertEqual(config.input_validation.search_step, 2)
        self.assertEqual(config.input_validation.success_template_path, "resources/templates/kariesi_page_header.png")
        self.assertEqual(config.input_validation.success_search_region.width, 360)
        self.assertEqual(config.input_validation.success_timeout_ms, 8000)
        self.assertEqual(config.zero_system.template_path, "resources/templates/zero_system_entry.png")
        self.assertEqual(config.zero_system.search_region.left, 1020)
        self.assertEqual(config.zero_system.detect_timeout_ms, 8000)
        self.assertEqual(config.zero_system.detect_poll_interval_ms, 500)
        self.assertEqual(config.zero_system.success_template_path, "resources/templates/zero_system_page_header.png")
        self.assertEqual(config.zero_system.success_search_region.width, 360)
        self.assertEqual(config.zero_system.success_timeout_ms, 8000)
        self.assertEqual(config.codex_flow.button_template_path, "resources/templates/codex_button.png")
        self.assertEqual(config.codex_flow.button_search_region.left, 1200)
        self.assertEqual(config.codex_flow.page_template_path, "resources/templates/first_codex_entry.png")
        self.assertEqual(config.codex_flow.enter_button_template_path, "resources/templates/codex_enter_button.png")
        self.assertEqual(config.team_setup.page_template_path, "resources/templates/team_config_page_header.png")
        self.assertEqual(config.team_setup.enter_button_template_path, "resources/templates/team_config_enter_button.png")
        self.assertEqual(config.team_setup.success_template_path, "resources/templates/roguelike_entry_top_right.png")
        self.assertEqual(config.team_setup.success_search_region.left, 1500)
        self.assertEqual(config.team_setup.transition_timeout_ms, 8000)
