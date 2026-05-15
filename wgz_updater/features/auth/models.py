from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class UserProfile:
    email: str
    name: str
    given_name: str = ""
    picture_url: str = ""

    @property
    def initials(self) -> str:
        if self.given_name:
            return self.given_name[0].upper()
        if self.name:
            return self.name[0].upper()
        if self.email:
            return self.email[0].upper()
        return "?"

    @property
    def display_name(self) -> str:
        return self.given_name or self.name or self.email
