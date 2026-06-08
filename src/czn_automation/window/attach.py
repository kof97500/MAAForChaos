from __future__ import annotations

from dataclasses import dataclass
from platform import system

from czn_automation.runtime.context import RunContext


@dataclass
class AttachResult:
    found: bool
    matched_title: str = ""
    reason: str = ""

    def summary(self) -> str:
        if self.found:
            return f"matched_title={self.matched_title}"
        return self.reason or "unknown"


class GameWindowService:
    def __init__(self, context: RunContext) -> None:
        self.context = context

    def attach(self) -> AttachResult:
        self.context.progress.update(
            stage="窗口连接",
            step="扫描系统窗口",
            status="进行中",
            detail="当前为占位实现，后续接入 Win32 窗口枚举",
        )
        self.context.logger.info("开始窗口扫描")

        if system() != "Windows":
            return AttachResult(
                found=False,
                reason="当前不是 Windows 环境，窗口连接能力将在 Windows 机器上验证",
            )

        for keyword in self.context.config.game_window.title_keywords:
            self.context.logger.debug("尝试匹配窗口关键字：%s", keyword)

        return AttachResult(
            found=False,
            reason="尚未接入 Win32 枚举与匹配逻辑",
        )
