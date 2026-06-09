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
class CodexFlowConfig:
    button_template_path: str
    button_search_region: SearchRegion
    button_match_threshold: float
    button_search_step: int
    post_click_wait_ms: int
    page_template_path: str
    page_search_region: SearchRegion
    page_match_threshold: float
    page_timeout_ms: int
    page_poll_interval_ms: int
    first_codex_template_path: str
    first_codex_search_region: SearchRegion
    first_codex_match_threshold: float
    first_codex_search_step: int
    enter_button_template_path: str
    enter_button_search_region: SearchRegion
    enter_button_match_threshold: float
    enter_button_search_step: int


@dataclass
class TeamSetupConfig:
    page_template_path: str
    page_search_region: SearchRegion
    page_match_threshold: float
    page_timeout_ms: int
    page_poll_interval_ms: int
    enter_button_template_path: str
    enter_button_search_region: SearchRegion
    enter_button_match_threshold: float
    enter_button_search_step: int
    post_click_wait_ms: int
    transition_timeout_ms: int
    transition_poll_interval_ms: int


@dataclass
class AppConfig:
    name: str
    environment: str
    game_window: GameWindowConfig
    logging: LoggingConfig
    input_validation: InputValidationConfig
    zero_system: ZeroSystemConfig
    codex_flow: CodexFlowConfig
    team_setup: TeamSetupConfig


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
        codex_flow=CodexFlowConfig(
            button_template_path=data["codex_flow"]["button_template_path"],
            button_search_region=SearchRegion(
                left=data["codex_flow"]["button_search_region"]["left"],
                top=data["codex_flow"]["button_search_region"]["top"],
                width=data["codex_flow"]["button_search_region"]["width"],
                height=data["codex_flow"]["button_search_region"]["height"],
            ),
            button_match_threshold=float(data["codex_flow"]["button_match_threshold"]),
            button_search_step=int(data["codex_flow"]["button_search_step"]),
            post_click_wait_ms=int(data["codex_flow"]["post_click_wait_ms"]),
            page_template_path=data["codex_flow"]["page_template_path"],
            page_search_region=SearchRegion(
                left=data["codex_flow"]["page_search_region"]["left"],
                top=data["codex_flow"]["page_search_region"]["top"],
                width=data["codex_flow"]["page_search_region"]["width"],
                height=data["codex_flow"]["page_search_region"]["height"],
            ),
            page_match_threshold=float(data["codex_flow"]["page_match_threshold"]),
            page_timeout_ms=int(data["codex_flow"]["page_timeout_ms"]),
            page_poll_interval_ms=int(data["codex_flow"]["page_poll_interval_ms"]),
            first_codex_template_path=data["codex_flow"]["first_codex_template_path"],
            first_codex_search_region=SearchRegion(
                left=data["codex_flow"]["first_codex_search_region"]["left"],
                top=data["codex_flow"]["first_codex_search_region"]["top"],
                width=data["codex_flow"]["first_codex_search_region"]["width"],
                height=data["codex_flow"]["first_codex_search_region"]["height"],
            ),
            first_codex_match_threshold=float(data["codex_flow"]["first_codex_match_threshold"]),
            first_codex_search_step=int(data["codex_flow"]["first_codex_search_step"]),
            enter_button_template_path=data["codex_flow"]["enter_button_template_path"],
            enter_button_search_region=SearchRegion(
                left=data["codex_flow"]["enter_button_search_region"]["left"],
                top=data["codex_flow"]["enter_button_search_region"]["top"],
                width=data["codex_flow"]["enter_button_search_region"]["width"],
                height=data["codex_flow"]["enter_button_search_region"]["height"],
            ),
            enter_button_match_threshold=float(data["codex_flow"]["enter_button_match_threshold"]),
            enter_button_search_step=int(data["codex_flow"]["enter_button_search_step"]),
        ),
        team_setup=TeamSetupConfig(
            page_template_path=data["team_setup"]["page_template_path"],
            page_search_region=SearchRegion(
                left=data["team_setup"]["page_search_region"]["left"],
                top=data["team_setup"]["page_search_region"]["top"],
                width=data["team_setup"]["page_search_region"]["width"],
                height=data["team_setup"]["page_search_region"]["height"],
            ),
            page_match_threshold=float(data["team_setup"]["page_match_threshold"]),
            page_timeout_ms=int(data["team_setup"]["page_timeout_ms"]),
            page_poll_interval_ms=int(data["team_setup"]["page_poll_interval_ms"]),
            enter_button_template_path=data["team_setup"]["enter_button_template_path"],
            enter_button_search_region=SearchRegion(
                left=data["team_setup"]["enter_button_search_region"]["left"],
                top=data["team_setup"]["enter_button_search_region"]["top"],
                width=data["team_setup"]["enter_button_search_region"]["width"],
                height=data["team_setup"]["enter_button_search_region"]["height"],
            ),
            enter_button_match_threshold=float(data["team_setup"]["enter_button_match_threshold"]),
            enter_button_search_step=int(data["team_setup"]["enter_button_search_step"]),
            post_click_wait_ms=int(data["team_setup"]["post_click_wait_ms"]),
            transition_timeout_ms=int(data["team_setup"]["transition_timeout_ms"]),
            transition_poll_interval_ms=int(data["team_setup"]["transition_poll_interval_ms"]),
        ),
    )
