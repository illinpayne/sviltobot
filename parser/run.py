import asyncio
from parser.scheduler.scheduler import run_periodically
from parser.config.parser_config_loader import load_parsers_from_json

parsers = load_parsers_from_json("config/parsers.json")
asyncio.run(run_periodically(parsers))