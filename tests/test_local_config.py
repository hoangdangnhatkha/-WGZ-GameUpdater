import json
from pathlib import Path
import pytest


def test_local_config_load_save(monkeypatch, tmp_path):
    import wgz_updater.core.local_config as lc_mod
    lc_mod._SETTINGS_FILE = tmp_path / "settings.json"
    lc_mod._instance = None  # reset singleton

    from wgz_updater.core.local_config import LocalConfig
    cfg = LocalConfig()
    cfg.load()  # file doesn't exist yet — should not raise
    cfg.set_game_path("game1", "D:/Games/game1")
    cfg.last_used_folder = "D:/Games"
    cfg.save()

    # Re-create singleton and reload
    lc_mod._instance = None
    cfg2 = LocalConfig()
    cfg2.load()
    assert cfg2.get_game_path("game1") == "D:/Games/game1"
    assert cfg2.last_used_folder == "D:/Games"
