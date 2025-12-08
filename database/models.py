from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Subscription:
    oblast: str
    queue_number: str
    name: str


@dataclass
class User:
    telegram_id: int
    first_name: str

    last_name: Optional[str] = None
    username: Optional[str] = None

    subscriptions: dict[str, Subscription] = field(default_factory=dict)

    created_at: datetime = field(default_factory=datetime.now)
