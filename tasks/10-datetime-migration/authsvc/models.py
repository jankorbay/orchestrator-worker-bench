from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class User:
    id: int
    email: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login: datetime | None = None

    def login(self) -> None:
        self.last_login = datetime.utcnow()

    def account_age_days(self) -> int:
        return (datetime.utcnow() - self.created_at).days
