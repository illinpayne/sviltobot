from .models import User, Subscription
from .json_provider import JSONProvider
from datetime import datetime
from typing import Optional


class DatabaseService:
    def __init__(self, data_path: str = "data"):
        self.provider = JSONProvider(data_path)
        self.users_file = "users"
        self._users_cache = self._load_users()

    def _load_users(self) -> dict:
        raw_data = self.provider.load(self.users_file)
        users: dict[int, User] = {}

        for uid_str, user_dict in raw_data.items():
            subs = {}

            for sub_name, sub_data in user_dict.get("subscriptions", {}).items():
                subs[sub_name] = Subscription(oblast=sub_data["oblast"], queue_number=sub_data["queue_number"],
                                              name=sub_data["name"])

            created_at_str = user_dict.get("created_at")
            if created_at_str:
                created_at_obj = datetime.fromisoformat(created_at_str)
            else:
                created_at_obj = datetime.now()

            user = User(telegram_id=user_dict["telegram_id"], first_name=user_dict["first_name"],
                        last_name=user_dict.get("last_name"), username=user_dict.get("username"),
                        subscriptions=subs, created_at=created_at_obj)

            users[int(uid_str)] = user

        return users

    def _save_all(self):
        data_to_save = {}

        for uid, user in self._users_cache.items():
            subs_dict = {}

            for sub in user.subscriptions.values():
                subs_dict[sub.name] = {
                    "oblast": sub.oblast,
                    "queue_number": sub.queue_number,
                    "name": sub.name
                }

            user_dict = {
                "telegram_id": user.telegram_id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
                "subscriptions": subs_dict,
                "created_at": user.created_at.isoformat()
            }

            data_to_save[str(uid)] = user_dict

        self.provider.save(self.users_file, data_to_save)

    def get_user(self, user_id: int) -> Optional[User]:
        return self._users_cache.get(user_id)

    def register_user(self, telegram_id: int, first_name: str, last_name: Optional[str], username: Optional[str]):
        user = self.get_user(telegram_id)

        if user:
            return user
        else:
            user = User(telegram_id=telegram_id, first_name=first_name, last_name=last_name, username=username)

            self._users_cache[telegram_id] = user
            self._save_all()

            return user

    def add_subscription(self, telegram_id: int, oblast: str, queue: str, name: str) -> bool:
        user = self.get_user(telegram_id)

        if user:
            user.subscriptions[name] = Subscription(oblast=oblast, queue_number=queue, name=name)
            self._save_all()
            return True
        else:
            return False
