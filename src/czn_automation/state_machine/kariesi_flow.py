from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
import time

from czn_automation.recognition.template_match import TemplateMatchResult, TemplateMatcher
from czn_automation.runtime.context import RunContext
from czn_automation.window.attach import AttachResult, GameWindowService, WindowInfo
from czn_automation.window.input import ClickResult, WindowInputService
from czn_automation.window.screenshot import CaptureResult, WindowScreenshotService


class KariesiState(Enum):
    ATTACH_WINDOW = auto()
    CAPTURE_INITIAL_SCREENSHOT = auto()
    DETECT_KARIESI_BUTTON = auto()
    CLICK_KARIESI_BUTTON = auto()
    WAIT_FOR_KARIESI_PAGE = auto()
    DETECT_ZERO_SYSTEM_ENTRY = auto()
    CLICK_ZERO_SYSTEM_ENTRY = auto()
    WAIT_FOR_ZERO_SYSTEM_PAGE = auto()
    SUCCESS = auto()
    FAILED = auto()


@dataclass
class KariesiFlowResult:
    success: bool
    final_state: KariesiState
    reason: str = ""


class KariesiEntryStateMachine:
    def __init__(self, context: RunContext) -> None:
        self.context = context
        self.window_service = GameWindowService(context)
        self.screenshot_service = WindowScreenshotService(context)
        self.input_service = WindowInputService(context)
        self.matcher = TemplateMatcher()

        self.current_state = KariesiState.ATTACH_WINDOW
        self.failure_reason = ""

        self.attach_result: AttachResult | None = None
        self.window: WindowInfo | None = None
        self.before_capture: CaptureResult | None = None
        self.button_match: TemplateMatchResult | None = None
        self.click_result: ClickResult | None = None
        self.kariesi_page_capture: CaptureResult | None = None
        self.zero_system_capture: CaptureResult | None = None
        self.zero_system_match: TemplateMatchResult | None = None

    def run(self) -> KariesiFlowResult:
        while self.current_state not in (KariesiState.SUCCESS, KariesiState.FAILED):
            self.context.logger.info("状态机进入状态：%s", self.current_state.name)
            self.current_state = self._handle_state(self.current_state)

        return KariesiFlowResult(
            success=self.current_state == KariesiState.SUCCESS,
            final_state=self.current_state,
            reason=self.failure_reason,
        )

    def _handle_state(self, state: KariesiState) -> KariesiState:
        handlers = {
            KariesiState.ATTACH_WINDOW: self._attach_window,
            KariesiState.CAPTURE_INITIAL_SCREENSHOT: self._capture_initial_screenshot,
            KariesiState.DETECT_KARIESI_BUTTON: self._detect_kariesi_button,
            KariesiState.CLICK_KARIESI_BUTTON: self._click_kariesi_button,
            KariesiState.WAIT_FOR_KARIESI_PAGE: self._wait_for_kariesi_page,
            KariesiState.DETECT_ZERO_SYSTEM_ENTRY: self._detect_zero_system_entry,
            KariesiState.CLICK_ZERO_SYSTEM_ENTRY: self._click_zero_system_entry,
            KariesiState.WAIT_FOR_ZERO_SYSTEM_PAGE: self._wait_for_zero_system_page,
        }
        handler = handlers.get(state)
        if handler is None:
            self.failure_reason = f"未实现的状态处理器：{state.name}"
            return KariesiState.FAILED
        return handler()

    def _attach_window(self) -> KariesiState:
        attach_result = self.window_service.attach()
        self.attach_result = attach_result
        if not attach_result.found or attach_result.window is None:
            self.context.progress.update(
                stage="窗口连接",
                step="连接目标窗口",
                status="失败",
                detail=attach_result.summary(),
            )
            self.context.logger.warning("窗口连接流程结束，但未找到目标窗口：%s", attach_result.summary())
            self.failure_reason = attach_result.summary()
            return KariesiState.FAILED

        self.window = attach_result.window
        self.context.progress.update(
            stage="窗口连接",
            step="连接目标窗口",
            status="成功",
            detail=attach_result.summary(),
        )
        self.context.logger.info("窗口连接流程完成：%s", attach_result.summary())
        return KariesiState.CAPTURE_INITIAL_SCREENSHOT

    def _capture_initial_screenshot(self) -> KariesiState:
        if self.window is None:
            self.failure_reason = "窗口未初始化，无法截图"
            return KariesiState.FAILED

        self.context.progress.update(
            stage="截图验证",
            step="保存首张窗口截图",
            status="进行中",
            detail="窗口已连接，开始抓取客户区截图",
        )
        capture_result = self.screenshot_service.capture_to_debug_file(self.window)
        if not capture_result.success:
            self.context.progress.update(
                stage="截图验证",
                step="保存首张窗口截图",
                status="失败",
                detail=capture_result.summary(),
            )
            self.context.logger.warning("截图验证失败：%s", capture_result.summary())
            self.failure_reason = capture_result.summary()
            return KariesiState.FAILED

        self.context.progress.update(
            stage="截图验证",
            step="保存首张窗口截图",
            status="成功",
            detail=capture_result.summary(),
        )
        self.context.logger.info("截图验证完成：%s", capture_result.summary())
        self.before_capture = self.screenshot_service.capture_named_debug_file(
            self.window,
            "before_input_click.bmp",
        )
        if not self.before_capture.success:
            self.context.progress.update(
                stage="按钮识别",
                step="保存点击前截图",
                status="失败",
                detail=self.before_capture.summary(),
            )
            self.context.logger.warning("保存点击前截图失败：%s", self.before_capture.summary())
            self.failure_reason = self.before_capture.summary()
            return KariesiState.FAILED

        return KariesiState.DETECT_KARIESI_BUTTON

    def _detect_kariesi_button(self) -> KariesiState:
        if self.before_capture is None or self.before_capture.path is None:
            self.failure_reason = "点击前截图不可用，无法识别按钮"
            return KariesiState.FAILED

        template_path = self.context.root_dir / self.context.config.input_validation.template_path
        self.context.progress.update(
            stage="按钮识别",
            step="识别卡厄思图标按钮",
            status="进行中",
            detail=f"template={self.context.config.input_validation.template_path}",
        )
        match = self.matcher.find_in_image(
            screenshot_path=self.before_capture.path,
            template_path=template_path,
            search_region=self.context.config.input_validation.search_region,
            threshold=self.context.config.input_validation.match_threshold,
            step=self.context.config.input_validation.search_step,
        )
        self.button_match = match
        if not match.found:
            self.context.progress.update(
                stage="按钮识别",
                step="识别卡厄思图标按钮",
                status="失败",
                detail=match.summary(),
            )
            self.context.logger.warning("按钮识别失败：%s", match.summary())
            self.failure_reason = match.summary()
            return KariesiState.FAILED

        self.context.progress.update(
            stage="按钮识别",
            step="识别卡厄思图标按钮",
            status="成功",
            detail=match.summary(),
        )
        self.context.logger.info("按钮识别成功：%s", match.summary())
        return KariesiState.CLICK_KARIESI_BUTTON

    def _click_kariesi_button(self) -> KariesiState:
        if self.window is None or self.button_match is None:
            self.failure_reason = "窗口或按钮识别结果缺失，无法执行点击"
            return KariesiState.FAILED

        self.context.progress.update(
            stage="输入验证",
            step="点击卡厄思图标按钮",
            status="进行中",
            detail=(
                f"client=({self.button_match.center_x},{self.button_match.center_y}) "
                f"score={self.button_match.score:.2f}"
            ),
        )
        click_result = self.input_service.click_client_point(
            self.window,
            self.button_match.center_x,
            self.button_match.center_y,
        )
        self.click_result = click_result
        if not click_result.success:
            self.context.progress.update(
                stage="输入验证",
                step="点击卡厄思图标按钮",
                status="失败",
                detail=click_result.summary(),
            )
            self.context.logger.warning("输入验证失败：%s", click_result.summary())
            self.failure_reason = click_result.summary()
            return KariesiState.FAILED

        self.context.logger.info("输入验证点击完成：%s", click_result.summary())
        time.sleep(self.context.config.input_validation.post_click_wait_ms / 1000)
        return KariesiState.WAIT_FOR_KARIESI_PAGE

    def _wait_for_kariesi_page(self) -> KariesiState:
        if self.window is None:
            self.failure_reason = "窗口缺失，无法验证结果页面"
            return KariesiState.FAILED

        result = self._wait_for_success_page(self.window)
        if result.found:
            self.kariesi_page_capture = self.screenshot_service.capture_named_debug_file(
                self.window,
                "kariesi_page_ready.bmp",
            )
            self.context.progress.update(
                stage="结果验证",
                step="等待卡厄思页面稳定出现",
                status="成功",
                detail=result.summary(),
            )
            self.context.logger.info("结果验证成功：%s", result.summary())
            return KariesiState.DETECT_ZERO_SYSTEM_ENTRY

        self.context.progress.update(
            stage="结果验证",
            step="等待卡厄思页面稳定出现",
            status="失败",
            detail=result.summary(),
        )
        self.context.logger.warning("结果验证失败：%s", result.summary())
        self.failure_reason = result.summary()
        return KariesiState.FAILED

    def _detect_zero_system_entry(self) -> KariesiState:
        if self.window is None:
            self.failure_reason = "窗口缺失，无法识别零式系统入口"
            return KariesiState.FAILED

        self.zero_system_capture = self.screenshot_service.capture_named_debug_file(
            self.window,
            "before_zero_system_click.bmp",
        )
        if not self.zero_system_capture.success or self.zero_system_capture.path is None:
            self.failure_reason = self.zero_system_capture.summary()
            self.context.progress.update(
                stage="按钮识别",
                step="识别零式系统入口",
                status="失败",
                detail=self.failure_reason,
            )
            return KariesiState.FAILED

        config = self.context.config.zero_system
        template_path = self.context.root_dir / config.template_path
        self.context.progress.update(
            stage="按钮识别",
            step="识别零式系统入口",
            status="进行中",
            detail=f"template={config.template_path}",
        )
        match = self.matcher.find_in_image(
            screenshot_path=self.zero_system_capture.path,
            template_path=template_path,
            search_region=config.search_region,
            threshold=config.match_threshold,
            step=config.search_step,
        )
        self.zero_system_match = match
        if not match.found:
            self.failure_reason = match.summary()
            self.context.progress.update(
                stage="按钮识别",
                step="识别零式系统入口",
                status="失败",
                detail=match.summary(),
            )
            self.context.logger.warning("零式系统入口识别失败：%s", match.summary())
            return KariesiState.FAILED

        self.context.progress.update(
            stage="按钮识别",
            step="识别零式系统入口",
            status="成功",
            detail=match.summary(),
        )
        self.context.logger.info("零式系统入口识别成功：%s", match.summary())
        return KariesiState.CLICK_ZERO_SYSTEM_ENTRY

    def _click_zero_system_entry(self) -> KariesiState:
        if self.window is None or self.zero_system_match is None:
            self.failure_reason = "窗口或零式系统入口识别结果缺失"
            return KariesiState.FAILED

        self.context.progress.update(
            stage="输入验证",
            step="点击零式系统入口",
            status="进行中",
            detail=(
                f"client=({self.zero_system_match.center_x},{self.zero_system_match.center_y}) "
                f"score={self.zero_system_match.score:.2f}"
            ),
        )
        click_result = self.input_service.click_client_point(
            self.window,
            self.zero_system_match.center_x,
            self.zero_system_match.center_y,
        )
        if not click_result.success:
            self.failure_reason = click_result.summary()
            self.context.progress.update(
                stage="输入验证",
                step="点击零式系统入口",
                status="失败",
                detail=click_result.summary(),
            )
            self.context.logger.warning("零式系统入口点击失败：%s", click_result.summary())
            return KariesiState.FAILED

        self.context.logger.info("零式系统入口点击完成：%s", click_result.summary())
        time.sleep(self.context.config.zero_system.post_click_wait_ms / 1000)
        return KariesiState.WAIT_FOR_ZERO_SYSTEM_PAGE

    def _wait_for_zero_system_page(self) -> KariesiState:
        if self.window is None or self.zero_system_capture is None or self.zero_system_capture.path is None:
            self.failure_reason = "缺少零式系统点击前基准截图"
            return KariesiState.FAILED

        result = self._wait_for_zero_system_page_success(self.window)
        if result.found:
            self.context.progress.update(
                stage="结果验证",
                step="等待零式系统页面稳定出现",
                status="成功",
                detail=result.summary(),
            )
            self.context.logger.info("零式系统页面验证成功：%s", result.summary())
            return KariesiState.SUCCESS

        self.failure_reason = result.summary()
        self.context.progress.update(
            stage="结果验证",
            step="等待零式系统页面稳定出现",
            status="失败",
            detail=result.summary(),
        )
        self.context.logger.warning("零式系统页面验证失败：%s", result.summary())
        return KariesiState.FAILED

    def _wait_for_success_page(self, window: WindowInfo) -> TemplateMatchResult:
        config = self.context.config.input_validation
        deadline = time.time() + (config.success_timeout_ms / 1000)
        attempt = 0
        template_path = self.context.root_dir / config.success_template_path
        last_result = TemplateMatchResult(found=False, reason="尚未开始轮询")

        self.context.progress.update(
            stage="结果验证",
            step="等待卡厄思页面稳定出现",
            status="进行中",
            detail=f"timeout={config.success_timeout_ms}ms interval={config.success_poll_interval_ms}ms",
        )

        while time.time() < deadline:
            attempt += 1
            filename = f"after_input_click_{attempt:02d}.bmp"
            capture = self.screenshot_service.capture_named_debug_file(window, filename)
            if not capture.success or capture.path is None:
                last_result = TemplateMatchResult(found=False, reason=capture.summary())
                time.sleep(config.success_poll_interval_ms / 1000)
                continue

            result = self.matcher.find_in_image(
                screenshot_path=capture.path,
                template_path=template_path,
                search_region=config.success_search_region,
                threshold=config.success_match_threshold,
                step=1,
            )
            self.context.logger.info("结果验证轮询 #%s: %s", attempt, result.summary())
            if result.found:
                return result

            last_result = result
            time.sleep(config.success_poll_interval_ms / 1000)

        return TemplateMatchResult(
            found=False,
            reason=f"等待目标页面超时，最后结果：{last_result.summary()}",
        )

    def _wait_for_zero_system_page_success(self, window: WindowInfo) -> TemplateMatchResult:
        config = self.context.config.zero_system
        deadline = time.time() + (config.success_timeout_ms / 1000)
        attempt = 0
        template_path = self.context.root_dir / config.success_template_path
        last_result = TemplateMatchResult(found=False, reason="尚未开始轮询")

        self.context.progress.update(
            stage="结果验证",
            step="等待零式系统页面稳定出现",
            status="进行中",
            detail=(
                f"timeout={config.success_timeout_ms}ms "
                f"interval={config.success_poll_interval_ms}ms"
            ),
        )

        while time.time() < deadline:
            attempt += 1
            filename = f"after_zero_system_click_{attempt:02d}.bmp"
            capture = self.screenshot_service.capture_named_debug_file(window, filename)
            if not capture.success or capture.path is None:
                last_result = TemplateMatchResult(found=False, reason=capture.summary())
                time.sleep(config.success_poll_interval_ms / 1000)
                continue

            result = self.matcher.find_in_image(
                screenshot_path=capture.path,
                template_path=template_path,
                search_region=config.success_search_region,
                threshold=config.success_match_threshold,
                step=1,
            )
            self.context.logger.info("零式系统结果验证轮询 #%s: %s", attempt, result.summary())
            if result.found:
                return result

            last_result = result
            time.sleep(config.success_poll_interval_ms / 1000)

        return TemplateMatchResult(
            found=False,
            reason=f"等待零式系统页面超时，最后结果：{last_result.summary()}",
        )
