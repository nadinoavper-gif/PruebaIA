from __future__ import annotations

from dataclasses import dataclass, asdict
import json
from pathlib import Path


@dataclass
class Experience:
    state_id: str
    signal: str
    confidence: float
    reward: float
    pnl: float
    regime: str


class ExperienceBuffer:
    def __init__(self, path: str = "data/experiences.ndjson"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, exp: Experience) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(exp)) + "\n")
