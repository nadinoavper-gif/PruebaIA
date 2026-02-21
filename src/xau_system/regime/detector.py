from __future__ import annotations

import numpy as np
from sklearn.mixture import GaussianMixture


class RegimeDetector:
    """Detector simple de régimen (trend/range/shock) con GMM."""

    def __init__(self, n_components: int = 3, random_state: int = 42):
        self.model = GaussianMixture(n_components=n_components, random_state=random_state)
        self._fitted = False

    def fit(self, X: np.ndarray) -> None:
        self.model.fit(X)
        self._fitted = True

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("RegimeDetector no entrenado")
        labels = self.model.predict(X)
        return labels

    @staticmethod
    def map_regime(label: int) -> str:
        mapping = {0: "range", 1: "trend", 2: "shock"}
        return mapping.get(int(label), "range")
