import re
from .common_parser import CommonRegionParser

class BaseParser(CommonRegionParser):
    def extract_queue_id(self, group_name: str) -> str:
        match = re.search(r'(\d+\.\d+)', group_name)
        return match.group(1) if match else None

    def map_queue_id(self, queue_id: str, time_range: str, queues_data: dict):
        if queue_id in queues_data:
            queues_data[queue_id].append(time_range)


class ChernivtsiParser(CommonRegionParser):
    def extract_queue_id(self, group_name: str) -> str:
        match = re.search(r'Група\s+(\d+)', group_name)
        return match.group(1) if match else None

    def map_queue_id(self, queue_id: str, time_range: str, queues_data: dict):
        queue_num = int(queue_id)
        if 1 <= queue_num <= 6:
            queues_data[f"{queue_num}.1"].append(time_range)
            queues_data[f"{queue_num}.2"].append(time_range)

