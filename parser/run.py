import asyncio
from parser.core.models import ParseConfig
from parser.scheduler.scheduler import run_periodically
from parser.strategies import (
    ZaporizhzhiaParser,
    DniproParser,
    CherkasyParser,
    KharkivParser,
    SumyParser,
    PoltavaParser,
    ChernihivParser,
    MykolaivParser,
    KirovohradParser,
    KyivCityParser,
    KyivOblParser,
    VinnytsiaParser,
    TernopilParser,
    ChernivtsiParser,
    ZhytomyrParser,
    KhmelnytskyiParser,
    IvanoFrankivskParser,
    ZakarpattiaParser,
    LvivParser,
    OdesaParser,
    RivneParser,
    VolynParser
)

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
        VolynParser()
    ),
    (
        ParseConfig(
            region_name="Запорізька область",
            url="https://alerts.org.ua/zaporizka-oblast/",
            save_path="data/zaporizhzhia.json"
        ),
        ZaporizhzhiaParser()
    ),
    (
        ParseConfig(
            region_name="Дніпропетровська область",
            url="https://alerts.org.ua/dnipropetrovska-oblast/",
            save_path="data/dnipro.json"
        ),
        DniproParser()
    ),
    (
        ParseConfig(
            region_name="Тернопільська область",
            url="https://alerts.org.ua/ternopilska-oblast/",
            save_path="data/ternopil.json"
        ),
        TernopilParser()
    ),
    (
        ParseConfig(
            region_name="Вінницька область",
            url="https://alerts.org.ua/vinnytcka-oblast/",
            save_path="data/vinnytsia.json"
        ),
        VinnytsiaParser()
    ),
    (
        ParseConfig(
            region_name="Житомирська область",
            url="https://alerts.org.ua/zhytomyrska-oblast/",
            save_path="data/zhytomyr.json"
        ),
        ZhytomyrParser()
    ),
    (
        ParseConfig(
            region_name="Закарпатська область",
            url="https://alerts.org.ua/zakarpatska-oblast/",
            save_path="data/zakarpattia.json"
        ),
        ZakarpattiaParser()
    ),
    (
        ParseConfig(
            region_name="Івано-Франківська область",
            url="https://alerts.org.ua/ivano-frankivska-oblast/",
            save_path="data/ivano-frankivsk.json"
        ),
        IvanoFrankivskParser()
    ),
    (
        ParseConfig(
            region_name="Київська область",
            url="https://alerts.org.ua/kyivska-oblast/",
            save_path="data/kyivobl.json"
        ),
        KyivOblParser()
    ),
(
        ParseConfig(
            region_name="місто Київ",
            url="https://alerts.org.ua/kyiv/",
            save_path="data/kyivcity.json"
        ),
        KyivCityParser()
    ),
    (
        ParseConfig(
            region_name="Кіровоградська область",
            url="https://alerts.org.ua/kirovogradska-oblast/",
            save_path="data/kirovohrad.json"
        ),
        KirovohradParser()
    ),
    (
        ParseConfig(
            region_name="Львівська область",
            url="https://alerts.org.ua/lvivska-oblast/",
            save_path="data/lviv.json"
        ),
        LvivParser()
    ),
    (
        ParseConfig(
            region_name="Миколаївська область",
            url="https://alerts.org.ua/mykolaivska-oblast/",
            save_path="data/mykolaiv.json"
        ),
        MykolaivParser()
    ),
    (
        ParseConfig(
            region_name="Полтавська область",
            url="https://alerts.org.ua/poltavska-oblast/",
            save_path="data/poltava.json"
        ),
        PoltavaParser()
    ),
    (
        ParseConfig(
            region_name="Сумська область",
            url="https://alerts.org.ua/sumska-oblast/",
            save_path="data/sumy.json"
        ),
        SumyParser()
    ),
    (
        ParseConfig(
            region_name="Харківська область",
            url="https://alerts.org.ua/harkivska-oblast/",
            save_path="data/kharkiv.json"
        ),
        KharkivParser()
    ),
    (
        ParseConfig(
            region_name="Хмельницька область",
            url="https://alerts.org.ua/hmelnitcka-oblast/",
            save_path="data/khmelnytskyi.json"
        ),
        KhmelnytskyiParser()
    ),
    (
        ParseConfig(
            region_name="Черкаська область",
            url="https://alerts.org.ua/cherkaska-oblast/",
            save_path="data/cherkasy.json"
        ),
        CherkasyParser()
    ),    (
        ParseConfig(
            region_name="Чернівецька область",
            url="https://alerts.org.ua/chernivetcka-oblast/",
            save_path="data/chernivtsi.json"
        ),
        ChernivtsiParser()
    ),
    (
        ParseConfig(
            region_name="Чернігівська область",
            url="https://alerts.org.ua/chernigivska-oblast/",
            save_path="data/chernihiv.json"
        ),
        ChernihivParser()
    ),
]

asyncio.run(run_periodically(parsers))