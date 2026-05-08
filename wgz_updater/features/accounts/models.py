from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AccountRecord:
    service: str
    username: str
    password: str = ""
    note: str = ""

    def to_row(self) -> list[str]:
        return [self.service, self.username, self.password, self.note]

    @classmethod
    def from_row(cls, row: list[str]) -> "AccountRecord":
        padded = list(row) + [""] * (4 - len(row))
        return cls(service=padded[0], username=padded[1], password=padded[2], note=padded[3])


@dataclass
class ServiceEntry:
    key: str
    label: str
    trailer_url: str = ""
    riot_window_titles: list[str] = field(default_factory=list)
