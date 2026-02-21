from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from xau_system.data.live_price import PriceTick


@dataclass
class MT5OrderRequest:
    symbol: str
    side: str  # BUY/SELL
    lot: float
    stop_loss: float
    take_profit: float
    deviation: int = 20
    magic: int = 20260221
    comment: str = "xau_system"


class MT5Bridge:
    """Bridge opcional a MetaTrader 5 (requiere paquete MetaTrader5 instalado y terminal activa)."""

    def __init__(self):
        self._mt5 = None
        self.available = False
        try:
            import MetaTrader5 as mt5  # type: ignore

            self._mt5 = mt5
            self.available = True
        except Exception:
            self.available = False

    def initialize(self) -> tuple[bool, str]:
        if not self.available or self._mt5 is None:
            return False, "MetaTrader5 no disponible en este entorno"
        ok = self._mt5.initialize()
        if not ok:
            return False, f"MT5 initialize() falló: {self._mt5.last_error()}"
        return True, "MT5 inicializado"

    def shutdown(self) -> None:
        if self.available and self._mt5 is not None:
            self._mt5.shutdown()

    def get_tick(self, symbol: str = "XAUUSD") -> PriceTick | None:
        if not self.available or self._mt5 is None:
            return None
        tick = self._mt5.symbol_info_tick(symbol)
        if tick is None:
            return None
        ts = datetime.fromtimestamp(int(tick.time), tz=timezone.utc)
        return PriceTick(
            symbol=symbol,
            bid=float(tick.bid),
            ask=float(tick.ask),
            last=float(tick.last if tick.last else (tick.bid + tick.ask) / 2.0),
            timestamp=ts,
            source="mt5",
        )

    def send_market_order(self, req: MT5OrderRequest) -> tuple[bool, str, dict]:
        """Envía orden de mercado. Si MT5 no está disponible, devuelve error controlado."""
        if not self.available or self._mt5 is None:
            return False, "MetaTrader5 no disponible", {}

        side = req.side.upper()
        order_type = self._mt5.ORDER_TYPE_BUY if side == "BUY" else self._mt5.ORDER_TYPE_SELL

        tick = self._mt5.symbol_info_tick(req.symbol)
        if tick is None:
            return False, f"Sin tick para {req.symbol}", {}

        price = float(tick.ask if side == "BUY" else tick.bid)
        request = {
            "action": self._mt5.TRADE_ACTION_DEAL,
            "symbol": req.symbol,
            "volume": float(req.lot),
            "type": order_type,
            "price": price,
            "sl": float(req.stop_loss),
            "tp": float(req.take_profit),
            "deviation": int(req.deviation),
            "magic": int(req.magic),
            "comment": req.comment,
            "type_time": self._mt5.ORDER_TIME_GTC,
            "type_filling": self._mt5.ORDER_FILLING_IOC,
        }

        result = self._mt5.order_send(request)
        if result is None:
            return False, f"order_send retornó None: {self._mt5.last_error()}", request

        ok = int(getattr(result, "retcode", -1)) == int(self._mt5.TRADE_RETCODE_DONE)
        msg = f"retcode={getattr(result, 'retcode', None)}"
        return ok, msg, request
