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


@dataclass
class AppConfig:
    name: str
    environment: str
    game_window: GameWindowConfig
    logging: LoggingConfig
    input_validation: InputValidationConfig


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
        ),
    )
