from pathlib import Path

from czn_automation.config import load_config


def test_load_config() -> None:
    root_dir = Path(__file__).resolve().parents[1]
    config = load_config(root_dir / "config" / "app.example.json")

    assert config.name == "czn-automation"
    assert config.game_window.title_keywords
    assert config.game_window.supported_resolutions[0].width == 1600
