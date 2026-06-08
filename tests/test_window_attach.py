import logging
import unittest
from pathlib import Path

from czn_automation.config import load_config
from czn_automation.runtime.context import RunContext
from czn_automation.runtime.progress import ProgressReporter
from czn_automation.window.attach import GameWindowService, WindowInfo


class GameWindowServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        root_dir = Path(__file__).resolve().parents[1]
        config = load_config(root_dir / "config" / "app.example.json")
        logger = logging.getLogger(f"test_logger_{id(self)}")
        logger.handlers.clear()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.NullHandler())
        self.context = RunContext(
            root_dir=root_dir,
            logger=logger,
            progress=ProgressReporter(),
            config=config,
        )
        self.service = GameWindowService(self.context)

    def test_match_window_prefers_supported_resolution(self) -> None:
        windows = [
            WindowInfo(
                hwnd=1001,
                title="Chaos Zero Nightmare - Windowed",
                left=0,
                top=0,
                width=1600,
                height=900,
                visible=True,
                minimized=False,
            ),
            WindowInfo(
                hwnd=1002,
                title="Chaos Zero Nightmare",
                left=10,
                top=20,
                width=1920,
                height=1080,
                visible=True,
                minimized=False,
            ),
        ]

        matched = self.service._match_window(windows)

        self.assertIsNotNone(matched)
        self.assertEqual(matched.hwnd, 1002)

    def test_match_window_returns_title_match_when_resolution_is_wrong(self) -> None:
        windows = [
            WindowInfo(
                hwnd=1003,
                title="卡厄思梦境",
                left=5,
                top=5,
                width=1600,
                height=900,
                visible=True,
                minimized=False,
            )
        ]

        matched = self.service._match_window(windows)

        self.assertIsNotNone(matched)
        self.assertEqual(matched.hwnd, 1003)
        self.assertFalse(self.service._is_supported_resolution(matched.width, matched.height))
