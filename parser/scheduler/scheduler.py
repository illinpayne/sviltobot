import asyncio
import aiohttp
from ..core.context import ParseContext
from ..storage.json_writer import save_to_json

async def run_periodically(parsers):
    while True:
        async with aiohttp.ClientSession() as session:
            for config, parser in parsers:
                ctx = ParseContext(parser)
                result = await ctx.execute(session, config)

                save_to_json(result.to_dict(), config.save_path)

        await asyncio.sleep(7200)  # 2 години
