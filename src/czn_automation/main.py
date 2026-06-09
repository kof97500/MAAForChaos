from __future__ import annotations

from pathlib import Path
import time

from czn_automation.config import load_config
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

        screenshot_service.capture_named_debug_file(attach_result.window, "before_input_click.bmp")
        input_service = WindowInputService(context)
        point = config.input_validation.click_point
        context.progress.update(
            stage="输入验证",
            step="执行固定坐标点击",
            status="进行中",
            detail=f"client=({point.x},{point.y})",
        )
        click_result = input_service.click_client_point(attach_result.window, point.x, point.y)
        if not click_result.success:
            context.progress.update(
                stage="输入验证",
                step="执行固定坐标点击",
                status="失败",
                detail=click_result.summary(),
            )
            context.logger.warning("输入验证失败：%s", click_result.summary())
            return 1

        context.logger.info("输入验证点击完成：%s", click_result.summary())
        time.sleep(config.input_validation.post_click_wait_ms / 1000)
        after_capture = screenshot_service.capture_named_debug_file(
            attach_result.window,
            "after_input_click.bmp",
        )
        if after_capture.success:
            context.progress.update(
                stage="输入验证",
                step="执行固定坐标点击",
                status="成功",
                detail=f"{click_result.summary()} after={after_capture.summary()}",
            )
            context.logger.info("输入验证完成：%s after=%s", click_result.summary(), after_capture.summary())
            return 0

        context.progress.update(
            stage="输入验证",
            step="执行固定坐标点击",
            status="失败",
            detail=after_capture.summary(),
        )
        context.logger.warning("输入后截图失败：%s", after_capture.summary())
        return 1

    context.progress.update(
        stage="窗口连接",
        step="连接目标窗口",
        status="失败",
        detail=attach_result.summary(),
    )
    context.logger.warning("窗口连接流程结束，但未找到目标窗口：%s", attach_result.summary())
    return 1
