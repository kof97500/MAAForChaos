from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
import time

from czn_automation.config import SearchRegion
from czn_automation.recognition.template_match import TemplateMatchResult, TemplateMatcher
from czn_automation.runtime.context import RunContext
from czn_automation.waiters.template_waiter import TemplateWaitResult, TemplateWaiter
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
    DETECT_CODEX_BUTTON = auto()
    CLICK_CODEX_BUTTON = auto()
    WAIT_FOR_CODEX_PAGE = auto()
    DETECT_FIRST_CODEX_ENTRY = auto()
    CLICK_FIRST_CODEX_ENTRY = auto()
    DETECT_CODEX_ENTER_BUTTON = auto()
    CLICK_CODEX_ENTER_BUTTON = auto()
    WAIT_FOR_TEAM_SETUP_PAGE = auto()
    DETECT_TEAM_SETUP_ENTER_BUTTON = auto()
    CLICK_TEAM_SETUP_ENTER_BUTTON = auto()
    WAIT_FOR_ROGUELIKE_ENTRY = auto()
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
        self.template_waiter = TemplateWaiter(context, self.screenshot_service, self.matcher)

        self.current_state = KariesiState.ATTACH_WINDOW
        self.failure_reason = ""

        self.attach_result: AttachResult | None = None
        self.window: WindowInfo | None = None
        self.before_capture: CaptureResult | None = None
        self.kariesi_match: TemplateMatchResult | None = None
        self.zero_system_match: TemplateMatchResult | None = None
        self.codex_button_match: TemplateMatchResult | None = None
        self.first_codex_match: TemplateMatchResult | None = None
        self.codex_enter_match: TemplateMatchResult | None = None
        self.team_setup_enter_match: TemplateMatchResult | None = None
        self.click_result: ClickResult | None = None

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
            KariesiState.DETECT_CODEX_BUTTON: self._detect_codex_button,
            KariesiState.CLICK_CODEX_BUTTON: self._click_codex_button,
            KariesiState.WAIT_FOR_CODEX_PAGE: self._wait_for_codex_page,
            KariesiState.DETECT_FIRST_CODEX_ENTRY: self._detect_first_codex_entry,
            KariesiState.CLICK_FIRST_CODEX_ENTRY: self._click_first_codex_entry,
            KariesiState.DETECT_CODEX_ENTER_BUTTON: self._detect_codex_enter_button,
            KariesiState.CLICK_CODEX_ENTER_BUTTON: self._click_codex_enter_button,
            KariesiState.WAIT_FOR_TEAM_SETUP_PAGE: self._wait_for_team_setup_page,
            KariesiState.DETECT_TEAM_SETUP_ENTER_BUTTON: self._detect_team_setup_enter_button,
            KariesiState.CLICK_TEAM_SETUP_ENTER_BUTTON: self._click_team_setup_enter_button,
            KariesiState.WAIT_FOR_ROGUELIKE_ENTRY: self._wait_for_roguelike_entry,
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
            self.failure_reason = self.before_capture.summary()
            return KariesiState.FAILED

        return KariesiState.DETECT_KARIESI_BUTTON

    def _detect_kariesi_button(self) -> KariesiState:
        if self.before_capture is None or self.before_capture.path is None:
            self.failure_reason = "点击前截图不可用，无法识别卡厄思入口"
            return KariesiState.FAILED

        config = self.context.config.input_validation
        self.context.progress.update(
            stage="按钮识别",
            step="识别卡厄思入口",
            status="进行中",
            detail=f"template={config.template_path}",
        )
        match = self._match_capture(
            self.before_capture.path,
            self.context.root_dir / config.template_path,
            config.search_region,
            config.match_threshold,
            config.search_step,
        )
        self.kariesi_match = match
        if not match.found:
            return self._fail_with_progress(
                stage="按钮识别",
                step="识别卡厄思入口",
                reason=match.summary(),
            )

        self.context.progress.update(
            stage="按钮识别",
            step="识别卡厄思入口",
            status="成功",
            detail=match.summary(),
        )
        return KariesiState.CLICK_KARIESI_BUTTON

    def _click_kariesi_button(self) -> KariesiState:
        if self.window is None or self.kariesi_match is None:
            self.failure_reason = "窗口或卡厄思入口识别结果缺失"
            return KariesiState.FAILED

        click_result = self._click_match(
            stage="输入验证",
            step="点击卡厄思入口",
            window=self.window,
            match=self.kariesi_match,
        )
        if not click_result.success:
            return self._fail_with_progress(
                stage="输入验证",
                step="点击卡厄思入口",
                reason=click_result.summary(),
            )

        time.sleep(self.context.config.input_validation.post_click_wait_ms / 1000)
        return KariesiState.WAIT_FOR_KARIESI_PAGE

    def _wait_for_kariesi_page(self) -> KariesiState:
        result = self._wait_for_template(
            stage="结果验证",
            step="等待卡厄思页面稳定出现",
            template_path=self.context.root_dir / self.context.config.input_validation.success_template_path,
            search_region=self.context.config.input_validation.success_search_region,
            threshold=self.context.config.input_validation.success_match_threshold,
            step_size=1,
            timeout_ms=self.context.config.input_validation.success_timeout_ms,
            poll_interval_ms=self.context.config.input_validation.success_poll_interval_ms,
            screenshot_prefix="after_input_click",
            log_prefix="卡厄思结果验证",
        )
        if not result.found:
            return self._fail_with_progress(
                stage="结果验证",
                step="等待卡厄思页面稳定出现",
                reason=result.summary(),
            )

        self.screenshot_service.capture_named_debug_file(self.window, "kariesi_page_ready.bmp")
        self.context.progress.update(
            stage="结果验证",
            step="等待卡厄思页面稳定出现",
            status="成功",
            detail=result.summary(),
        )
        return KariesiState.DETECT_ZERO_SYSTEM_ENTRY

    def _detect_zero_system_entry(self) -> KariesiState:
        config = self.context.config.zero_system
        result = self._wait_for_template(
            stage="按钮识别",
            step="识别零式系统入口",
            template_path=self.context.root_dir / config.template_path,
            search_region=config.search_region,
            threshold=config.match_threshold,
            step_size=config.search_step,
            timeout_ms=config.detect_timeout_ms,
            poll_interval_ms=config.detect_poll_interval_ms,
            screenshot_prefix="before_zero_system_click",
            log_prefix="零式系统入口",
        )
        self.zero_system_match = result.match
        if not result.found:
            return self._fail_with_progress(
                stage="按钮识别",
                step="识别零式系统入口",
                reason=result.summary(),
            )

        self.context.progress.update(
            stage="按钮识别",
            step="识别零式系统入口",
            status="成功",
            detail=result.summary(),
        )
        return KariesiState.CLICK_ZERO_SYSTEM_ENTRY

    def _click_zero_system_entry(self) -> KariesiState:
        if self.window is None or self.zero_system_match is None:
            self.failure_reason = "窗口或零式系统入口识别结果缺失"
            return KariesiState.FAILED

        click_result = self._click_match(
            stage="输入验证",
            step="点击零式系统入口",
            window=self.window,
            match=self.zero_system_match,
        )
        if not click_result.success:
            return self._fail_with_progress(
                stage="输入验证",
                step="点击零式系统入口",
                reason=click_result.summary(),
            )

        time.sleep(self.context.config.zero_system.post_click_wait_ms / 1000)
        return KariesiState.WAIT_FOR_ZERO_SYSTEM_PAGE

    def _wait_for_zero_system_page(self) -> KariesiState:
        config = self.context.config.zero_system
        result = self._wait_for_template(
            stage="结果验证",
            step="等待零式系统页面稳定出现",
            template_path=self.context.root_dir / config.success_template_path,
            search_region=config.success_search_region,
            threshold=config.success_match_threshold,
            step_size=1,
            timeout_ms=config.success_timeout_ms,
            poll_interval_ms=config.success_poll_interval_ms,
            screenshot_prefix="after_zero_system_click",
            log_prefix="零式系统结果验证",
        )
        if not result.found:
            return self._fail_with_progress(
                stage="结果验证",
                step="等待零式系统页面稳定出现",
                reason=result.summary(),
            )

        self.screenshot_service.capture_named_debug_file(self.window, "zero_system_page_ready.bmp")
        self.context.progress.update(
            stage="结果验证",
            step="等待零式系统页面稳定出现",
            status="成功",
            detail=result.summary(),
        )
        return KariesiState.DETECT_CODEX_BUTTON

    def _detect_codex_button(self) -> KariesiState:
        config = self.context.config.codex_flow
        result = self._wait_for_template(
            stage="按钮识别",
            step="识别法典按钮",
            template_path=self.context.root_dir / config.button_template_path,
            search_region=config.button_search_region,
            threshold=config.button_match_threshold,
            step_size=config.button_search_step,
            timeout_ms=config.page_timeout_ms,
            poll_interval_ms=config.page_poll_interval_ms,
            screenshot_prefix="before_codex_button_click",
            log_prefix="法典按钮",
        )
        self.codex_button_match = result.match
        if not result.found:
            return self._fail_with_progress(
                stage="按钮识别",
                step="识别法典按钮",
                reason=result.summary(),
            )

        self.context.progress.update(
            stage="按钮识别",
            step="识别法典按钮",
            status="成功",
            detail=result.summary(),
        )
        return KariesiState.CLICK_CODEX_BUTTON

    def _click_codex_button(self) -> KariesiState:
        if self.window is None or self.codex_button_match is None:
            self.failure_reason = "窗口或法典按钮识别结果缺失"
            return KariesiState.FAILED

        click_result = self._click_match(
            stage="输入验证",
            step="点击法典按钮",
            window=self.window,
            match=self.codex_button_match,
        )
        if not click_result.success:
            return self._fail_with_progress(
                stage="输入验证",
                step="点击法典按钮",
                reason=click_result.summary(),
            )

        time.sleep(self.context.config.codex_flow.post_click_wait_ms / 1000)
        return KariesiState.WAIT_FOR_CODEX_PAGE

    def _wait_for_codex_page(self) -> KariesiState:
        config = self.context.config.codex_flow
        result = self._wait_for_template(
            stage="结果验证",
            step="等待法典选择页面稳定出现",
            template_path=self.context.root_dir / config.page_template_path,
            search_region=config.page_search_region,
            threshold=config.page_match_threshold,
            step_size=2,
            timeout_ms=config.page_timeout_ms,
            poll_interval_ms=config.page_poll_interval_ms,
            screenshot_prefix="after_codex_button_click",
            log_prefix="法典页面验证",
        )
        if not result.found:
            return self._fail_with_progress(
                stage="结果验证",
                step="等待法典选择页面稳定出现",
                reason=result.summary(),
            )

        self.screenshot_service.capture_named_debug_file(self.window, "codex_page_ready.bmp")
        self.context.progress.update(
            stage="结果验证",
            step="等待法典选择页面稳定出现",
            status="成功",
            detail=result.summary(),
        )
        return KariesiState.DETECT_FIRST_CODEX_ENTRY

    def _detect_first_codex_entry(self) -> KariesiState:
        config = self.context.config.codex_flow
        result = self._wait_for_template(
            stage="按钮识别",
            step="识别第一个法典槽位",
            template_path=self.context.root_dir / config.first_codex_template_path,
            search_region=config.first_codex_search_region,
            threshold=config.first_codex_match_threshold,
            step_size=config.first_codex_search_step,
            timeout_ms=config.page_timeout_ms,
            poll_interval_ms=config.page_poll_interval_ms,
            screenshot_prefix="before_first_codex_click",
            log_prefix="法典01入口",
        )
        self.first_codex_match = result.match
        if not result.found:
            return self._fail_with_progress(
                stage="按钮识别",
                step="识别第一个法典槽位",
                reason=result.summary(),
            )

        self.context.progress.update(
            stage="按钮识别",
            step="识别第一个法典槽位",
            status="成功",
            detail=result.summary(),
        )
        return KariesiState.CLICK_FIRST_CODEX_ENTRY

    def _click_first_codex_entry(self) -> KariesiState:
        if self.window is None or self.first_codex_match is None:
            self.failure_reason = "窗口或第一个法典槽位识别结果缺失"
            return KariesiState.FAILED

        click_result = self._click_match(
            stage="输入验证",
            step="点击第一个法典槽位",
            window=self.window,
            match=self.first_codex_match,
        )
        if not click_result.success:
            return self._fail_with_progress(
                stage="输入验证",
                step="点击第一个法典槽位",
                reason=click_result.summary(),
            )

        time.sleep(self.context.config.codex_flow.post_click_wait_ms / 1000)
        return KariesiState.DETECT_CODEX_ENTER_BUTTON

    def _detect_codex_enter_button(self) -> KariesiState:
        config = self.context.config.codex_flow
        result = self._wait_for_template(
            stage="按钮识别",
            step="识别法典页面进入按钮",
            template_path=self.context.root_dir / config.enter_button_template_path,
            search_region=config.enter_button_search_region,
            threshold=config.enter_button_match_threshold,
            step_size=config.enter_button_search_step,
            timeout_ms=config.page_timeout_ms,
            poll_interval_ms=config.page_poll_interval_ms,
            screenshot_prefix="before_codex_enter_click",
            log_prefix="法典进入按钮",
        )
        self.codex_enter_match = result.match
        if not result.found:
            return self._fail_with_progress(
                stage="按钮识别",
                step="识别法典页面进入按钮",
                reason=result.summary(),
            )

        self.context.progress.update(
            stage="按钮识别",
            step="识别法典页面进入按钮",
            status="成功",
            detail=result.summary(),
        )
        return KariesiState.CLICK_CODEX_ENTER_BUTTON

    def _click_codex_enter_button(self) -> KariesiState:
        if self.window is None or self.codex_enter_match is None:
            self.failure_reason = "窗口或法典进入按钮识别结果缺失"
            return KariesiState.FAILED

        click_result = self._click_match(
            stage="输入验证",
            step="点击法典页面进入按钮",
            window=self.window,
            match=self.codex_enter_match,
        )
        if not click_result.success:
            return self._fail_with_progress(
                stage="输入验证",
                step="点击法典页面进入按钮",
                reason=click_result.summary(),
            )

        time.sleep(self.context.config.codex_flow.post_click_wait_ms / 1000)
        return KariesiState.WAIT_FOR_TEAM_SETUP_PAGE

    def _wait_for_team_setup_page(self) -> KariesiState:
        config = self.context.config.team_setup
        result = self._wait_for_template(
            stage="结果验证",
            step="等待配置队伍页面稳定出现",
            template_path=self.context.root_dir / config.page_template_path,
            search_region=config.page_search_region,
            threshold=config.page_match_threshold,
            step_size=1,
            timeout_ms=config.page_timeout_ms,
            poll_interval_ms=config.page_poll_interval_ms,
            screenshot_prefix="after_codex_enter_click",
            log_prefix="配置队伍页面验证",
        )
        if not result.found:
            return self._fail_with_progress(
                stage="结果验证",
                step="等待配置队伍页面稳定出现",
                reason=result.summary(),
            )

        self.screenshot_service.capture_named_debug_file(self.window, "team_setup_page_ready.bmp")
        self.context.progress.update(
            stage="结果验证",
            step="等待配置队伍页面稳定出现",
            status="成功",
            detail=result.summary(),
        )
        return KariesiState.DETECT_TEAM_SETUP_ENTER_BUTTON

    def _detect_team_setup_enter_button(self) -> KariesiState:
        config = self.context.config.team_setup
        result = self._wait_for_template(
            stage="按钮识别",
            step="识别配置队伍页面进入按钮",
            template_path=self.context.root_dir / config.enter_button_template_path,
            search_region=config.enter_button_search_region,
            threshold=config.enter_button_match_threshold,
            step_size=config.enter_button_search_step,
            timeout_ms=config.page_timeout_ms,
            poll_interval_ms=config.page_poll_interval_ms,
            screenshot_prefix="before_team_setup_enter_click",
            log_prefix="配置队伍进入按钮",
        )
        self.team_setup_enter_match = result.match
        if not result.found:
            return self._fail_with_progress(
                stage="按钮识别",
                step="识别配置队伍页面进入按钮",
                reason=result.summary(),
            )

        self.context.progress.update(
            stage="按钮识别",
            step="识别配置队伍页面进入按钮",
            status="成功",
            detail=result.summary(),
        )
        return KariesiState.CLICK_TEAM_SETUP_ENTER_BUTTON

    def _click_team_setup_enter_button(self) -> KariesiState:
        if self.window is None or self.team_setup_enter_match is None:
            self.failure_reason = "窗口或配置队伍进入按钮识别结果缺失"
            return KariesiState.FAILED

        click_result = self._click_match(
            stage="输入验证",
            step="点击配置队伍页面进入按钮",
            window=self.window,
            match=self.team_setup_enter_match,
        )
        if not click_result.success:
            return self._fail_with_progress(
                stage="输入验证",
                step="点击配置队伍页面进入按钮",
                reason=click_result.summary(),
            )

        time.sleep(self.context.config.team_setup.post_click_wait_ms / 1000)
        return KariesiState.WAIT_FOR_ROGUELIKE_ENTRY

    def _wait_for_roguelike_entry(self) -> KariesiState:
        config = self.context.config.team_setup
        result = self._wait_for_template(
            stage="结果验证",
            step="等待肉鸽入口界面稳定出现",
            template_path=self.context.root_dir / config.success_template_path,
            search_region=config.success_search_region,
            threshold=config.success_match_threshold,
            step_size=1,
            timeout_ms=config.transition_timeout_ms,
            poll_interval_ms=config.transition_poll_interval_ms,
            screenshot_prefix="after_team_setup_enter_click",
            log_prefix="肉鸽入口验证",
        )
        if not result.found:
            return self._fail_with_progress(
                stage="结果验证",
                step="等待肉鸽入口界面稳定出现",
                reason=result.summary(),
            )

        self.screenshot_service.capture_named_debug_file(self.window, "roguelike_entry_ready.bmp")
        self.context.progress.update(
            stage="结果验证",
            step="等待肉鸽入口界面稳定出现",
            status="成功",
            detail=result.summary(),
        )
        return KariesiState.SUCCESS

    def _match_capture(
        self,
        screenshot_path: Path,
        template_path: Path,
        search_region: SearchRegion,
        threshold: float,
        step_size: int,
    ) -> TemplateMatchResult:
        return self.matcher.find_in_image(
            screenshot_path=screenshot_path,
            template_path=template_path,
            search_region=search_region,
            threshold=threshold,
            step=step_size,
        )

    def _wait_for_template(
        self,
        *,
        stage: str,
        step: str,
        template_path: Path,
        search_region: SearchRegion,
        threshold: float,
        step_size: int,
        timeout_ms: int,
        poll_interval_ms: int,
        screenshot_prefix: str,
        log_prefix: str,
    ) -> TemplateWaitResult:
        if self.window is None:
            return TemplateWaitResult(
                found=False,
                match=TemplateMatchResult(found=False, reason="窗口缺失，无法执行等待"),
                capture=None,
            )

        self.context.progress.update(
            stage=stage,
            step=step,
            status="进行中",
            detail=f"timeout={timeout_ms}ms interval={poll_interval_ms}ms",
        )
        return self.template_waiter.wait_for_template(
            self.window,
            template_path=template_path,
            search_region=search_region,
            threshold=threshold,
            step=step_size,
            timeout_ms=timeout_ms,
            poll_interval_ms=poll_interval_ms,
            screenshot_prefix=screenshot_prefix,
            log_prefix=log_prefix,
        )

    def _click_match(
        self,
        *,
        stage: str,
        step: str,
        window: WindowInfo,
        match: TemplateMatchResult,
    ) -> ClickResult:
        self.context.progress.update(
            stage=stage,
            step=step,
            status="进行中",
            detail=f"client=({match.center_x},{match.center_y}) score={match.score:.2f}",
        )
        click_result = self.input_service.click_client_point(
            window,
            match.center_x,
            match.center_y,
        )
        self.click_result = click_result
        if click_result.success:
            self.context.logger.info("%s完成：%s", step, click_result.summary())
            self.context.progress.update(
                stage=stage,
                step=step,
                status="成功",
                detail=click_result.summary(),
            )
        return click_result

    def _fail_with_progress(self, *, stage: str, step: str, reason: str) -> KariesiState:
        self.failure_reason = reason
        self.context.progress.update(stage=stage, step=step, status="失败", detail=reason)
        self.context.logger.warning("%s失败：%s", step, reason)
        return KariesiState.FAILED
