from wgz_updater.features.accounts.models import AccountRecord


def test_to_json():
    rec = AccountRecord(
        service="Steam", username="user1", password="pass1",
        nickname="My Steam", game="Elden Ring"
    )
    d = rec.to_json()
    assert d["nickname"] == "My Steam"
    assert d["username"] == "user1"
    assert d["game"] == "Elden Ring"
    assert d["type"] == "steam"


def test_from_json():
    rec = AccountRecord.from_json("Riot", {
        "nickname": "Riot Main",
        "username": "riotuser",
        "password": "riotpass",
        "type": "riot",
        "game": "Valorant",
    })
    assert rec.service == "Riot"
    assert rec.nickname == "Riot Main"
    assert rec.game == "Valorant"
