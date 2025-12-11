from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Subscription:
    oblast: str
    queue_number: str
    name: str

    notifications_enabled: bool = True
    reminder_offsets: list[int] = field(default_factory=list)

@dataclass
class User:
    telegram_id: int
    first_name: str

    last_name: Optional[str] = None
    username: Optional[str] = None

    subscriptions: list[Subscription] = field(default_factory=list)

    created_at: datetime = field(default_factory=datetime.now)
