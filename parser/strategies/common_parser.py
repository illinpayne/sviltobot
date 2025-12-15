import re
from bs4 import BeautifulSoup
from datetime import datetime
from abc import abstractmethod
from ..core.models import RegionParseResult, ParseConfig
from .base import BaseRegionParser


class CommonRegionParser(BaseRegionParser):
    def normalize_time(self, time_str: str) -> str:
        return time_str.replace(':', '-')

    def merge_time_ranges(self, time_ranges: list) -> list:
        if not time_ranges:
            return []

        sorted_ranges = sorted(time_ranges, key=lambda x: x.split(" - ")[0])
        merged = []
        current_start, current_end = sorted_ranges[0].split(" - ")

        for time_range in sorted_ranges[1:]:
            start, end = time_range.split(" - ")
            if current_end == start:
                current_end = end
            else:
                merged.append(f"{current_start} - {current_end}")
                current_start, current_end = start, end

        merged.append(f"{current_start} - {current_end}")
        return merged

    def init_queues_data(self) -> dict:
        return {
            f"{i}.{j}": [] for i in range(1, 7) for j in (1, 2)
        }

    @abstractmethod
    def extract_queue_id(self, group_name: str) -> str:
        pass

    @abstractmethod
    def map_queue_id(self, queue_id: str, time_range: str, queues_data: dict):
        pass

    async def parse(self, session, config: ParseConfig) -> RegionParseResult:
        async with session.get(config.url) as resp:
            html = await resp.text()

        soup = BeautifulSoup(html, "html.parser")
        queues_data = self.init_queues_data()

        groups = soup.find_all("div", class_="group")

        for group in groups:
            # Виправлено: шукаємо по правильному класу
            name_tag = group.find("b", class_="group-name")
            if not name_tag:
                continue

            group_name = name_tag.get_text(strip=True)
            queue_id = self.extract_queue_id(group_name)

            if not queue_id:
                continue

            # Шукаємо період всередині групи
            period_div = group.find("div", class_="period")
            if not period_div:
                continue

            # Знаходимо всі div з data-start і data-end
            time_divs = period_div.find_all("div", attrs={"data-start": True, "data-end": True})

            for div in time_divs:
                # Перевіряємо чи є OFF статус (class="stts2" або <b class="off">)
                off_tag = div.find("b", class_="off")
                maybe_tag = div.find("b", class_="maybe")
                has_off_class = "stts2" in div.get("class", [])

                if off_tag or maybe_tag or has_off_class:
                    # Отримуємо час з атрибутів
                    start_time = div.get("data-start")
                    end_time = div.get("data-end")

                    if start_time and end_time:
                        start = self.normalize_time(start_time)
                        end = self.normalize_time(end_time)
                        time_range = f"{start} - {end}"
                        self.map_queue_id(queue_id, time_range, queues_data)

        # Об'єднуємо діапазони для кожної черги
        for queue in queues_data:
            queues_data[queue] = self.merge_time_ranges(queues_data[queue])

        current_date = datetime.now().strftime("%d.%m.%Y")
        print(queues_data)

        return RegionParseResult(
            date=current_date,
            queues=queues_data
        )
