# XAU/USD AI Trading Architecture (Python Base)

Implementación base en Python de la arquitectura híbrida propuesta para señales de trading en oro (XAU/USD):

- Pipeline de datos OHLCV y preprocesamiento.
- Features técnicas (RSI, MACD, Chaikin AD, ATR, z-score).
- Módulos de modelos (CNN, temporal GRU+attention, híbrido).
- Ensemble de consenso multitemporal.
- Gestión de riesgo fija al 1% por operación.
- Reward y gating para autoaprendizaje online.
- API FastAPI para inferencia de señal.
- Ingesta en tiempo real (`/ingest/bar`) con buffer persistente para entrenamiento continuo.
- Fusión de sesgo fundamental (USD, real yields, tasa FED, aversión al riesgo) y confirmación de volumen.
- Detección automática de precio de XAUUSD con proveedores en cascada (MT5 -> buffer realtime -> fallback).
- Integración opcional con MetaTrader 5 para obtención de tick y envío de órdenes de mercado.
- Objetivo de beneficio: 2% por defecto, 3% máximo en señales de alta confianza.
- Entrenamiento online instantáneo en ejecución (`/training/start`, `/training/status`, `/training/stop`).
- Recepción de análisis del usuario desde TradingView por webhook (`/tradingview/analysis`).

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
- `POST /training/start`, `GET /training/status`, `POST /training/stop`: entrenamiento online instantáneo.
- `POST /tradingview/analysis`: ingesta del análisis chartista/fundamental del usuario en TradingView.
- `GET /tradingview/analysis/latest?n=20`: consulta de análisis recientes recibidos.


## Integración MetaTrader 5 (opcional)

Si `MetaTrader5` está instalado y la terminal está abierta/logueada, puedes:

- `POST /mt5/initialize` para inicializar conexión
- `GET /market/xauusd/price` para precio automático del oro
- `POST /mt5/order` para enviar orden de mercado

Si MT5 no está disponible, la API responde de forma segura sin romper el servicio.


## Interfaz gráfica

Se añadió una interfaz web para uso sencillo del usuario:

- `GET /` o `GET /ui` abre el panel visual.
- Desde la UI puedes:
  - Consultar precio automático de XAUUSD.
  - Iniciar/parar/monitorizar entrenamiento online.
  - Enviar análisis de TradingView.
  - Generar señal sin construir requests manuales.


## Módulo de implementación y pruebas

Se añadió `src/xau_system/implementation.py` para guiar el uso y validar el sistema rápidamente.

- `ImplementationModule.default_signal_payload()`: payload base para señal XAUUSD.
- `ImplementationModule.smoke_test_core()`: prueba rápida del núcleo sin levantar API.
- `ImplementationModule.smoke_test_api(base_url)`: prueba del endpoint `/signal/xauusd`.

Script de ejecución:

```bash
python scripts/run_implementation_checks.py --skip-api
python scripts/run_implementation_checks.py --api http://127.0.0.1:8000
```
