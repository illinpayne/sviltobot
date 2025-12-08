
from abc import ABC, abstractmethod
from ..core.models import RegionParseResult, ParseConfig

class BaseRegionParser(ABC):

    @abstractmethod
    async def parse(self, session, config: ParseConfig) -> RegionParseResult:
        pass
