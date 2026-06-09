from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

from czn_automation.config import SearchRegion


@dataclass
class TemplateMatchResult:
    found: bool
    left: int = 0
    top: int = 0
    width: int = 0
    height: int = 0
    score: float = 9999.0
    reason: str = ""

    @property
    def center_x(self) -> int:
        return self.left + self.width // 2

    @property
    def center_y(self) -> int:
        return self.top + self.height // 2

    def summary(self) -> str:
        if self.found:
            return (
                f"rect=({self.left},{self.top},{self.width},{self.height}) "
                f"center=({self.center_x},{self.center_y}) score={self.score:.2f}"
            )
        return self.reason or "unknown"


class TemplateMatcher:
    def __init__(self, foreground_threshold: int = 72) -> None:
        self.foreground_threshold = foreground_threshold

    def find_in_image(
        self,
        screenshot_path: Path,
        template_path: Path,
        search_region: SearchRegion,
        threshold: float,
        step: int,
    ) -> TemplateMatchResult:
        screenshot = Image.open(screenshot_path).convert("L")
        template = Image.open(template_path).convert("L")
        template_mask = self._build_template_mask(template)

        region = screenshot.crop(
            (
                search_region.left,
                search_region.top,
                search_region.left + search_region.width,
                search_region.top + search_region.height,
            )
        )

        if template.width > region.width or template.height > region.height:
            return TemplateMatchResult(
                found=False,
                reason="模板尺寸大于搜索区域，无法执行匹配",
            )

        best = self._scan_region(
            region,
            template,
            template_mask,
            search_region.left,
            search_region.top,
            step,
        )
        if best is None:
            return TemplateMatchResult(found=False, reason="未得到任何匹配结果")

        refined = self._refine_best_match(
            region,
            template,
            template_mask,
            search_region.left,
            search_region.top,
            best,
        )
        if refined.score > threshold:
            refined.found = False
            refined.reason = f"匹配分数超过阈值: score={refined.score:.2f} threshold={threshold:.2f}"
        return refined

    def _scan_region(
        self,
        region: Image.Image,
        template: Image.Image,
        template_mask: Image.Image,
        offset_left: int,
        offset_top: int,
        step: int,
    ) -> TemplateMatchResult | None:
        max_x = region.width - template.width
        max_y = region.height - template.height
        best_score = None
        best_left = 0
        best_top = 0

        for top in range(0, max_y + 1, max(step, 1)):
            for left in range(0, max_x + 1, max(step, 1)):
                score = self._score(
                    region.crop((left, top, left + template.width, top + template.height)),
                    template,
                    template_mask,
                )
                if best_score is None or score < best_score:
                    best_score = score
                    best_left = left
                    best_top = top

        if best_score is None:
            return None

        return TemplateMatchResult(
            found=True,
            left=offset_left + best_left,
            top=offset_top + best_top,
            width=template.width,
            height=template.height,
            score=best_score,
        )

    def _refine_best_match(
        self,
        region: Image.Image,
        template: Image.Image,
        template_mask: Image.Image,
        offset_left: int,
        offset_top: int,
        coarse: TemplateMatchResult,
    ) -> TemplateMatchResult:
        local_left = coarse.left - offset_left
        local_top = coarse.top - offset_top
        best = coarse

        start_left = max(local_left - 2, 0)
        start_top = max(local_top - 2, 0)
        end_left = min(local_left + 2, region.width - template.width)
        end_top = min(local_top + 2, region.height - template.height)

        for top in range(start_top, end_top + 1):
            for left in range(start_left, end_left + 1):
                score = self._score(
                    region.crop((left, top, left + template.width, top + template.height)),
                    template,
                    template_mask,
                )
                if score < best.score:
                    best = TemplateMatchResult(
                        found=True,
                        left=offset_left + left,
                        top=offset_top + top,
                        width=template.width,
                        height=template.height,
                        score=score,
                    )
        return best

    def _score(self, image_a: Image.Image, image_b: Image.Image, mask: Image.Image) -> float:
        diff = ImageChops.difference(image_a, image_b)
        if mask.getbbox() is None:
            return float(ImageStat.Stat(diff).mean[0])
        return float(ImageStat.Stat(diff, mask=mask).mean[0])

    def _build_template_mask(self, template: Image.Image) -> Image.Image:
        return template.point(
            lambda pixel: 255 if pixel >= self.foreground_threshold else 0,
            mode="L",
        )
