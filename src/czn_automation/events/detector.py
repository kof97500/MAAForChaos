from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from PIL import Image, ImageStat


@dataclass
class Rect:
    left: int
    top: int
    width: int
    height: int

    @property
    def center_x(self) -> int:
        return self.left + self.width // 2

    @property
    def center_y(self) -> int:
        return self.top + self.height // 2


@dataclass
class EventOption:
    index: int
    rect: Rect
    crop_path: str = ""

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "rect": asdict(self.rect),
            "center": {
                "x": self.rect.center_x,
                "y": self.rect.center_y,
            },
            "crop_path": self.crop_path,
        }


@dataclass
class EventDetectionResult:
    is_event_page: bool
    option_count: int
    options: list[EventOption]
    event_button_rect: Rect
    screenshot_path: str
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "is_event_page": self.is_event_page,
            "option_count": self.option_count,
            "options": [item.to_dict() for item in self.options],
            "event_button_rect": asdict(self.event_button_rect),
            "event_button_center": {
                "x": self.event_button_rect.center_x,
                "y": self.event_button_rect.center_y,
            },
            "screenshot_path": self.screenshot_path,
            "reason": self.reason,
        }

    def summary(self) -> str:
        if not self.is_event_page:
            return self.reason or "未识别为事件页"
        return (
            f"event_page option_count={self.option_count} "
            f"button_center=({self.event_button_rect.center_x},{self.event_button_rect.center_y})"
        )


class EventDetector:
    def detect(self, screenshot_path: Path) -> EventDetectionResult:
        image = Image.open(screenshot_path).convert("L")
        options = self._detect_options(image)
        button_rect = self._estimate_event_button_rect(image.width, image.height)
        is_event_page = 2 <= len(options) <= 4
        reason = "" if is_event_page else f"未检测到 2-4 个事件选项框，当前仅检测到 {len(options)} 个"
        return EventDetectionResult(
            is_event_page=is_event_page,
            option_count=len(options),
            options=options,
            event_button_rect=button_rect,
            screenshot_path=str(screenshot_path),
            reason=reason,
        )

    def save_debug_artifacts(
        self,
        *,
        result: EventDetectionResult,
        root_dir: Path,
    ) -> Path:
        image = Image.open(result.screenshot_path)
        output_dir = root_dir / "debug" / "events"
        options_dir = output_dir / "options"
        output_dir.mkdir(parents=True, exist_ok=True)
        options_dir.mkdir(parents=True, exist_ok=True)

        for option in result.options:
            crop_path = options_dir / f"option_{option.index}.png"
            rect = option.rect
            image.crop(
                (rect.left, rect.top, rect.left + rect.width, rect.top + rect.height)
            ).save(crop_path)
            option.crop_path = str(crop_path)

        report_path = output_dir / "event_probe_result.json"
        report_path.write_text(
            json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return report_path

    def _detect_options(self, image: Image.Image) -> list[EventOption]:
        width, height = image.size
        roi_left = 0
        roi_top = int(height * 0.74)
        roi_right = width
        roi_bottom = int(height * 0.98)
        roi = image.crop((roi_left, roi_top, roi_right, roi_bottom))

        column_scores = []
        for x in range(roi.width):
            column = roi.crop((x, 0, x + 1, roi.height))
            darkness = 255.0 - ImageStat.Stat(column).mean[0]
            column_scores.append(darkness)

        smooth_scores = self._smooth(column_scores, radius=10)
        threshold = max(38.0, max(smooth_scores) * 0.58)
        runs = self._find_runs(smooth_scores, threshold=threshold, min_width=max(140, width // 12))
        merged_runs = self._merge_close_runs(runs, gap=max(18, width // 96))

        options: list[EventOption] = []
        for index, (run_left, run_right) in enumerate(merged_runs[:4], start=1):
            option_rect = self._build_option_rect(
                roi=roi,
                run_left=run_left,
                run_right=run_right,
                absolute_left=roi_left + run_left,
                absolute_right=roi_left + run_right,
                absolute_top=roi_top,
                screen_height=height,
                screen_width=width,
            )
            options.append(EventOption(index=index, rect=option_rect))

        return options

    def _build_option_rect(
        self,
        *,
        roi: Image.Image,
        run_left: int,
        run_right: int,
        absolute_left: int,
        absolute_right: int,
        absolute_top: int,
        screen_height: int,
        screen_width: int,
    ) -> Rect:
        option_slice = roi.crop((run_left, 0, run_right + 1, roi.height))
        row_scores = []
        for y in range(option_slice.height):
            row = option_slice.crop((0, y, option_slice.width, y + 1))
            darkness = 255.0 - ImageStat.Stat(row).mean[0]
            row_scores.append(darkness)

        smooth_rows = self._smooth(row_scores, radius=6)
        row_threshold = max(32.0, max(smooth_rows) * 0.55)
        row_runs = self._find_runs(smooth_rows, threshold=row_threshold, min_width=max(24, screen_height // 40))
        if row_runs:
            top_run, bottom_run = row_runs[0]
            top = absolute_top + max(0, top_run - 14)
            bottom = absolute_top + min(option_slice.height - 1, bottom_run + 18)
        else:
            top = int(screen_height * 0.78)
            bottom = int(screen_height * 0.97)

        left = max(0, absolute_left - 10)
        right = min(screen_width - 1, absolute_right + 10)
        return Rect(
            left=left,
            top=top,
            width=right - left + 1,
            height=bottom - top + 1,
        )

    def _estimate_event_button_rect(self, width: int, height: int) -> Rect:
        left = int(width * 0.0)
        top = int(height * 0.18)
        right = int(width * 0.28)
        bottom = int(height * 0.39)
        return Rect(left=left, top=top, width=right - left, height=bottom - top)

    def _smooth(self, values: list[float], radius: int) -> list[float]:
        output: list[float] = []
        for index in range(len(values)):
            start = max(0, index - radius)
            end = min(len(values), index + radius + 1)
            output.append(sum(values[start:end]) / (end - start))
        return output

    def _find_runs(self, values: list[float], *, threshold: float, min_width: int) -> list[tuple[int, int]]:
        runs: list[tuple[int, int]] = []
        start: int | None = None
        for index, value in enumerate(values):
            if value >= threshold and start is None:
                start = index
            elif value < threshold and start is not None:
                if index - start >= min_width:
                    runs.append((start, index - 1))
                start = None
        if start is not None and len(values) - start >= min_width:
            runs.append((start, len(values) - 1))
        return runs

    def _merge_close_runs(self, runs: list[tuple[int, int]], gap: int) -> list[tuple[int, int]]:
        if not runs:
            return []
        merged = [runs[0]]
        for current_left, current_right in runs[1:]:
            previous_left, previous_right = merged[-1]
            if current_left - previous_right <= gap:
                merged[-1] = (previous_left, current_right)
            else:
                merged.append((current_left, current_right))
        return merged
