from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import AsyncIterator, Callable


@dataclass
class MarketBar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str = "realtime"


class RealTimeBuffer:
    """Buffer circular para barras en vivo y escritura NDJSON para entrenamiento."""

    def __init__(self, maxlen: int = 5000, persist_path: str | None = "data/realtime_xauusd.ndjson"):
        self._buf: deque[MarketBar] = deque(maxlen=maxlen)
        self.persist_path = Path(persist_path) if persist_path else None
        if self.persist_path:
            self.persist_path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, bar: MarketBar) -> None:
        self._buf.append(bar)
        if self.persist_path:
            row = asdict(bar)
            row["timestamp"] = bar.timestamp.astimezone(timezone.utc).isoformat()
            with self.persist_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row) + "\n")

    def latest(self, n: int = 1) -> list[MarketBar]:
        if n <= 0:
            return []
        return list(self._buf)[-n:]

    def __len__(self) -> int:
        return len(self._buf)


class RealTimeCollector:
    """Consume un stream async de barras y alimenta el buffer."""

    def __init__(self, buffer: RealTimeBuffer):
        self.buffer = buffer
        self._callbacks: list[Callable[[MarketBar], None]] = []

    def register_callback(self, fn: Callable[[MarketBar], None]) -> None:
        self._callbacks.append(fn)

    async def run(self, stream: AsyncIterator[MarketBar], stop_event: asyncio.Event | None = None) -> None:
        stop_event = stop_event or asyncio.Event()
        async for bar in stream:
            if stop_event.is_set():
                break
            self.buffer.append(bar)
            for cb in self._callbacks:
                cb(bar)


async def mock_bar_stream(interval_s: float = 1.0) -> AsyncIterator[MarketBar]:
    """Stream simulado para paper-trading/entorno de desarrollo."""
    price = 2300.0
    while True:
        drift = 0.2
        price = max(1000.0, price + drift)
        yield MarketBar(
            timestamp=datetime.now(timezone.utc),
            open=price - 0.3,
            high=price + 0.5,
            low=price - 0.7,
            close=price,
            volume=1000.0,
            source="mock",
        )
        await asyncio.sleep(interval_s)
