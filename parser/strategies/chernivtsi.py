import re
from bs4 import BeautifulSoup
from datetime import datetime
from ..core.models import RegionParseResult, ParseConfig
from .base import BaseRegionParser


class ChernivtsiParser(BaseRegionParser):

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

    async def parse(self, session, config: ParseConfig) -> RegionParseResult:
        async with session.get(config.url) as resp:
            html = await resp.text()

        soup = BeautifulSoup(html, "html.parser")

        queues_data = {}

        for i in range(1, 13):
            queues_data[f"{i}.1"] = []
            queues_data[f"{i}.2"] = []

        groups = soup.find_all("div", class_="group")

        for group in groups:
            name_tag = group.find("b", class_="name")
            if not name_tag:
                continue

            group_name = name_tag.get_text(strip=True)
            match = re.search(r'Група\s+(\d+)', group_name)
            if not match:
                continue

            queue_id = match.group(1)
            time_divs = group.find_all("div")

            for div in time_divs:
                off_tag = div.find("b", class_="off")
                maybe_tag = div.find("b", class_="maybe")

                if off_tag or maybe_tag:
                    time_text = div.get_text(strip=True)
                    time_text = time_text.replace("OFF", "").replace("?", "").strip()

                    time_match = re.search(r'(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})', time_text)
                    if time_match:
                        start = self.normalize_time(time_match.group(1))
                        end = self.normalize_time(time_match.group(2))
                        time_range = f"{start} - {end}"

                        for subgroup in (f"{queue_id}.1", f"{queue_id}.2"):
                            if subgroup in queues_data:
                                queues_data[subgroup].append(time_range)

        for queue in queues_data:
            queues_data[queue] = self.merge_time_ranges(queues_data[queue])

        current_date = datetime.now().strftime("%d.%m.%Y")

        return RegionParseResult(
            date=current_date,
            queues=queues_data
        )