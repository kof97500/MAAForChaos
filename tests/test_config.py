import unittest
from pathlib import Path

from czn_automation.config import load_config


class ConfigTestCase(unittest.TestCase):
    def test_load_config(self) -> None:
        root_dir = Path(__file__).resolve().parents[1]
        config = load_config(root_dir / "config" / "app.example.json")

        self.assertEqual(config.name, "czn-automation")
        self.assertTrue(config.game_window.title_keywords)
        self.assertEqual(config.game_window.supported_resolutions[0].width, 1920)
        self.assertEqual(config.game_window.supported_resolutions[0].height, 1080)
        self.assertEqual(config.input_validation.template_path, "resources/templates/kariesi_entry.png")
        self.assertEqual(config.input_validation.search_region.left, 1600)
        self.assertEqual(config.input_validation.search_region.width, 320)
