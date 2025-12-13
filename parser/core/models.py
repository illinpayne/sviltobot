from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class ParseConfig:
    url: str                    # URL парсингу
    save_path: str              # куди писати JSON

@dataclass
class RegionParseResult:
    date: str
    queues: Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self):
        return {
            self.date: self.queues
        }