import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from czn_automation.events.detector import EventDetector


class EventDetectorTestCase(unittest.TestCase):
    def test_detect_three_event_options(self) -> None:
        detector = EventDetector()
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "event.png"
            self._build_mock_event_page(image_path, option_count=3)
            result = detector.detect(image_path)

        self.assertTrue(result.is_event_page, result.summary())
        self.assertEqual(result.option_count, 3)
        self.assertEqual(len(result.options), 3)
        self.assertGreater(result.event_button_rect.width, 0)

    def test_single_option_layout_still_reports_one_option(self) -> None:
        detector = EventDetector()
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "non_event.png"
            self._build_mock_event_page(image_path, option_count=1)
            result = detector.detect(image_path)

        self.assertEqual(result.option_count, 1)

    def test_detect_three_options_with_dark_background_band(self) -> None:
        detector = EventDetector()
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "event_with_band.png"
            self._build_mock_event_page(image_path, option_count=3, dark_band=True)
            result = detector.detect(image_path)

        self.assertTrue(result.is_event_page, result.summary())
        self.assertEqual(result.option_count, 3)

    def _build_mock_event_page(self, output_path: Path, option_count: int, dark_band: bool = False) -> None:
        width, height = 1920, 1080
        image = Image.new("RGB", (width, height), color=(220, 220, 230))
        draw = ImageDraw.Draw(image)

        draw.rectangle((0, 0, width, 170), fill=(80, 70, 90))
        draw.rectangle((0, 190, 520, 360), fill=(25, 20, 30))
        draw.rectangle((0, 210, 120, 340), fill=(40, 20, 50))
        draw.rectangle((330, 220, 1600, 380), fill=(150, 150, 160))
        if dark_band:
            draw.rectangle((0, 810, width, 1070), fill=(70, 68, 80))

        if option_count == 1:
            box_width = 900
            total_gap = 0
        else:
            total_gap = 28 * (option_count - 1)
            box_width = (width - 70 - total_gap) // option_count
        left = 24
        for _ in range(option_count):
            draw.rounded_rectangle(
                (left, 840, left + box_width, 1060),
                radius=28,
                fill=(35, 31, 42) if not dark_band else (20, 18, 25),
            )
            left += box_width + 28

        image.save(output_path)
