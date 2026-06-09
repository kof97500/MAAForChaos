from __future__ import annotations

import argparse
from pathlib import Path
import time

from czn_automation.config import load_config
from czn_automation.events.detector import EventDetector
from czn_automation.runtime.context import RunContext
from czn_automation.runtime.dpi import enable_dpi_awareness
from czn_automation.runtime.logger import setup_logger
from czn_automation.runtime.progress import ProgressReporter
from czn_automation.window.attach import GameWindowService
from czn_automation.window.input import WindowInputService
from czn_automation.window.screenshot import WindowScreenshotService


DETAIL_OPEN_TIMEOUT_MS = 5000
DETAIL_OPEN_POLL_INTERVAL_MS = 400


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

    screenshot_path = _resolve_screenshot_path(args.image, context, detector)
    if screenshot_path is None:
        return 1

    context.progress.update(
        stage="事件检测",
        step="分析事件详情与选项",
        status="进行中",
        detail=str(screenshot_path),
    )
    result = detector.detect(screenshot_path)
    report_path = detector.save_debug_artifacts(result=result, root_dir=root_dir)

    if result.is_event_page:
        detail = (
            f"option_count={result.option_count} "
            f"button_center=({result.event_button_rect.center_x},{result.event_button_rect.center_y}) "
            f"event_name={result.event_name or '-'} "
            f"ocr={'yes' if result.ocr_available else 'no'} "
            f"report={report_path}"
        )
        context.progress.update(
            stage="事件检测",
            step="分析事件详情与选项",
            status="成功",
            detail=detail,
        )
        context.logger.info("事件检测成功：%s", result.summary())
        return 0

    context.progress.update(
        stage="事件检测",
        step="分析事件详情与选项",
        status="失败",
        detail=f"{result.reason} report={report_path}",
    )
    context.logger.warning("事件检测失败：%s", result.summary())
    return 1


def _resolve_screenshot_path(
    image_arg: str,
    context: RunContext,
    detector: EventDetector,
) -> Path | None:
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
        step="连接游戏窗口",
        status="进行中",
        detail="未传入截图，尝试连接当前游戏窗口并点击事件按钮",
    )
    window_service = GameWindowService(context)
    screenshot_service = WindowScreenshotService(context)
    input_service = WindowInputService(context)
    attach_result = window_service.attach()
    if not attach_result.found or attach_result.window is None:
        context.progress.update(
            stage="事件检测",
            step="连接游戏窗口",
            status="失败",
            detail=attach_result.summary(),
        )
        return None
    window = attach_result.window

    before_capture = screenshot_service.capture_named_debug_file(
        window,
        "event_probe_before_click.bmp",
    )
    if not before_capture.success or before_capture.path is None:
        context.progress.update(
            stage="事件检测",
            step="保存点击前截图",
            status="失败",
            detail=before_capture.summary(),
        )
        return None

    before_result = detector.detect(before_capture.path)
    button_rect = before_result.event_button_rect
    context.progress.update(
        stage="事件检测",
        step="点击事件信息按钮",
        status="进行中",
        detail=f"client=({button_rect.center_x},{button_rect.center_y})",
    )
    click_result = input_service.click_client_point(
        window,
        button_rect.center_x,
        button_rect.center_y,
    )
    if not click_result.success:
        context.progress.update(
            stage="事件检测",
            step="点击事件信息按钮",
            status="失败",
            detail=click_result.summary(),
        )
        return None

    context.progress.update(
        stage="事件检测",
        step="点击事件信息按钮",
        status="成功",
        detail=click_result.summary(),
    )
    time.sleep(0.4)

    capture_result = screenshot_service.capture_named_debug_file(
        window,
        "event_probe_after_click_00.bmp",
    )
    if not capture_result.success or capture_result.path is None:
        context.progress.update(
            stage="事件检测",
            step="保存点击后截图",
            status="失败",
            detail=capture_result.summary(),
        )
        return None

    context.progress.update(
        stage="事件检测",
        step="等待事件详情展开",
        status="成功",
        detail=str(capture_result.path),
    )
    return _wait_for_event_detail(
        context=context,
        detector=detector,
        screenshot_service=screenshot_service,
        window=window,
        initial_capture_path=capture_result.path,
    )


def _wait_for_event_detail(
    *,
    context: RunContext,
    detector: EventDetector,
    screenshot_service: WindowScreenshotService,
    window,
    initial_capture_path: Path,
) -> Path | None:
    deadline = time.time() + (DETAIL_OPEN_TIMEOUT_MS / 1000)
    attempt = 0
    last_path = initial_capture_path

    context.progress.update(
        stage="事件检测",
        step="等待事件详情展开",
        status="进行中",
        detail=(
            f"timeout={DETAIL_OPEN_TIMEOUT_MS}ms "
            f"interval={DETAIL_OPEN_POLL_INTERVAL_MS}ms"
        ),
    )

    while time.time() < deadline:
        attempt += 1
        if attempt == 1:
            capture_path = last_path
        else:
            capture_result = screenshot_service.capture_named_debug_file(
                window,
                f"event_probe_after_click_{attempt:02d}.bmp",
            )
            if not capture_result.success or capture_result.path is None:
                time.sleep(DETAIL_OPEN_POLL_INTERVAL_MS / 1000)
                continue
            capture_path = capture_result.path
            last_path = capture_path

        result = detector.detect(capture_path)
        context.logger.info(
            "事件详情等待轮询 #%s: detail_opened=%s event_name=%s option_count=%s",
            attempt,
            result.detail_opened,
            result.event_name or "-",
            result.option_count,
        )

        if result.detail_opened:
            if not detector.ocr_available or result.event_name:
                context.progress.update(
                    stage="事件检测",
                    step="等待事件详情展开",
                    status="成功",
                    detail=(
                        f"detail_opened={result.detail_opened} "
                        f"event_name={result.event_name or '-'}"
                    ),
                )
                return capture_path

        time.sleep(DETAIL_OPEN_POLL_INTERVAL_MS / 1000)

    context.progress.update(
        stage="事件检测",
        step="等待事件详情展开",
        status="失败",
        detail=f"超时，最后截图：{last_path}",
    )
    return None


if __name__ == "__main__":
    raise SystemExit(main())
