# parser/strategies/rivne.py
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
from ..core.models import RegionParseResult, HourSlot, ParseConfig
from .base import BaseRegionParser


class RivneParser(BaseRegionParser):

    async def parse(self, session, config: ParseConfig) -> RegionParseResult:
        async with session.get(config.url) as resp:
            # Варто перевірити кодування, іноді укр сайти це win-1251, але uz.gov.ua зазвичай utf-8
            html = await resp.text()

        soup = BeautifulSoup(html, "html.parser")

        # --- Таблиця годин відключення ---
        # Знаходимо першу таблицю
        tables = soup.find_all("table")
        if not tables:
            print(f"Warning: No tables found for {config.region_name}")
            return RegionParseResult(config.region_name, datetime.now().strftime("%d.%m.%Y"), [], [])

        hours_table = tables[0]
        rows = hours_table.find_all("tr")

        # Пропускаємо заголовки, якщо вони є. Зазвичай перший рядок - час, другий - черги
        # Треба переконатися, що структура саме така.
        # У RIVNEOBLENERGO часто структура складна. Припустимо, що ваш код був близький до правди:

        if len(rows) < 2:
            return RegionParseResult(config.region_name, datetime.now().strftime("%d.%m.%Y"), [], [])

        time_row = rows[0].find_all("td")[1:]  # [1:] пропускає першу клітинку (назву рядка)
        queue_row = rows[1].find_all("td")[1:]

        hour_slots = []

        # Використовуємо zip, щоб іти по колонкам
        for time_cell, queue_cell in zip(time_row, queue_row):
            # --- ВИПРАВЛЕННЯ ЧАСУ ---
            # get_text(separator="|", strip=True) з'єднає рядки через роздільник,
            # це надійніше ніж split("\n")
            time_text = time_cell.get_text("|", strip=True)

            # Спробуємо розбити "16:00|20:00" або "16:00-20:00"
            if "|" in time_text:
                parts = time_text.split("|")
                start, end = parts[0], parts[-1]
            elif "-" in time_text:
                parts = time_text.split("-")
                start, end = parts[0], parts[-1]
            else:
                # Якщо час вказаний одним числом або якось інакше
                start = end = time_text

            # --- Парсинг черг ---
            # Розбиваємо по комі, новому рядку або інших роздільниках
            raw_queues = queue_cell.get_text("\n", strip=True).split("\n")
            queues = [q.strip() for q in raw_queues if q.strip()]

            hour_slots.append(HourSlot(start=start, end=end, queues=queues))

        # Форматуємо дату як у вашому прикладі: "04.12.2025"
        current_date = datetime.now().strftime("%d.%m.%Y")

        return RegionParseResult(
            region=config.region_name,
            date=current_date,
            hours=hour_slots,
            addresses=[]
        )