from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import shutil
from pathlib import Path

from PIL import Image, ImageOps, ImageStat

try:
    import pytesseract
except ImportError:  # pragma: no cover - optional dependency fallback
    pytesseract = None


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
    title: str = ""
    description: str = ""
    crop_path: str = ""
    title_crop_path: str = ""
    description_crop_path: str = ""

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "rect": asdict(self.rect),
            "center": {
                "x": self.rect.center_x,
                "y": self.rect.center_y,
            },
            "title": self.title,
            "description": self.description,
            "crop_path": self.crop_path,
            "title_crop_path": self.title_crop_path,
            "description_crop_path": self.description_crop_path,
        }


@dataclass
class EventDetectionResult:
    is_event_page: bool
    option_count: int
    options: list[EventOption]
    event_button_rect: Rect
    detail_opened: bool
    event_name: str
    event_subtitle: str
    name_panel_rect: Rect
    screenshot_path: str
    ocr_available: bool
    reason: str = ""
    name_panel_path: str = ""
    event_name_crop_path: str = ""
    event_subtitle_crop_path: str = ""

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
            "detail_opened": self.detail_opened,
            "event_name": self.event_name,
            "event_subtitle": self.event_subtitle,
            "name_panel_rect": asdict(self.name_panel_rect),
            "name_panel_path": self.name_panel_path,
            "event_name_crop_path": self.event_name_crop_path,
            "event_subtitle_crop_path": self.event_subtitle_crop_path,
            "screenshot_path": self.screenshot_path,
            "ocr_available": self.ocr_available,
            "reason": self.reason,
        }

    def summary(self) -> str:
        if not self.is_event_page:
            return self.reason or "未识别为事件页"
        return (
            f"event_page option_count={self.option_count} "
            f"button_center=({self.event_button_rect.center_x},{self.event_button_rect.center_y}) "
            f"event_name={self.event_name or '-'}"
        )


