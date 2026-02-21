from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from xau_system.data.realtime import RealTimeBuffer


@dataclass
class PriceTick:
    symbol: str
    bid: float
    ask: float
    last: float
    timestamp: datetime
    source: str


class PriceProvider(Protocol):
    def get_tick(self, symbol: str = "XAUUSD") -> PriceTick | None:
        ...


class BufferPriceProvider:
    """Usa el último close de la ingesta real-time como precio actual."""

    def __init__(self, buffer: RealTimeBuffer):
        self.buffer = buffer

    def get_tick(self, symbol: str = "XAUUSD") -> PriceTick | None:
        latest = self.buffer.latest(1)
        if not latest:
            return None
        bar = latest[-1]
        return PriceTick(
            symbol=symbol,
            bid=bar.close,
            ask=bar.close,
            last=bar.close,
            timestamp=bar.timestamp,
            source=f"buffer:{bar.source}",
        )


class CompositePriceProvider:
    """Prueba proveedores en cascada hasta obtener un tick válido."""

    def __init__(self, providers: list[PriceProvider]):
        self.providers = providers

    def get_tick(self, symbol: str = "XAUUSD") -> PriceTick | None:
        for provider in self.providers:
            tick = provider.get_tick(symbol)
            if tick and tick.last > 0:
                return tick
        return None


class FixedPriceProvider:
    """Proveedor de respaldo para desarrollo/testing."""

    def __init__(self, price: float = 2300.0, source: str = "fixed"):
        self.price = price
        self.source = source

    def get_tick(self, symbol: str = "XAUUSD") -> PriceTick | None:
        return PriceTick(
            symbol=symbol,
            bid=self.price,
            ask=self.price,
            last=self.price,
            timestamp=datetime.now(timezone.utc),
            source=self.source,
        )


class MT5PriceProvider:
    """Proveedor de tick desde MetaTrader 5 si está disponible."""

    def __init__(self, bridge):
        self.bridge = bridge

    def get_tick(self, symbol: str = "XAUUSD") -> PriceTick | None:
        return self.bridge.get_tick(symbol)
