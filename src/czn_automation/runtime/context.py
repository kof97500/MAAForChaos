from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from logging import Logger

from czn_automation.config import AppConfig
from czn_automation.runtime.progress import ProgressReporter


@dataclass
class RunContext:
    root_dir: Path
    logger: Logger
    progress: ProgressReporter
    config: AppConfig
