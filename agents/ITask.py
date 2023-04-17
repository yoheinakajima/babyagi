from typing import NamedTuple


class Task(NamedTuple):
    id: int
    description: str = ""
    result: str = ""