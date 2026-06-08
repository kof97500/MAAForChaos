from __future__ import annotations

from pathlib import Path

from czn_automation.config import load_config
from czn_automation.runtime.context import RunContext
from czn_automation.runtime.logger import setup_logger
from czn_automation.runtime.progress import ProgressReporter
from czn_automation.window.attach import GameWindowService


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
    context.progress.update(
        stage="初始化",
        step="加载配置与运行上下文",
        status="进行中",
        detail=f"environment={config.environment}",
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
        return 0

    context.progress.update(
        stage="窗口连接",
        step="连接目标窗口",
        status="失败",
        detail=attach_result.summary(),
    )
    context.logger.warning("窗口连接流程结束，但未找到目标窗口：%s", attach_result.summary())
    return 1
