from dataclasses import dataclass
from typing import List, Dict


@dataclass
class ParseConfig:
    region_name: str
    url: str
    save_path: str


@dataclass
class HourSlot:
    start: str
    end: str
    queues: List[str]


@dataclass
class AddressRecord:
    queue: str
    address: str

    def to_dict(self):
        return {
            "queue": self.queue,
            "address": self.address
        }


@dataclass
class RegionParseResult:
    region: str
    date: str
    hours: List[HourSlot]
    addresses: List[AddressRecord]

    def to_dict(self):
        # 1. Створюємо словник для групування: { "Номер черги": ["час1", "час2"] }
        schedule_by_queue: Dict[str, List[str]] = {}

        for slot in self.hours:
            # Формуємо рядок часу, наприклад "14:00 - 18:00"
            # Якщо start/end пусті (якщо сайт не віддав час), ставимо заглушку або ігноруємо
            time_range = f"{slot.start} - {slot.end}"
            if not slot.start or not slot.end:
                time_range = "Час не визначено"

            for q in slot.queues:
                # Очищаємо назву черги від зайвих пробілів
                q_clean = q.strip()
                if q_clean not in schedule_by_queue:
                    schedule_by_queue[q_clean] = []

                # Додаємо час у список цієї черги
                schedule_by_queue[q_clean].append(time_range)

        # 2. Повертаємо структуру: { "DD.MM.YYYY": { "1": [...], "2": [...] } }
        # Важливо: дату краще форматувати як у вашому прикладі (DD.MM.YYYY)
        return {
            self.date: schedule_by_queue
        }