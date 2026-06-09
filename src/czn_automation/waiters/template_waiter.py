from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time

from czn_automation.config import SearchRegion
from czn_automation.recognition.template_match import TemplateMatchResult, TemplateMatcher
from czn_automation.runtime.context import RunContext
from czn_automation.window.attach import WindowInfo
from czn_automation.window.screenshot import CaptureResult, WindowScreenshotService


@dataclass
class TemplateWaitResult:
    found: bool
    match: TemplateMatchResult
    capture: CaptureResult | None = None

    def summary(self) -> str:
        return self.match.summary()


class TemplateWaiter:
    def __init__(
        self,
        context: RunContext,
        screenshot_service: WindowScreenshotService,
        matcher: TemplateMatcher,
    ) -> None:
        self.context = context
        self.screenshot_service = screenshot_service
        self.matcher = matcher

    def wait_for_template(
        self,
        window: WindowInfo,
        *,
        template_path: Path,
        search_region: SearchRegion,
        threshold: float,
        step: int,
        timeout_ms: int,
        poll_interval_ms: int,
        screenshot_prefix: str,
        log_prefix: str,
    ) -> TemplateWaitResult:
        deadline = time.time() + (timeout_ms / 1000)
        attempt = 0
        last_match = TemplateMatchResult(found=False, reason="尚未开始轮询")
        last_capture: CaptureResult | None = None

        while time.time() < deadline:
            attempt += 1
            filename = f"{screenshot_prefix}_{attempt:02d}.bmp"
            capture = self.screenshot_service.capture_named_debug_file(window, filename)
            last_capture = capture
            if not capture.success or capture.path is None:
                last_match = TemplateMatchResult(found=False, reason=capture.summary())
                time.sleep(poll_interval_ms / 1000)
                continue

            match = self.matcher.find_in_image(
                screenshot_path=capture.path,
                template_path=template_path,
                search_region=search_region,
                threshold=threshold,
                step=step,
            )
            self.context.logger.info("%s轮询 #%s: %s", log_prefix, attempt, match.summary())
            if match.found:
                return TemplateWaitResult(found=True, match=match, capture=capture)

            last_match = match
            time.sleep(poll_interval_ms / 1000)

        return TemplateWaitResult(
            found=False,
            match=TemplateMatchResult(
                found=False,
                reason=f"等待模板超时，最后结果：{last_match.summary()}",
            ),
            capture=last_capture,
        )

    def wait_for_template_to_disappear(
        self,
        window: WindowInfo,
        *,
        template_path: Path,
        search_region: SearchRegion,
        threshold: float,
        step: int,
        timeout_ms: int,
        poll_interval_ms: int,
        screenshot_prefix: str,
        log_prefix: str,
    ) -> TemplateWaitResult:
        deadline = time.time() + (timeout_ms / 1000)
        attempt = 0
        last_match = TemplateMatchResult(found=True, reason="尚未开始轮询")
        last_capture: CaptureResult | None = None

        while time.time() < deadline:
            attempt += 1
            filename = f"{screenshot_prefix}_{attempt:02d}.bmp"
            capture = self.screenshot_service.capture_named_debug_file(window, filename)
            last_capture = capture
            if not capture.success or capture.path is None:
                last_match = TemplateMatchResult(found=True, reason=capture.summary())
                time.sleep(poll_interval_ms / 1000)
                continue

            match = self.matcher.find_in_image(
                screenshot_path=capture.path,
                template_path=template_path,
                search_region=search_region,
                threshold=threshold,
                step=step,
            )
            self.context.logger.info("%s轮询 #%s: %s", log_prefix, attempt, match.summary())
            if not match.found:
                return TemplateWaitResult(
                    found=True,
                    match=TemplateMatchResult(found=True, reason="目标模板已消失"),
                    capture=capture,
                )

            last_match = match
            time.sleep(poll_interval_ms / 1000)

        return TemplateWaitResult(
            found=False,
            match=TemplateMatchResult(
                found=False,
                reason=f"等待模板消失超时，最后结果：{last_match.summary()}",
            ),
            capture=last_capture,
        )
