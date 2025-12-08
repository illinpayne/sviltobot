# parser/strategies/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List
from ..core.models import RegionParseResult, ParseConfig

class BaseRegionParser(ABC):

    @abstractmethod
    async def parse(self, session, config: ParseConfig) -> RegionParseResult:
        pass
