import re
from bs4 import BeautifulSoup
from datetime import datetime
from ..core.models import RegionParseResult, ParseConfig
from .base import BaseRegionParser


class RivneParser(BaseRegionParser):

    def parse_queue_string(self, queue_str: str) -> list:

        # Парсить рядок типу "2(1,2)" або "5(1,2)" в список ["2.1", "2.2"]
        # Також обробляє "4(2)" -> ["4.2"], "2(1)" -> ["2.1"]

        match = re.match(r'(\d+)\(([0-9,]+)\)', queue_str)
        if match:
            main_queue = match.group(1)
            sub_queues = match.group(2).split(',')
            return [f"{main_queue}.{sub.strip()}" for sub in sub_queues]
        return []

    def merge_time_ranges(self, time_ranges: list) -> list:

        # Об'єднує послідовні часові діапазони.
        # ["00-00 - 02-00", "02-00 - 05-00"] -> ["00-00 - 05-00"]
        #
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

        queues_data = {
            "1.1": [], "1.2": [],
            "2.1": [], "2.2": [],
            "3.1": [], "3.2": [],
            "4.1": [], "4.2": [],
            "5.1": [], "5.2": [],
            "6.1": [], "6.2": []
        }

        hours_table = soup.find_all("table")[0]
        rows = hours_table.find_all("tr")

        time_row = rows[0].find_all("td")[1:]
        queue_row = rows[1].find_all("td")[1:]

        for time_cell, queue_cell in zip(time_row, queue_row):
            time_paragraphs = time_cell.find_all("p")
            times = [p.get_text(strip=True) for p in time_paragraphs if p.get_text(strip=True)]

            if len(times) >= 2:
                start = times[0]
                end = times[1]
            elif len(times) == 1:
                parts = times[0].split()
                if len(parts) >= 2:
                    start = parts[0]
                    end = parts[1]
                else:
                    start = end = times[0]
            else:
                continue

            time_range = f"{start} - {end}"

            queue_paragraphs = queue_cell.find_all("p")
            queue_strings = [p.get_text(strip=True) for p in queue_paragraphs if p.get_text(strip=True)]

            for queue_str in queue_strings:
                parsed_queues = self.parse_queue_string(queue_str)
                for queue in parsed_queues:
                    if queue in queues_data:
                        queues_data[queue].append(time_range)


        for queue in queues_data:
            queues_data[queue] = self.merge_time_ranges(queues_data[queue])


        current_date = datetime.now().strftime("%d.%m.%Y")

        return RegionParseResult(
            date=current_date,
            queues=queues_data
        )