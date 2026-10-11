from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class User:
    id: int
    email: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: datetime | None = None

    def login(self) -> None:
        self.last_login = datetime.now(timezone.utc)

    def account_age_days(self) -> int:
        return (datetime.now(timezone.utc) - self.created_at).days
