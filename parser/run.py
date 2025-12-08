import asyncio

from parser.strategies.odesa import OdesaParser
from parser.strategies.rivne import RivneParser
from parser.core.models import ParseConfig
from parser.scheduler.scheduler import run_periodically

parsers = [
    (
        ParseConfig(
            region_name="Рівненська область",
            url="https://www.uz.gov.ua/about/activity/electropostachannia/electro_consumers/temporary_shutdown/grafikiobmezhen/622352/",
            save_path="data/rivne.json"
        ),
        RivneParser()
    ),
# (
#         ParseConfig(
#             region_name="Одеська область",
#             url="https://www.uz.gov.ua/about/activity/electropostachannia/electro_consumers/temporary_shutdown/grafikiobmezhen/622336/",
#             save_path="data/odesa.json"
#         ),
#         OdesaParser()
#     ),
    #аналогічно інші області
]

asyncio.run(run_periodically(parsers))
