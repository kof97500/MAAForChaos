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
            template_path=root_dir / "resources" / "templates" / "kariesi_entry.png",
            search_region=SearchRegion(left=1600, top=390, width=320, height=220),
            threshold=25.0,
            step=2,
        )

        self.assertTrue(result.found, result.summary())
        self.assertLessEqual(result.score, 25.0)
        self.assertEqual(result.left, 1647)
        self.assertEqual(result.top, 433)

    def test_match_kariesi_page_header_template(self) -> None:
        root_dir = Path(__file__).resolve().parents[1]
        matcher = TemplateMatcher()
        result = matcher.find_in_image(
            screenshot_path=Path(
                "/Users/michael/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/"
                "michael-lyr_3e43/temp/RWTemp/2026-06/52a1ab9b3472a7f71ab346a045b579f6/"
                "752cddee3f7ca6066d8409c03117e5a6.jpg"
            ),
            template_path=root_dir / "resources" / "templates" / "kariesi_page_header.png",
            search_region=SearchRegion(left=0, top=0, width=360, height=120),
            threshold=20.0,
            step=1,
        )

        self.assertTrue(result.found, result.summary())
        self.assertLessEqual(result.score, 1.0)
        self.assertEqual(result.left, 18)
        self.assertEqual(result.top, 14)

    def test_match_zero_system_entry_template(self) -> None:
        root_dir = Path(__file__).resolve().parents[1]
        matcher = TemplateMatcher()
        screenshot = Path(
            "/Users/michael/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/"
            "michael-lyr_3e43/temp/RWTemp/2026-06/52a1ab9b3472a7f71ab346a045b579f6/"
            "752cddee3f7ca6066d8409c03117e5a6.jpg"
        )
        result = matcher.find_in_image(
            screenshot_path=screenshot,
            template_path=root_dir / "resources" / "templates" / "zero_system_entry.png",
            search_region=SearchRegion(left=1020, top=760, width=620, height=260),
            threshold=25.0,
            step=2,
        )

        self.assertTrue(result.found, result.summary())
        self.assertLessEqual(result.score, 1.0)
        self.assertEqual(result.left, 1065)
        self.assertEqual(result.top, 812)

    def test_match_zero_system_page_header_template(self) -> None:
        root_dir = Path(__file__).resolve().parents[1]
        matcher = TemplateMatcher()
        screenshot = Path(
            "/Users/michael/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/"
            "michael-lyr_3e43/temp/RWTemp/2026-06/52a1ab9b3472a7f71ab346a045b579f6/"
            "2b944e74ac966397c53494f2b934f79c.jpg"
        )
        result = matcher.find_in_image(
            screenshot_path=screenshot,
            template_path=root_dir / "resources" / "templates" / "zero_system_page_header.png",
            search_region=SearchRegion(left=0, top=0, width=360, height=120),
            threshold=20.0,
            step=1,
        )

        self.assertTrue(result.found, result.summary())
        self.assertLessEqual(result.score, 1.0)
        self.assertEqual(result.left, 18)
        self.assertEqual(result.top, 14)

    def test_match_codex_button_template(self) -> None:
        root_dir = Path(__file__).resolve().parents[1]
        matcher = TemplateMatcher()
        screenshot = Path(
            "/Users/michael/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/"
            "michael-lyr_3e43/temp/RWTemp/2026-06/52a1ab9b3472a7f71ab346a045b579f6/"
            "2b944e74ac966397c53494f2b934f79c.jpg"
        )
        result = matcher.find_in_image(
            screenshot_path=screenshot,
            template_path=root_dir / "resources" / "templates" / "codex_button.png",
            search_region=SearchRegion(left=1200, top=380, width=700, height=360),
            threshold=30.0,
            step=2,
        )

        self.assertTrue(result.found, result.summary())
        self.assertLessEqual(result.score, 1.0)
        self.assertEqual(result.left, 1480)
        self.assertEqual(result.top, 455)

    def test_match_first_codex_entry_template(self) -> None:
        root_dir = Path(__file__).resolve().parents[1]
        matcher = TemplateMatcher()
        screenshot = Path(
            "/Users/michael/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/"
            "michael-lyr_3e43/temp/RWTemp/2026-06/52a1ab9b3472a7f71ab346a045b579f6/"
            "171c6dc640f3340cebb24ea74a9525ab.jpg"
        )
        result = matcher.find_in_image(
            screenshot_path=screenshot,
            template_path=root_dir / "resources" / "templates" / "first_codex_entry.png",
            search_region=SearchRegion(left=0, top=170, width=650, height=500),
            threshold=30.0,
            step=2,
        )

        self.assertTrue(result.found, result.summary())
        self.assertLessEqual(result.score, 1.0)
        self.assertEqual(result.left, 45)
        self.assertEqual(result.top, 235)

    def test_match_codex_enter_button_template(self) -> None:
        root_dir = Path(__file__).resolve().parents[1]
        matcher = TemplateMatcher()
        screenshot = Path(
            "/Users/michael/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/"
            "michael-lyr_3e43/temp/RWTemp/2026-06/52a1ab9b3472a7f71ab346a045b579f6/"
            "171c6dc640f3340cebb24ea74a9525ab.jpg"
        )
        result = matcher.find_in_image(
            screenshot_path=screenshot,
            template_path=root_dir / "resources" / "templates" / "codex_enter_button.png",
            search_region=SearchRegion(left=1450, top=880, width=460, height=190),
            threshold=25.0,
            step=2,
        )

        self.assertTrue(result.found, result.summary())
        self.assertLessEqual(result.score, 25.0)
        self.assertEqual(result.left, 1535)
        self.assertEqual(result.top, 925)

    def test_match_team_setup_page_header_template(self) -> None:
        root_dir = Path(__file__).resolve().parents[1]
        matcher = TemplateMatcher()
        screenshot = Path(
            "/Users/michael/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/"
            "michael-lyr_3e43/temp/RWTemp/2026-06/52a1ab9b3472a7f71ab346a045b579f6/"
            "4831467a0e74eeb750d4a53873a94868.jpg"
        )
        result = matcher.find_in_image(
            screenshot_path=screenshot,
            template_path=root_dir / "resources" / "templates" / "team_config_page_header.png",
            search_region=SearchRegion(left=0, top=0, width=380, height=140),
            threshold=20.0,
            step=1,
        )

        self.assertTrue(result.found, result.summary())
        self.assertLessEqual(result.score, 1.0)
        self.assertEqual(result.left, 18)
        self.assertEqual(result.top, 14)

    def test_match_team_setup_enter_button_template(self) -> None:
        root_dir = Path(__file__).resolve().parents[1]
        matcher = TemplateMatcher()
        screenshot = Path(
            "/Users/michael/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/"
            "michael-lyr_3e43/temp/RWTemp/2026-06/52a1ab9b3472a7f71ab346a045b579f6/"
            "4831467a0e74eeb750d4a53873a94868.jpg"
        )
        result = matcher.find_in_image(
            screenshot_path=screenshot,
            template_path=root_dir / "resources" / "templates" / "team_config_enter_button.png",
            search_region=SearchRegion(left=1450, top=880, width=460, height=190),
            threshold=25.0,
            step=2,
        )

        self.assertTrue(result.found, result.summary())
        self.assertLessEqual(result.score, 25.0)
        self.assertEqual(result.left, 1535)
        self.assertEqual(result.top, 925)
