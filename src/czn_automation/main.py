from __future__ import annotations

from pathlib import Path

from czn_automation.config import load_config
from czn_automation.runtime.context import RunContext
from czn_automation.runtime.dpi import enable_dpi_awareness
from czn_automation.runtime.logger import setup_logger
from czn_automation.runtime.progress import ProgressReporter
from czn_automation.state_machine.kariesi_flow import KariesiEntryStateMachine


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
    flow = KariesiEntryStateMachine(context)
    result = flow.run()
    if result.success:
        context.logger.info("状态机执行完成，最终状态：%s", result.final_state.name)
        return 0

    context.logger.warning(
        "状态机执行失败，最终状态：%s reason=%s",
        result.final_state.name,
        result.reason,
    )
    return 1