class EventDetector:
    def __init__(self) -> None:
        self.tesseract_path = shutil.which("tesseract") or ""
        if self.tesseract_path and pytesseract is not None:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path

    def detect(self, screenshot_path: Path) -> EventDetectionResult:
        with Image.open(screenshot_path) as source_image:
            grayscale = source_image.convert("L")
            options = self._detect_options(grayscale)
            button_rect = self._estimate_event_button_rect(grayscale.width, grayscale.height)
            name_panel_rect = self._estimate_name_panel_rect(grayscale.width, grayscale.height)
            detail_opened = self._is_detail_panel_open(grayscale, name_panel_rect)

            event_name = ""
            event_subtitle = ""
            if detail_opened and self.ocr_available:
                event_name_rect = self._estimate_event_name_rect(grayscale.width, grayscale.height)
                event_subtitle_rect = self._estimate_event_subtitle_rect(grayscale.width, grayscale.height)
                event_name = self._ocr_rect(source_image, event_name_rect, psm=7)
                event_subtitle = self._ocr_rect(source_image, event_subtitle_rect, psm=7)

            for option in options:
                title_rect, desc_rect = self._split_option_rect(option.rect)
                if self.ocr_available:
                    option.title = self._ocr_rect(source_image, title_rect, psm=7)
                    option.description = self._ocr_rect(source_image, desc_rect, psm=6)

        is_event_page = detail_opened
        if is_event_page:
            reason = "" if event_name or not self.ocr_available else "详情已展开，但未识别到事件名称"
        else:
            reason = "点击后未检测到事件详情面板，当前可能不是事件页"

        return EventDetectionResult(
            is_event_page=is_event_page,
            option_count=len(options),
            options=options,
            event_button_rect=button_rect,
            detail_opened=detail_opened,
            event_name=event_name,
            event_subtitle=event_subtitle,
            name_panel_rect=name_panel_rect,
            screenshot_path=str(screenshot_path),
            ocr_available=self.ocr_available,
            reason=reason,
        )

    @property
    def ocr_available(self) -> bool:
        return bool(self.tesseract_path) and pytesseract is not None

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

        name_panel_path = output_dir / "event_name_panel.png"
        image.crop(self._rect_box(result.name_panel_rect)).save(name_panel_path)
        result.name_panel_path = str(name_panel_path)

        event_name_rect = self._estimate_event_name_rect(image.width, image.height)
        event_name_crop_path = output_dir / "event_name.png"
        image.crop(self._rect_box(event_name_rect)).save(event_name_crop_path)
        result.event_name_crop_path = str(event_name_crop_path)

        event_subtitle_rect = self._estimate_event_subtitle_rect(image.width, image.height)
        event_subtitle_crop_path = output_dir / "event_subtitle.png"
        image.crop(self._rect_box(event_subtitle_rect)).save(event_subtitle_crop_path)
        result.event_subtitle_crop_path = str(event_subtitle_crop_path)

        for option in result.options:
            crop_path = options_dir / f"option_{option.index}.png"
            image.crop(self._rect_box(option.rect)).save(crop_path)
            option.crop_path = str(crop_path)

            title_rect, desc_rect = self._split_option_rect(option.rect)
            title_crop_path = options_dir / f"option_{option.index}_title.png"
            desc_crop_path = options_dir / f"option_{option.index}_description.png"
            image.crop(self._rect_box(title_rect)).save(title_crop_path)
            image.crop(self._rect_box(desc_rect)).save(desc_crop_path)
            option.title_crop_path = str(title_crop_path)
            option.description_crop_path = str(desc_crop_path)

        report_path = output_dir / "event_probe_result.json"
        report_path.write_text(
            json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return report_path

    def _detect_options(self, image: Image.Image) -> list[EventOption]:
        layout_options = self._detect_options_by_layout(image)
        if layout_options:
            return layout_options

        return self._detect_options_by_projection(image)

    def _detect_options_by_layout(self, image: Image.Image) -> list[EventOption]:
        width, height = image.size
        best_score = 0.0
        best_options: list[EventOption] = []

        for option_count in (4, 3, 2):
            options = self._build_layout_options(width, height, option_count)
            if not options:
                continue

            slot_scores = []
            box_darkness_values = []
            for option in options:
                rect = option.rect
                darkness = self._region_darkness(
                    image,
                    rect.left + max(12, rect.width // 20),
                    rect.top + max(16, rect.height // 12),
                    rect.left + rect.width - max(12, rect.width // 20),
                    rect.top + rect.height - max(18, rect.height // 10),
                )
                above_darkness = self._region_darkness(
                    image,
                    rect.left + max(12, rect.width // 20),
                    max(0, rect.top - max(50, rect.height // 3)),
                    rect.left + rect.width - max(12, rect.width // 20),
                    max(1, rect.top - max(10, rect.height // 10)),
                )
                box_darkness_values.append(darkness)
                slot_scores.append(darkness - above_darkness)

            average_score = sum(slot_scores) / len(slot_scores)
            min_box_darkness = min(box_darkness_values)
            second_darkest = sorted(box_darkness_values)[1] if len(box_darkness_values) >= 2 else min_box_darkness
            if (
                min_box_darkness >= 120.0
                and second_darkest >= 120.0
                and average_score >= 8.0
                and average_score > best_score
            ):
                best_score = average_score
                best_options = options

        return best_options

    def _build_layout_options(self, width: int, height: int, option_count: int) -> list[EventOption]:
        margin = max(24, int(width * 0.0125))
        gap = max(22, int(width * 0.0145))
        available = width - (margin * 2) - gap * (option_count - 1)
        if available <= 0:
            return []

        box_width = available // option_count
        box_height = int(height * 0.208)
        top = int(height * 0.778)
        options: list[EventOption] = []
        left = margin
        for index in range(1, option_count + 1):
            options.append(
                EventOption(
                    index=index,
                    rect=Rect(
                        left=left,
                        top=top,
                        width=box_width,
                        height=box_height,
                    ),
                )
            )
            left += box_width + gap
        return options

    def _detect_options_by_projection(self, image: Image.Image) -> list[EventOption]:
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
            option_rect = self._build_projection_option_rect(
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

    def _build_projection_option_rect(
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
        top = int(height * 0.205)
        right = int(width * 0.11)
        bottom = int(height * 0.365)
        return Rect(left=left, top=top, width=right - left, height=bottom - top)

    def _estimate_name_panel_rect(self, width: int, height: int) -> Rect:
        left = int(width * 0.0)
        top = int(height * 0.165)
        right = int(width * 0.28)
        bottom = int(height * 0.325)
        return Rect(left=left, top=top, width=right - left, height=bottom - top)

    def _estimate_event_name_rect(self, width: int, height: int) -> Rect:
        left = int(width * 0.047)
        top = int(height * 0.185)
        right = int(width * 0.255)
        bottom = int(height * 0.238)
        return Rect(left=left, top=top, width=right - left, height=bottom - top)

    def _estimate_event_subtitle_rect(self, width: int, height: int) -> Rect:
        left = int(width * 0.047)
        top = int(height * 0.238)
        right = int(width * 0.173)
        bottom = int(height * 0.286)
        return Rect(left=left, top=top, width=right - left, height=bottom - top)

    def _split_option_rect(self, rect: Rect) -> tuple[Rect, Rect]:
        title_height = max(56, int(rect.height * 0.28))
        title_rect = Rect(
            left=rect.left + max(18, rect.width // 28),
            top=rect.top + max(14, rect.height // 20),
            width=rect.width - max(36, rect.width // 14),
            height=title_height,
        )
        description_rect = Rect(
            left=rect.left + max(18, rect.width // 28),
            top=title_rect.top + title_rect.height - max(4, rect.height // 40),
            width=rect.width - max(36, rect.width // 14),
            height=rect.height - title_height - max(26, rect.height // 10),
        )
        return title_rect, description_rect

    def _is_detail_panel_open(self, image: Image.Image, panel_rect: Rect) -> bool:
        region_darkness = self._region_darkness(
            image,
            panel_rect.left + max(12, panel_rect.width // 20),
            panel_rect.top + max(12, panel_rect.height // 10),
            panel_rect.left + panel_rect.width - max(12, panel_rect.width // 20),
            panel_rect.top + panel_rect.height - max(12, panel_rect.height // 10),
        )
        return region_darkness >= 120.0

    def _ocr_rect(self, image: Image.Image, rect: Rect, *, psm: int) -> str:
        if not self.ocr_available:
            return ""

        crop = image.crop(self._rect_box(rect)).convert("L")
        crop = ImageOps.autocontrast(crop)
        crop = crop.resize((crop.width * 2, crop.height * 2))
        crop = crop.point(lambda pixel: 255 if pixel > 150 else 0)

        for language in ("chi_sim+eng", "chi_sim", "eng"):
            try:
                text = pytesseract.image_to_string(
                    crop,
                    lang=language,
                    config=f"--psm {psm}",
                )
            except Exception:
                continue
            normalized = self._normalize_ocr_text(text)
            if normalized:
                return normalized
        return ""

    def _normalize_ocr_text(self, text: str) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    def _region_darkness(
        self,
        image: Image.Image,
        left: int,
        top: int,
        right: int,
        bottom: int,
    ) -> float:
        left = max(0, min(image.width - 1, left))
        top = max(0, min(image.height - 1, top))
        right = max(left + 1, min(image.width, right))
        bottom = max(top + 1, min(image.height, bottom))
        region = image.crop((left, top, right, bottom))
        return 255.0 - ImageStat.Stat(region).mean[0]

    def _rect_box(self, rect: Rect) -> tuple[int, int, int, int]:
        return (rect.left, rect.top, rect.left + rect.width, rect.top + rect.height)

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
