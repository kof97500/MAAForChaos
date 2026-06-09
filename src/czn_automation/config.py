from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Resolution:
    width: int
    height: int


@dataclass
class GameWindowConfig:
    title_keywords: list[str]
    supported_resolutions: list[Resolution]


@dataclass
class LoggingConfig:
    level: str
    file_path: str


@dataclass
class SearchRegion:
    left: int
    top: int
    width: int
    height: int


@dataclass
class InputValidationConfig:
    template_path: str
    search_region: SearchRegion
    match_threshold: float
    search_step: int
    post_click_wait_ms: int
    success_template_path: str
    success_search_region: SearchRegion
    success_match_threshold: float
    success_timeout_ms: int
    success_poll_interval_ms: int


@dataclass
class ZeroSystemConfig:
    template_path: str
    search_region: SearchRegion
    match_threshold: float
    search_step: int
    detect_timeout_ms: int
    detect_poll_interval_ms: int
    post_click_wait_ms: int
    success_template_path: str
    success_search_region: SearchRegion
    success_match_threshold: float
    success_timeout_ms: int
    success_poll_interval_ms: int


@dataclass
class AppConfig:
    name: str
    environment: str
    game_window: GameWindowConfig
    logging: LoggingConfig
    input_validation: InputValidationConfig
    zero_system: ZeroSystemConfig


def load_config(path: Path) -> AppConfig:
    data = json.loads(path.read_text(encoding="utf-8"))
    resolutions = [
        Resolution(width=item["width"], height=item["height"])
        for item in data["game_window"]["supported_resolutions"]
    ]

    return AppConfig(
        name=data["app"]["name"],
        environment=data["app"]["environment"],
        game_window=GameWindowConfig(
            title_keywords=data["game_window"]["title_keywords"],
            supported_resolutions=resolutions,
        ),
        logging=LoggingConfig(
            level=data["logging"]["level"],
            file_path=data["logging"]["file_path"],
        ),
        input_validation=InputValidationConfig(
            template_path=data["input_validation"]["template_path"],
            search_region=SearchRegion(
                left=data["input_validation"]["search_region"]["left"],
                top=data["input_validation"]["search_region"]["top"],
                width=data["input_validation"]["search_region"]["width"],
                height=data["input_validation"]["search_region"]["height"],
            ),
            match_threshold=float(data["input_validation"]["match_threshold"]),
            search_step=int(data["input_validation"]["search_step"]),
            post_click_wait_ms=data["input_validation"]["post_click_wait_ms"],
            success_template_path=data["input_validation"]["success_template_path"],
            success_search_region=SearchRegion(
                left=data["input_validation"]["success_search_region"]["left"],
                top=data["input_validation"]["success_search_region"]["top"],
                width=data["input_validation"]["success_search_region"]["width"],
                height=data["input_validation"]["success_search_region"]["height"],
            ),
            success_match_threshold=float(data["input_validation"]["success_match_threshold"]),
            success_timeout_ms=int(data["input_validation"]["success_timeout_ms"]),
            success_poll_interval_ms=int(data["input_validation"]["success_poll_interval_ms"]),
        ),
        zero_system=ZeroSystemConfig(
            template_path=data["zero_system"]["template_path"],
            search_region=SearchRegion(
                left=data["zero_system"]["search_region"]["left"],
                top=data["zero_system"]["search_region"]["top"],
                width=data["zero_system"]["search_region"]["width"],
                height=data["zero_system"]["search_region"]["height"],
            ),
            match_threshold=float(data["zero_system"]["match_threshold"]),
            search_step=int(data["zero_system"]["search_step"]),
            detect_timeout_ms=int(data["zero_system"]["detect_timeout_ms"]),
            detect_poll_interval_ms=int(data["zero_system"]["detect_poll_interval_ms"]),
            post_click_wait_ms=int(data["zero_system"]["post_click_wait_ms"]),
            success_template_path=data["zero_system"]["success_template_path"],
            success_search_region=SearchRegion(
                left=data["zero_system"]["success_search_region"]["left"],
                top=data["zero_system"]["success_search_region"]["top"],
                width=data["zero_system"]["success_search_region"]["width"],
                height=data["zero_system"]["success_search_region"]["height"],
            ),
            success_match_threshold=float(data["zero_system"]["success_match_threshold"]),
            success_timeout_ms=int(data["zero_system"]["success_timeout_ms"]),
            success_poll_interval_ms=int(data["zero_system"]["success_poll_interval_ms"]),
        ),
    )
