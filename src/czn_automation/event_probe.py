from __future__ import annotations

import argparse
from pathlib import Path

from czn_automation.config import load_config
from czn_automation.events.detector import EventDetector
from czn_automation.runtime.context import RunContext
from czn_automation.runtime.dpi import enable_dpi_awareness
from czn_automation.runtime.logger import setup_logger
from czn_automation.runtime.progress import ProgressReporter
from czn_automation.window.attach import GameWindowService
from czn_automation.window.screenshot import WindowScreenshotService


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="卡厄思事件页检测工具")
    parser.add_argument(
        "--image",
        type=str,
        default="",
        help="离线检测截图路径；不传则直接连接当前游戏窗口并截图",
    )
    args = parser.parse_args(argv)

    root_dir = Path(__file__).resolve().parents[2]
    config = load_config(root_dir / "config" / "app.example.json")
    logger = setup_logger(
        root_dir=root_dir,
        level=config.logging.level,
        file_path=config.logging.file_path,
    )
    progress = ProgressReporter()
    context = RunContext(root_dir=root_dir, logger=logger, progress=progress, config=config)

    context.logger.info("事件检测工具启动")
    dpi_mode = enable_dpi_awareness()
    context.logger.info("DPI 感知模式：%s", dpi_mode)
    detector = EventDetector()

    screenshot_path = _resolve_screenshot_path(args.image, context)
    if screenshot_path is None:
        return 1

    context.progress.update(
        stage="事件检测",
        step="分析事件页布局",
        status="进行中",
        detail=str(screenshot_path),
    )
    result = detector.detect(screenshot_path)
    report_path = detector.save_debug_artifacts(result=result, root_dir=root_dir)

    if result.is_event_page:
        detail = (
            f"option_count={result.option_count} "
            f"button_center=({result.event_button_rect.center_x},{result.event_button_rect.center_y}) "
            f"report={report_path}"
        )
        context.progress.update(
            stage="事件检测",
            step="分析事件页布局",
            status="成功",
            detail=detail,
        )
        context.logger.info("事件检测成功：%s", result.summary())
        return 0

    context.progress.update(
        stage="事件检测",
        step="分析事件页布局",
        status="失败",
        detail=f"{result.reason} report={report_path}",
    )
    context.logger.warning("事件检测失败：%s", result.summary())
    return 1


def _resolve_screenshot_path(image_arg: str, context: RunContext) -> Path | None:
    if image_arg:
        image_path = Path(image_arg).expanduser().resolve()
        if not image_path.exists():
            context.progress.update(
                stage="事件检测",
                step="加载输入截图",
                status="失败",
                detail=f"文件不存在：{image_path}",
            )
            context.logger.warning("事件检测输入截图不存在：%s", image_path)
            return None
        context.progress.update(
            stage="事件检测",
            step="加载输入截图",
            status="成功",
            detail=str(image_path),
        )
        return image_path

    context.progress.update(
        stage="事件检测",
        step="连接游戏窗口并截图",
        status="进行中",
        detail="未传入截图，尝试从当前游戏窗口抓取",
    )
    window_service = GameWindowService(context)
    screenshot_service = WindowScreenshotService(context)
    attach_result = window_service.attach()
    if not attach_result.found or attach_result.window is None:
        context.progress.update(
            stage="事件检测",
            step="连接游戏窗口并截图",
            status="失败",
            detail=attach_result.summary(),
        )
        return None

    capture_result = screenshot_service.capture_named_debug_file(
        attach_result.window,
        "event_probe_source.bmp",
    )
    if not capture_result.success or capture_result.path is None:
        context.progress.update(
            stage="事件检测",
            step="连接游戏窗口并截图",
            status="失败",
            detail=capture_result.summary(),
        )
        return None

    context.progress.update(
        stage="事件检测",
        step="连接游戏窗口并截图",
        status="成功",
        detail=str(capture_result.path),
    )
    return capture_result.path


if __name__ == "__main__":
    raise SystemExit(main())
