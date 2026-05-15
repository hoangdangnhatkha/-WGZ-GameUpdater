from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AccountRecord:
    service: str
    username: str
    password: str = ""
    nickname: str = ""
    game: str = ""
    note: str = ""

    def to_row(self) -> list[str]:
        return [self.service, self.username, self.password, self.nickname, self.game, self.note]

    @classmethod
    def from_row(cls, row: list[str]) -> "AccountRecord":
        padded = list(row) + [""] * (6 - len(row))
        return cls(
            service=padded[0], username=padded[1], password=padded[2],
            nickname=padded[3], game=padded[4], note=padded[5],
        )

    def to_json(self) -> dict:
        return {
            "nickname": self.nickname,
            "username": self.username,
            "password": self.password,
            "type": self.service.lower(),
            "game": self.game,
        }

    @classmethod
    def from_json(cls, service: str, data: dict) -> "AccountRecord":
        return cls(
            service=service,
            username=data.get("username", ""),
            password=data.get("password", ""),
            nickname=data.get("nickname", ""),
            game=data.get("game", ""),
        )

