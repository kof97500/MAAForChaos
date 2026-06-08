from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ProgressState:
    stage: str
    step: str
    status: str
    detail: str
    updated_at: datetime


class ProgressReporter:
    def __init__(self) -> None:
        self.current: ProgressState | None = None

    def update(self, stage: str, step: str, status: str, detail: str = "") -> None:
        self.current = ProgressState(
            stage=stage,
            step=step,
            status=status,
            detail=detail,
            updated_at=datetime.now(),
        )
        print(
            f"[阶段] {stage}\n"
            f"[步骤] {step}\n"
            f"[状态] {status}\n"
            f"[详情] {detail or '-'}\n"
        )
