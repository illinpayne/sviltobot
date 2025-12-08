# parser/core/context.py
from .models import ParseConfig
from ..strategies.base import BaseRegionParser

class ParseContext:
    def __init__(self, strategy: BaseRegionParser):
        self.strategy = strategy

    async def execute(self, session, config: ParseConfig):
        return await self.strategy.parse(session, config)
