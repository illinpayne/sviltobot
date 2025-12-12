import json
from parser.core.models import ParseConfig
from parser.strategies import BaseParser, ChernivtsiParser

PARSER_MAP = {
    "BaseParser": BaseParser,
    "ChernivtsiParser": ChernivtsiParser
}

def load_parsers_from_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = []

    for item in data["parsers"]:
        parser_cls = PARSER_MAP[item["parser"]]
        parser_instance = parser_cls()

        config = ParseConfig(
            url=item["url"],
            save_path=item["save_path"]
        )

        result.append((config, parser_instance))
    return result
