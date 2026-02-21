from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TrainerStats:
    running: bool = False
    steps: int = 0
    last_loss: float = 0.0
    last_update_ts: float = 0.0


class OnlineTrainer:
    """
    Entrenamiento online simplificado en caliente.
    Lee líneas nuevas de un archivo NDJSON de experiencias y simula pasos de update.
    """

    def __init__(self, experience_path: str = "data/experiences.ndjson", poll_s: float = 1.0):
        self.experience_path = Path(experience_path)
        self.poll_s = poll_s
        self.stats = TrainerStats()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._offset = 0

    def _train_step(self, line: str) -> float:
        # Proxy de "loss": decrece suavemente a medida que hay más pasos.
        base = max(0.01, 1.0 / (1.0 + self.stats.steps))
        penalty = 0.0 if line.strip() else 0.1
        return base + penalty

    def _loop(self) -> None:
        self.stats.running = True
        self.experience_path.parent.mkdir(parents=True, exist_ok=True)
        self.experience_path.touch(exist_ok=True)

        while not self._stop.is_set():
            with self.experience_path.open("r", encoding="utf-8") as f:
                f.seek(self._offset)
                new_lines = f.readlines()
                self._offset = f.tell()

            for line in new_lines:
                self.stats.steps += 1
                self.stats.last_loss = self._train_step(line)
                self.stats.last_update_ts = time.time()

            time.sleep(self.poll_s)

        self.stats.running = False

    def start(self) -> bool:
        if self._thread and self._thread.is_alive():
            return False
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return True

    def stop(self) -> bool:
        if not self._thread:
            return False
        self._stop.set()
        self._thread.join(timeout=2.0)
        return True

    def status(self) -> TrainerStats:
        return self.stats
