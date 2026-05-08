from wgz_updater.core.config import AppConfig

_RAW = {
    "updater": {"latest_version": "1.0.0"},
    "game_themes.json": {
        "Elden Ring": {
            "image": "https://example.com/er.jpg",
            "slideshow": ["https://a.com/1.jpg", "https://a.com/2.jpg"],
            "trailer_url": "https://youtube.com/watch?v=abc"
        },
        "Night Reign": "https://example.com/nr.jpg",
    },
    "Mod_1": {
        "name": "Night Reign Mod",
        "game": "Night Reign",
        "version": "v2.0",
        "urls": ["https://drive.google.com/file1"],
        "type": "zip",
        "tag": "HOT",
    },
}


def test_themes_parsed():
    cfg = AppConfig.from_raw(_RAW)
    assert "Elden Ring" in cfg.themes
    theme = cfg.themes["Elden Ring"]
    assert theme.image == "https://example.com/er.jpg"
    assert len(theme.slideshow) == 2
    assert theme.trailer_url == "https://youtube.com/watch?v=abc"


def test_string_theme_becomes_image():
    cfg = AppConfig.from_raw(_RAW)
    assert cfg.themes["Night Reign"].image == "https://example.com/nr.jpg"


def test_games_parsed():
    cfg = AppConfig.from_raw(_RAW)
    assert len(cfg.games) == 1
    assert cfg.games[0].tag == "HOT"
