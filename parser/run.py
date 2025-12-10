import asyncio

from parser.strategies.odesa import OdesaParser
from parser.strategies.rivne import RivneParser
from parser.strategies.volyn import VolynParser
from parser.core.models import ParseConfig
from parser.scheduler.scheduler import run_periodically

parsers = [
    (
        ParseConfig(
            region_name="Рівненська область",
            url="https://alerts.org.ua/rivnenska-oblast/",
            save_path="data/rivne.json"
        ),
        RivneParser()
    ),
    (
        ParseConfig(
            region_name="Одеська область",
            url="https://alerts.org.ua/odeska-oblast/",
            save_path="data/odesa.json"
        ),
        OdesaParser()
    ),
    (
        ParseConfig(
            region_name="Волинська область",
            url="https://alerts.org.ua/volynska-oblast/",
            save_path="data/volyn.json"
        ),
        VolynParser
    ),
    # (
    #     ParseConfig(
    #         region_name="Тернопільська область",
    #         url="https://www.uz.gov.ua/about/activity/electropostachannia/electro_consumers/temporary_shutdown/grafikiobmezhen/622368/",
    #         save_path="data/ternopil.json"
    #     ),
    #     parser
    # ),
    # (
    #     ParseConfig(
    #         region_name="Вінницька область",
    #         url="https://www.uz.gov.ua/about/activity/electropostachannia/electro_consumers/temporary_shutdown/grafikiobmezhen/622232/",
    #         save_path="data/vinnytsia.json"
    #     ),
    #     parser
    # ),

    # (
    #     ParseConfig(
    #         region_name="Житомирська область",
    #         url="https://www.uz.gov.ua/about/activity/electropostachannia/electro_consumers/temporary_shutdown/grafikiobmezhen/622240/",
    #         save_path="data/zhytomyr.json"
    #     ),
    #     parser
    # ),
    # (
    #     ParseConfig(
    #         region_name="Закарпатська область",
    #         url="https://www.uz.gov.ua/about/activity/electropostachannia/electro_consumers/temporary_shutdown/grafikiobmezhen/622272/",
    #         save_path="data/zakarpattia.json"
    #     ),
    #     parser
    # ),
    # (
    #     ParseConfig(
    #         region_name="Івано-Франківська область",
    #         url="https://www.uz.gov.ua/about/activity/electropostachannia/electro_consumers/temporary_shutdown/grafikiobmezhen/622248/",
    #         save_path="data/ivano-frankivsk.json"
    #     ),
    #     parser
    # ),
    # (
    #     ParseConfig(
    #         region_name="Київська область",
    #         url="https://www.uz.gov.ua/about/activity/electropostachannia/electro_consumers/temporary_shutdown/grafikiobmezhen/622252/",
    #         save_path="data/kyiv.json"
    #     ),
    #     parser
    # ),
    # (
    #     ParseConfig(
    #         region_name="Кіровоградська область",
    #         url="https://www.uz.gov.ua/about/activity/electropostachannia/electro_consumers/temporary_shutdown/grafikiobmezhen/622304/",
    #         save_path="data/kirovohrad.json"
    #     ),
    #     parser
    # ),
    # (
    #     ParseConfig(
    #         region_name="Львівська область",
    #         url="https://www.uz.gov.ua/about/activity/electropostachannia/electro_consumers/temporary_shutdown/grafikiobmezhen/622260/",
    #         save_path="data/lviv.json"
    #     ),
    #     parser
    # ),
    # (
    #     ParseConfig(
    #         region_name="Миколаївська область",
    #         url="https://www.uz.gov.ua/about/activity/electropostachannia/electro_consumers/temporary_shutdown/grafikiobmezhen/622264/",
    #         save_path="data/mykolaiv.json"
    #     ),
    #     parser
    # ),
    # # Полтавська область
    # (
    #     ParseConfig(
    #         region_name="Полтавська область",
    #         url="https://www.uz.gov.ua/about/activity/electropostachannia/electro_consumers/temporary_shutdown/grafikiobmezhen/622276/",
    #         save_path="data/poltava.json"
    #     ),
    #     parser
    # ),
    # # Сумська область
    # (
    #     ParseConfig(
    #         region_name="Сумська область",
    #         url="https://www.uz.gov.ua/about/activity/electropostachannia/electro_consumers/temporary_shutdown/grafikiobmezhen/622280/",
    #         save_path="data/sumy.json"
    #     ),
    #     parser
    # ),
    # # Харківська область
    # (
    #     ParseConfig(
    #         region_name="Харківська область",
    #         url="https://www.uz.gov.ua/about/activity/electropostachannia/electro_consumers/temporary_shutdown/grafikiobmezhen/622284/",
    #         save_path="data/kharkiv.json"
    #     ),
    #     parser
    # ),
    # # Херсонська область
    # (
    #     ParseConfig(
    #         region_name="Херсонська область",
    #         url="https://www.uz.gov.ua/about/activity/electropostachannia/electro_consumers/temporary_shutdown/grafikiobmezhen/622288/",
    #         save_path="data/kherson.json"
    #     ),
    #     parser
    # ),
    # # Хмельницька область
    # (
    #     ParseConfig(
    #         region_name="Хмельницька область",
    #         url="https://www.uz.gov.ua/about/activity/electropostachannia/electro_consumers/temporary_shutdown/grafikiobmezhen/622292/",
    #         save_path="data/khmelnytskyi.json"
    #     ),
    #     parser
    # ),
    # # Черкаська область
    # (
    #     ParseConfig(
    #         region_name="Черкаська область",
    #         url="https://www.uz.gov.ua/about/activity/electropostachannia/electro_consumers/temporary_shutdown/grafikiobmezhen/622296/",
    #         save_path="data/cherkasy.json"
    #     ),
    #     parser
    # ),
    # (
    #     ParseConfig(
    #         region_name="Чернівецька область",
    #         url="https://www.uz.gov.ua/about/activity/electropostachannia/electro_consumers/temporary_shutdown/grafikiobmezhen/622300/",
    #         save_path="data/chernivtsi.json"
    #     ),
    #     parser
    # ),
    # (
    #     ParseConfig(
    #         region_name="Чернігівська область",
    #         url="https://www.uz.gov.ua/about/activity/electropostachannia/electro_consumers/temporary_shutdown/grafikiobmezhen/622304/",
    #         save_path="data/chernihiv.json"
    #     ),
    #     parser
    # ),
]

asyncio.run(run_periodically(parsers))