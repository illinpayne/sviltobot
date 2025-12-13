import datetime
import json
import sqlite3

from database.models import User, Subscription
from database.providers.sqlite_provider import SQLiteProvider


class UserRepository:
    def __init__(self):
        self.provider = SQLiteProvider("data")

        self._create_tables()

    def _create_tables(self):
        with self.provider.connect() as conn:
            conn.executescript("""
                               CREATE TABLE IF NOT EXISTS users
                               (
                                   telegram_id INTEGER PRIMARY KEY,
                                   first_name  TEXT NOT NULL,
                                   last_name   TEXT,
                                   username    TEXT,
                                   created_at  TEXT NOT NULL
                               );
                               CREATE TABLE IF NOT EXISTS subscriptions
                               (
                                   id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                                   user_id               INTEGER NOT NULL,
                                   oblast                TEXT    NOT NULL,
                                   queue_number          TEXT    NOT NULL,
                                   name                  TEXT    NOT NULL,
                                   notifications_enabled INTEGER DEFAULT 1,
                                   reminder_offsets      TEXT    DEFAULT '[]',
                                   FOREIGN KEY (user_id) REFERENCES users (telegram_id) ON DELETE CASCADE,
                                   UNIQUE (user_id, name)
                               );
                               """)

    def register_user(self, user: User) -> bool:
        with self.provider.connect() as conn:
            try:
                conn.execute("""
                             INSERT INTO users (telegram_id, first_name, last_name, username, created_at)
                             VALUES (?, ?, ?, ?, ?)
                             """, (user.telegram_id,
                                   user.first_name,
                                   user.last_name,
                                   user.username,
                                   user.created_at.isoformat()))
                return True
            except sqlite3.IntegrityError:
                return False

    def get_user(self, telegram_id: int) -> User | None:
        with self.provider.connect() as conn:
            cursor = conn.execute("""SELECT *
                                     FROM users
                                     WHERE telegram_id = ?""", (telegram_id,))
            user = cursor.fetchone()

            if not user:
                return None

            cursor = conn.execute("""SELECT *
                                     FROM subscriptions
                                     WHERE user_id = ?""", (telegram_id,))
            subs = cursor.fetchall()

            subscriptions_list = []
            for sub in subs:
                subscriptions_list.append(Subscription(
                    oblast=sub["oblast"],
                    queue_number=sub["queue_number"],
                    name=sub["name"],
                    notifications_enabled=bool(sub["notifications_enabled"]),
                    reminder_offsets=json.loads(sub["reminder_offsets"]),
                ))

            return User(
                telegram_id=user["telegram_id"],
                first_name=user["first_name"],
                last_name=user["last_name"],
                username=user["username"],
                subscriptions=subscriptions_list,
                created_at=datetime.datetime.fromisoformat(user["created_at"]),
            )

    def update_user(self, telegram_id: int, user: User) -> bool:
        with self.provider.connect() as conn:
            try:
                cursor = conn.execute("""
                                      UPDATE users
                                      SET first_name = ?,
                                          last_name  = ?,
                                          username   = ?
                                      WHERE telegram_id = ?
                                      """, (user.first_name, user.last_name, user.username, telegram_id))
                return cursor.rowcount > 0
            except sqlite3.IntegrityError:
                return False

    def delete_user(self, telegram_id: int) -> bool:
        with self.provider.connect() as conn:
            cursor = conn.execute("""DELETE
                            FROM users
                            WHERE telegram_id = ?""", (telegram_id,))
            return cursor.rowcount > 0

    def add_subscription(self, telegram_id: int, subscription: Subscription) -> bool:
        with self.provider.connect() as conn:
            try:
                conn.execute("""
                             INSERT INTO subscriptions (user_id, oblast, queue_number, name,
                                                        notifications_enabled, reminder_offsets)
                             VALUES (?, ?, ?, ?, ?, ?)
                             """, (telegram_id, subscription.oblast, subscription.queue_number, subscription.name,
                                   int(subscription.notifications_enabled), json.dumps(subscription.reminder_offsets)))
                return True
            except sqlite3.IntegrityError:
                return False

    def update_subscription(self, telegram_id: int, name: str, subscription: Subscription) -> bool:
        with self.provider.connect() as conn:
            try:
                cursor = conn.execute("""
                             UPDATE subscriptions
                             SET oblast                = ?,
                                 queue_number          = ?,
                                 name                  = ?,
                                 notifications_enabled = ?,
                                 reminder_offsets      = ?
                             WHERE user_id = ?
                               AND name = ?
                             """, (subscription.oblast, subscription.queue_number, subscription.name,
                                   subscription.notifications_enabled, json.dumps(subscription.reminder_offsets),
                                   telegram_id, name))
                return cursor.rowcount > 0
            except sqlite3.IntegrityError:
                return False

    def delete_subscription(self, telegram_id: int, name: str) -> bool:
        with self.provider.connect() as conn:
            cursor = conn.execute("""
                         DELETE
                         FROM subscriptions
                         WHERE user_id = ?
                           AND name = ? """, (telegram_id, name))
            return cursor.rowcount > 0
