# parser/run.py
import asyncio
from parser_new.strategies.rivne import RivneParser
from parser_new.core.models import ParseConfig
from parser_new.scheduler.scheduler import run_periodically

parsers = [
    (
        ParseConfig(
            region_name="Рівненська область",
            url="https://www.uz.gov.ua/about/activity/electropostachannia/electro_consumers/temporary_shutdown/grafikiobmezhen/622352/",
            save_path="data/rivne.json"
        ),
        RivneParser()
    ),
    # додати аналогічно інші області:
]

asyncio.run(run_periodically(parsers))
