from __future__ import annotations

from pathlib import Path
import time

from czn_automation.config import load_config
from czn_automation.recognition.template_match import TemplateMatchResult, TemplateMatcher
from czn_automation.runtime.context import RunContext
from czn_automation.runtime.dpi import enable_dpi_awareness
from czn_automation.runtime.logger import setup_logger
from czn_automation.runtime.progress import ProgressReporter
from czn_automation.window.attach import GameWindowService
from czn_automation.window.input import WindowInputService
from czn_automation.window.screenshot import WindowScreenshotService


def main() -> int:
    root_dir = Path(__file__).resolve().parents[2]
    config_path = root_dir / "config" / "app.example.json"
    config = load_config(config_path)

    logger = setup_logger(
        root_dir=root_dir,
        level=config.logging.level,
        file_path=config.logging.file_path,
    )
    progress = ProgressReporter()
    context = RunContext(root_dir=root_dir, logger=logger, progress=progress, config=config)

    context.logger.info("程序启动")
    dpi_mode = enable_dpi_awareness()
    context.logger.info("DPI 感知模式：%s", dpi_mode)
    context.progress.update(
        stage="初始化",
        step="加载配置与运行上下文",
        status="进行中",
        detail=f"environment={config.environment}, dpi={dpi_mode}",
    )

    window_service = GameWindowService(context)
    attach_result = window_service.attach()

    if attach_result.found:
        context.progress.update(
            stage="窗口连接",
            step="连接目标窗口",
            status="成功",
            detail=attach_result.summary(),
        )
        context.logger.info("窗口连接流程完成：%s", attach_result.summary())

        screenshot_service = WindowScreenshotService(context)
        context.progress.update(
            stage="截图验证",
            step="保存首张窗口截图",
            status="进行中",
            detail="窗口已连接，开始抓取客户区截图",
        )
        capture_result = screenshot_service.capture_to_debug_file(attach_result.window)
        if capture_result.success:
            context.progress.update(
                stage="截图验证",
                step="保存首张窗口截图",
                status="成功",
                detail=capture_result.summary(),
            )
            context.logger.info("截图验证完成：%s", capture_result.summary())
        else:
            context.progress.update(
                stage="截图验证",
                step="保存首张窗口截图",
                status="失败",
                detail=capture_result.summary(),
            )
            context.logger.warning("截图验证失败：%s", capture_result.summary())
            return 1

        before_capture = screenshot_service.capture_named_debug_file(
            attach_result.window,
            "before_input_click.bmp",
        )
        if not before_capture.success:
            context.progress.update(
                stage="按钮识别",
                step="保存点击前截图",
                status="失败",
                detail=before_capture.summary(),
            )
            context.logger.warning("保存点击前截图失败：%s", before_capture.summary())
            return 1

        matcher = TemplateMatcher()
        template_path = root_dir / config.input_validation.template_path
        context.progress.update(
            stage="按钮识别",
            step="识别卡厄思图标按钮",
            status="进行中",
            detail=f"template={config.input_validation.template_path}",
        )
        match = matcher.find_in_image(
            screenshot_path=before_capture.path,
            template_path=template_path,
            search_region=config.input_validation.search_region,
            threshold=config.input_validation.match_threshold,
            step=config.input_validation.search_step,
        )
        if not match.found:
            context.progress.update(
                stage="按钮识别",
                step="识别卡厄思图标按钮",
                status="失败",
                detail=match.summary(),
            )
            context.logger.warning("按钮识别失败：%s", match.summary())
            return 1

        context.progress.update(
            stage="按钮识别",
            step="识别卡厄思图标按钮",
            status="成功",
            detail=match.summary(),
        )
        context.logger.info("按钮识别成功：%s", match.summary())

        input_service = WindowInputService(context)
        context.progress.update(
            stage="输入验证",
            step="点击卡厄思图标按钮",
            status="进行中",
            detail=f"client=({match.center_x},{match.center_y}) score={match.score:.2f}",
        )
        click_result = input_service.click_client_point(
            attach_result.window,
            match.center_x,
            match.center_y,
        )
        if not click_result.success:
            context.progress.update(
                stage="输入验证",
                step="点击卡厄思图标按钮",
                status="失败",
                detail=click_result.summary(),
            )
            context.logger.warning("输入验证失败：%s", click_result.summary())
            return 1

        context.logger.info("输入验证点击完成：%s", click_result.summary())
        time.sleep(config.input_validation.post_click_wait_ms / 1000)
        validation_result = wait_for_success_page(
            context=context,
            screenshot_service=screenshot_service,
            matcher=matcher,
            window=attach_result.window,
        )
        if validation_result.found:
            context.progress.update(
                stage="结果验证",
                step="等待卡厄思页面稳定出现",
                status="成功",
                detail=validation_result.summary(),
            )
            context.logger.info("结果验证成功：%s", validation_result.summary())
            return 0

        context.progress.update(
            stage="结果验证",
            step="等待卡厄思页面稳定出现",
            status="失败",
            detail=validation_result.summary(),
        )
        context.logger.warning("结果验证失败：%s", validation_result.summary())
        return 1

    context.progress.update(
        stage="窗口连接",
        step="连接目标窗口",
        status="失败",
        detail=attach_result.summary(),
    )
    context.logger.warning("窗口连接流程结束，但未找到目标窗口：%s", attach_result.summary())
    return 1


def wait_for_success_page(
    context: RunContext,
    screenshot_service: WindowScreenshotService,
    matcher: TemplateMatcher,
    window,
) -> TemplateMatchResult:
    config = context.config.input_validation
    deadline = time.time() + (config.success_timeout_ms / 1000)
    attempt = 0
    template_path = context.root_dir / config.success_template_path
    last_result = TemplateMatchResult(found=False, reason="尚未开始轮询")

    context.progress.update(
        stage="结果验证",
        step="等待卡厄思页面稳定出现",
        status="进行中",
        detail=f"timeout={config.success_timeout_ms}ms interval={config.success_poll_interval_ms}ms",
    )

    while time.time() < deadline:
        attempt += 1
        filename = f"after_input_click_{attempt:02d}.bmp"
        capture = screenshot_service.capture_named_debug_file(window, filename)
        if not capture.success:
            last_result = TemplateMatchResult(found=False, reason=capture.summary())
            time.sleep(config.success_poll_interval_ms / 1000)
            continue

        result = matcher.find_in_image(
            screenshot_path=capture.path,
            template_path=template_path,
            search_region=config.success_search_region,
            threshold=config.success_match_threshold,
            step=1,
        )
        context.logger.info("结果验证轮询 #%s: %s", attempt, result.summary())
        if result.found:
            return result

        last_result = result
        time.sleep(config.success_poll_interval_ms / 1000)

    return TemplateMatchResult(
        found=False,
        reason=f"等待目标页面超时，最后结果：{last_result.summary()}",
    )
