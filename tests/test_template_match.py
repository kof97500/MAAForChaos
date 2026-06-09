import unittest
from pathlib import Path

from czn_automation.config import SearchRegion
from czn_automation.recognition.template_match import TemplateMatcher


class TemplateMatcherTestCase(unittest.TestCase):
    def test_match_kariesi_template_in_reference_image(self) -> None:
        root_dir = Path(__file__).resolve().parents[1]
        matcher = TemplateMatcher()
        result = matcher.find_in_image(
            screenshot_path=Path("/private/tmp/czn_click_ref.png"),
            template_path=root_dir / "resources" / "templates" / "kariesi_icon.png",
            search_region=SearchRegion(left=1660, top=410, width=220, height=140),
            threshold=18.0,
            step=2,
        )

        self.assertTrue(result.found, result.summary())
        self.assertLessEqual(result.score, 1.0)
        self.assertEqual(result.left, 1778)
        self.assertEqual(result.top, 426)
