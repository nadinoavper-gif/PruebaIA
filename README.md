# XAU/USD AI Trading Architecture (Python Base)

Implementación base en Python de la arquitectura híbrida propuesta para señales de trading en oro (XAU/USD):

- Pipeline de datos OHLCV y preprocesamiento.
- Features técnicas (RSI, MACD, Chaikin AD, ATR, z-score).
- Módulos de modelos (CNN, temporal GRU+attention, híbrido).
- Ensemble de consenso multitemporal.
- Gestión de riesgo (1-2%, máximo 3%).
- Reward y gating para autoaprendizaje online.
- API FastAPI para inferencia de señal.
- Ingesta en tiempo real (`/ingest/bar`) con buffer persistente para entrenamiento continuo.
- Fusión de sesgo fundamental (USD, real yields, tasa FED, aversión al riesgo) y confirmación de volumen.

## Estructura

```text
src/xau_system/
  api/
  data/
  ensemble/
  features/
  models/
  regime/
  risk/
  rl/
  utils/
```

## Ejecutar tests

```bash
pytest
```

## Levantar API

```bash
uvicorn xau_system.api.app_fastapi:app --reload
```


## Endpoints nuevos

- `POST /ingest/bar`: guarda barras en tiempo real para entrenamiento incremental.
- `GET /realtime/latest?n=5`: retorna últimas barras en buffer.
- `POST /signal/xauusd`: acepta `fundamentals` y `chaikin_ok` para fusión técnico-fundamental.
