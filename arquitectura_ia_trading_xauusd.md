# Arquitectura técnica integral de IA para trading algorítmico en XAU/USD

> **Ámbito exclusivo:** Oro (XAU/USD spot o futuros).  
> **Propósito:** detectar zonas de entrada/salida (COMPRA/VENTA/NEUTRAL) mediante patrones chartistas + contexto temporal multiescala + aprendizaje continuo.

---

## 1) Objetivo del sistema y principios de diseño

### Objetivo operativo
Diseñar un sistema híbrido capaz de:
1. **Reconocer patrones chartistas** en velas japonesas (HCH, dobles techos/suelos, triángulos, banderas, cuñas, canales, S/R dinámicos).
2. **Combinar múltiples temporalidades** (1H, 4H, D1, W1) en un modelo jerárquico.
3. Emitir señal final con:
   - `signal ∈ {BUY, SELL, NEUTRAL}`
   - `confidence ∈ [0,1]`
   - `entry_zone`, `stop_zone`, `target_zone(s)`
   - tamaño de riesgo sugerido por trade: **1–2% (máx. 3%)** según calidad del patrón y régimen.

### Principios clave
- **Gold-first**: calibrado para comportamiento específico del oro (activo refugio, sensibilidad a USD real, tasas, riesgo geopolítico).
- **Multimodal**: imagen (chart) + series temporales + indicadores + volumen.
- **Ensemble robusto**: especialistas por timeframe y patrón.
- **Autoaprendizaje controlado**: actualización online con límites de seguridad y evaluación en sombra.

---

## 2) Arquitectura de alto nivel (end-to-end)

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                        CAPA DE INGESTA DE DATOS XAU/USD                     │
│  Histórico OHLCV (15+ años) | WebSocket real-time | Calendario macro        │
└──────────────────────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                  PREPROCESAMIENTO Y FEATURE ENGINEERING                      │
│  - Limpieza, resample 1H/4H/D1/W1                                           │
│  - Normalización robusta (rolling z-score, log returns, ATR scaling)        │
│  - Render de imágenes de velas por ventana (OpenCV/mplfinance)              │
│  - Indicadores: RSI, MACD, Chaikin AD, ATR, volumen relativo                │
│  - Etiquetado supervisado inicial + weak labeling + QA humana                │
└──────────────────────────────────────────────────────────────────────────────┘
                     │
                     ├─────────────── rama visual ────────────────┐
                     ▼                                             ▼
┌──────────────────────────────┐                 ┌────────────────────────────────┐
│ CNN por temporalidad         │                 │ Modelo temporal (GRU/LSTM)     │
│ Conv-BN-ReLU-MaxPool + FPN   │                 │ secuencias multivariantes       │
│ salida: embedding + patrón   │                 │ + self-attention temporal        │
└──────────────────────────────┘                 └────────────────────────────────┘
                     │                             │
                     └────────────── fusión multimodal ────────────┘
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                     FUSIÓN + ATENCIÓN INTER-TIMEFRAME                        │
│  - Cross-attention entre 1H/4H/D1/W1                                        │
│  - Capa densa para: señal, confianza, zonas de precio                       │
└──────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│               ENSAMBLE + GESTOR DE RIESGO + MOTOR DE EJECUCIÓN               │
│  - Voting ponderado por calibración y régimen                                │
│  - Filtro contradicciones entre temporalidades                                │
│  - Sizing 1-2% (máx 3%), SL/TP por ATR y estructura de patrón                │
└──────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│          FEEDBACK LOOP (AUTOAPRENDIZAJE + REGIME DETECTION + MLOPS)          │
│  - Reward por PnL ajustado por riesgo y coste                                │
│  - Online fine-tuning en cola validada                                       │
│  - Drift detector + champion/challenger                                      │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 3) Capa de datos y preprocesamiento

## 3.1 Fuentes y cobertura
- Histórico de **15+ años** para XAU/USD (spot/futuros continuo).
- Campos mínimos: `timestamp, open, high, low, close, volume`.
- Opcional exógeno (solo si aporta out-of-sample): DXY, UST10Y real yield, calendario macro.

## 3.2 Pipeline de calidad de datos
1. Detección de huecos y duplicados.
2. Ajuste de timezone y sesiones.
3. Resampling consistente en 1H/4H/D1/W1.
4. Versionado de datasets (`DVC`/`Delta Lake`).

## 3.3 Normalización
- Precios: `log-return` y `z-score rolling` (evita fuga de información).
- Volumen: `volume / rolling_median(volume, n)` para robustez.
- Rango: escalado por `ATR` para comparabilidad entre regímenes.

## 3.4 Generación de imágenes chartistas
Para cada ventana temporal (ej. 128 velas):
- Render de velas + overlays (tendencias, niveles S/R estimados).
- Imagen RGB (ej. `224x224`) para CNN.
- Canales opcionales extras: mapa de volumen, heatmap de volatilidad.

## 3.5 Aumentación de datos (patrones raros)
- **Geométrica suave**: escalado anisotrópico controlado, pequeñas rotaciones, traslación.
- **Temporal warping**: compresión/expansión local de segmentos del patrón.
- **Perturbación estocástica**: ruido microestructural coherente con ATR.
- **Mixup/CutMix temporal** en embeddings, no en labels duros cuando degrade semántica.
- **Generación sintética condicionada** (TimeGAN/VAE) para clases minoritarias (ej. cuñas de alta calidad).

---

## 4) Módulo de visión (CNN)

## 4.1 Arquitectura recomendada (por timeframe)
- Backbone CNN (Keras):
  - `Conv2D(32,3) -> BN -> ReLU -> MaxPool`
  - `Conv2D(64,3) -> BN -> ReLU -> MaxPool`
  - `Conv2D(128,3) -> BN -> ReLU -> MaxPool`
  - `Conv2D(256,3) -> BN -> ReLU`
  - `GlobalAveragePooling`
- Cabezas de salida:
  1. **Clasificación de patrón** (softmax multicategoría + “none”).
  2. **Calidad del patrón** (regresión 0..1).
  3. **Puntos estructurales** (neckline, breakout zone, invalidation).

## 4.2 Pérdidas
- `L_total = λ1*FocalLoss(pattern) + λ2*BCE(valid_breakout) + λ3*Huber(keypoints)`
- Focal para balancear patrones raros.

## 4.3 Estrategias anti-overfitting
- Split temporal estricto (walk-forward).
- Early stopping + dropout + weight decay.
- Test en periodos de crisis (2008, 2020, 2022) como “stress OOS”.

---

## 5) Módulo temporal (GRU/LSTM + atención)

## 5.1 Entrada multivariante
Para cada timeframe:
- OHLC normalizado
- retornos y volatilidad
- RSI, MACD, Chaikin AD
- volumen relativo
- embedding visual de CNN

## 5.2 Arquitectura
- `BiGRU(128, return_sequences=True)` (o LSTM equivalente).
- `MultiHeadSelfAttention(num_heads=4, key_dim=32)`.
- `LayerNorm + Residual`.
- `Dense(128, gelu) -> Dropout -> Dense(outputs)`.

## 5.3 Salidas
- Probabilidad direccional (up/down/neutral)
- Horizonte óptimo (n barras)
- Mapa de atención temporal (explicabilidad).

---

## 6) Arquitectura híbrida CNN-GRU/LSTM con atención multiescala

## 6.1 Fusión
- **Early fusion**: concatenar features técnicas + embedding CNN.
- **Late fusion**: promedio ponderado de logits por timeframe.
- **Cross-timeframe attention**: D1/W1 modulan 1H/4H para reducir ruido.

## 6.2 Regla de consenso de señal
Ejemplo:
- BUY si:
  - `P_buy_1H > 0.62`, `P_buy_4H > 0.60`
  - sesgo D1 no bajista fuerte
  - confirmación volumen (`Chaikin > umbral` o volumen relativo breakout > 1.2)
- SELL análogo.
- Si conflicto fuerte -> `NEUTRAL`.

---

## 7) Módulo de autoaprendizaje

## 7.1 Reward y RL
Se define recompensa por operación cerrada:

`reward = α * net_return - β * drawdown_increment - γ * turnover_cost - δ * regime_mismatch`

- `net_return`: retorno neto post-costes.
- penaliza exceso de rotación y desalineación con régimen detectado.

## 7.2 Online fine-tuning seguro
- Buffer de experiencias recientes (ej. últimas 4–8 semanas).
- Reentreno incremental nocturno con **gating**:
  1. Validación en conjunto sombra.
  2. No degradar Sharpe ni aumentar max drawdown > tolerancia.
  3. Canary deployment 10% señales antes de promover a champion.

## 7.3 Detección de régimen
- Features: volatilidad realizada, pendiente de tendencia, autocorrelación, spread intradía, macro proxy.
- Modelo: HMM / clustering (Gaussian Mixture, k=3..5) → estados (trend, range, shock).
- Cada régimen activa pesos distintos del ensemble y umbrales de confianza.

---

## 8) Sistema de ensemble

- Modelos especialistas:
  - Por timeframe: 1H, 4H, D1, W1.
  - Por familia de patrón: reversión, continuación, ruptura.
- Votación ponderada:
  - Peso por calibración reciente (Brier score inverso).
  - Peso por régimen (performance condicionada).
- Meta-modelo de calibración final (Platt/Isotonic) para confianza confiable.

---

## 9) Gestión de riesgo (restricción 1–2%, máximo 3%)

## 9.1 Position sizing
- Riesgo base por operación: **1%**.
- Subida a **2%** si:
  - consenso multitimeframe fuerte,
  - patrón de alta calidad,
  - régimen favorable.
- **Máx. absoluto 3%** solo en señal excepcional y liquidez adecuada.

## 9.2 Stops y objetivos
- `SL` por invalidación estructural del patrón + colchón ATR.
- `TP1/TP2` por proyección chartista (altura patrón) y niveles S/R.
- trailing dinámico si atención detecta extensión de tendencia.

## 9.3 Cortacircuitos
- Stop diario de pérdida.
- Pausa automática tras N pérdidas consecutivas.
- Reducción de tamaño en régimen shock.

---

## 10) Flujo de datos operacional

1. Llega nueva barra vía WebSocket.
2. Actualiza features e imágenes por timeframe.
3. CNN detecta patrón + calidad.
4. GRU/LSTM+attention estima dirección y contexto temporal.
5. Ensemble agrega y calibra probabilidad.
6. Motor de riesgo calcula `entry/SL/TP` y tamaño (1–2%, max 3%).
7. Emite señal o NEUTRAL.
8. Al cierre de trade, se escribe experiencia para RL/online learning.

---

## 11) Plan de implementación (timeline sugerido)

## Fase 0 (Semanas 1–2): Infra y datos
- Conectores de datos históricos + real-time.
- Normalización, validación, versionado.

## Fase 1 (Semanas 3–6): Etiquetado y baseline CNN
- Definir taxonomía de patrones.
- Etiquetado supervisado inicial + herramienta QA.
- Entrenar CNN baseline por timeframe.

## Fase 2 (Semanas 7–10): Híbrido CNN-GRU/LSTM + atención
- Integrar features técnicas y embeddings visuales.
- Entrenar modelo multimodal y calibrar confianza.

## Fase 3 (Semanas 11–14): Ensemble + riesgo + backtesting
- Implementar votación ponderada y consenso.
- Backtesting walk-forward con costes y slippage.

## Fase 4 (Semanas 15–18): Autoaprendizaje y régimen
- RL reward loop y online fine-tuning con gating.
- Detector de régimen y conmutación adaptativa.

## Fase 5 (Semanas 19–22): Paper trading y hardening
- Prueba en real sin ejecución.
- Monitoreo de drift, latencia, estabilidad.

## Fase 6 (Semanas 23+): Producción gradual
- Canary y despliegue progresivo.
- Revisión mensual de riesgo y performance.

---

## 12) Métricas de evaluación

## 12.1 Reconocimiento de patrones
- Matriz de confusión por patrón y timeframe.
- F1 macro, recall en clases raras.
- Error en keypoints estructurales.

## 12.2 Trading
- Rentabilidad acumulada neta.
- Sharpe/Sortino.
- Max Drawdown.
- Win rate y payoff ratio.
- Expectancy por operación.

## 12.3 Generalización
- Walk-forward multi-régimen.
- Estabilidad de calibración de confianza.
- Performance OOS en ventanas no vistas.

---

## 13) Respuestas a preguntas de reflexión

### 13.1 ¿Cómo manejar la subjetividad chartista?
- Formalizar definición matemática de cada patrón (restricciones geométricas y temporales).
- Etiquetado dual (anotador A/B) + arbitraje para reducir sesgo humano.
- Salida probabilística y no binaria (con intervalo de confianza).
- Usar keypoints estructurales para explicabilidad y auditoría.

### 13.2 ¿Qué aumentación usar para patrones raros?
- Combinación de: warping temporal + perturbación ATR + generación sintética condicionada (TimeGAN/VAE).
- Priorización por clases minoritarias y hard-negative mining.

### 13.3 ¿Cómo evitar overfitting al pasado?
- Walk-forward estricto, no random split.
- Regularización fuerte y test en regímenes extremos.
- Ensemble con modelos menos correlacionados.
- Política de actualización online con umbrales de no-regresión.

### 13.4 ¿Qué hacer con patrones contradictorios entre temporalidades?
- Jerarquía: W1/D1 como contexto, 4H como confirmación, 1H como timing.
- Si contradicción material y baja confianza conjunta -> NEUTRAL.
- Reducción automática de tamaño o bloqueo de operación.

### 13.5 ¿Cómo incorporar volumen como confirmación?
- Features: Chaikin AD, OBV, volumen relativo, burst de volumen en breakout.
- Reglas: sin confirmación de volumen, la señal baja categoría o se invalida.
- Peso dinámico del volumen según régimen (más útil en rupturas que en rangos).

---

## 14) Riesgos y limitaciones

- **No estacionariedad** del mercado del oro.
- Riesgo de eventos exógenos abruptos (geopolítica, bancos centrales).
- Calidad de volumen en OTC spot puede ser proxy imperfecto.
- Deriva de concepto y fatiga de modelos.
- Riesgo operativo (latencia, datos corruptos, reconexión WebSocket).

Mitigaciones:
- drift detection, fallback a modo conservador, límites de pérdida y circuit breakers.

---

## 15) Stack tecnológico sugerido

- **Modelado:** TensorFlow/Keras.
- **Visión:** OpenCV + mplfinance.
- **Series:** pandas, numpy, ta-lib/pandas-ta.
- **Serving:** FastAPI + WebSockets.
- **Backtesting:** vectorbt/backtrader (con costes realistas).
- **Almacenamiento:**
  - Time-series DB (TimescaleDB/InfluxDB) para OHLCV.
  - Vector DB (Qdrant/FAISS) para embeddings de patrones.
- **MLOps:** MLflow + DVC + Prometheus/Grafana.

---

## 16) Estructura base de código (Python, pseudocódigo)

```python
# project_structure
# ├── data/
# ├── features/
# ├── models/
# │   ├── cnn_pattern.py
# │   ├── temporal_gru.py
# │   ├── fusion_attention.py
# │   └── ensemble.py
# ├── rl/
# │   ├── reward.py
# │   └── online_update.py
# ├── risk/
# │   └── position_sizing.py
# ├── api/
# │   └── app_fastapi.py
# └── backtest/
#     └── walk_forward.py
```

```python
# models/cnn_pattern.py
import tensorflow as tf
from tensorflow.keras import layers, Model


def build_cnn(input_shape=(224, 224, 3), n_patterns=10):
    x_in = layers.Input(shape=input_shape)
    x = x_in
    for f in [32, 64, 128, 256]:
        x = layers.Conv2D(f, 3, padding="same")(x)
        x = layers.BatchNormalization()(x)
        x = layers.ReLU()(x)
        if f < 256:
            x = layers.MaxPool2D()(x)
    emb = layers.GlobalAveragePooling2D(name="embedding")(x)
    pattern = layers.Dense(n_patterns, activation="softmax", name="pattern_head")(emb)
    quality = layers.Dense(1, activation="sigmoid", name="quality_head")(emb)
    return Model(x_in, [pattern, quality, emb], name="cnn_pattern")
```

```python
# models/fusion_attention.py
import tensorflow as tf
from tensorflow.keras import layers, Model


def build_hybrid(seq_len=128, n_features=32, emb_dim=256):
    seq_in = layers.Input((seq_len, n_features), name="seq_features")
    vis_in = layers.Input((emb_dim,), name="visual_embedding")

    # Broadcast embedding visual a la secuencia
    vis_seq = layers.RepeatVector(seq_len)(vis_in)
    x = layers.Concatenate()([seq_in, vis_seq])

    x = layers.Bidirectional(layers.GRU(128, return_sequences=True))(x)
    attn = layers.MultiHeadAttention(num_heads=4, key_dim=32)(x, x)
    x = layers.LayerNormalization()(x + attn)
    x = layers.GlobalAveragePooling1D()(x)

    x = layers.Dense(128, activation="gelu")(x)
    x = layers.Dropout(0.2)(x)

    signal = layers.Dense(3, activation="softmax", name="signal")(x)  # BUY/SELL/NEUTRAL
    conf = layers.Dense(1, activation="sigmoid", name="confidence")(x)
    tp_sl = layers.Dense(4, activation="linear", name="zones")(x)  # entry_low/high, sl, tp
    return Model([seq_in, vis_in], [signal, conf, tp_sl], name="hybrid_cnn_gru_attn")
```

```python
# risk/position_sizing.py

def risk_fraction(confidence: float, regime: str, pattern_quality: float) -> float:
    base = 0.01
    if confidence > 0.75 and pattern_quality > 0.7 and regime in {"trend", "stable"}:
        base = 0.02
    if confidence > 0.88 and pattern_quality > 0.85 and regime == "trend":
        base = 0.03  # techo máximo permitido
    return min(base, 0.03)
```

```python
# rl/reward.py

def trade_reward(net_return, dd_increment, turnover_cost, regime_mismatch,
                 a=1.0, b=0.5, c=0.2, d=0.2):
    return a * net_return - b * dd_increment - c * turnover_cost - d * regime_mismatch
```

```python
# api/app_fastapi.py
from fastapi import FastAPI

app = FastAPI()


@app.post("/signal/xauusd")
def get_signal(payload: dict):
    # 1) construir features + imagen
    # 2) inferencia CNN + híbrido temporal
    # 3) ensemble y calibración
    # 4) riesgo: tamaño 1-2% (máx 3%)
    return {
        "instrument": "XAUUSD",
        "signal": "BUY",
        "confidence": 0.78,
        "entry_zone": [2324.5, 2326.2],
        "stop_zone": [2316.8, 2317.5],
        "targets": [2335.0, 2341.2],
        "risk_fraction": 0.02,
    }
```

---

## 17) Referencias técnicas (mapeo a decisiones)

- **CNN en oro / reconocimiento visual de patrones** → justifica módulo visual especializado y clasificación de formaciones chartistas.
- **Modelos híbridos CNN-GRU/LSTM con mejoras 22–48%** → sustenta la fusión visión + secuencia.
- **Self-attention para dependencias largas** → soporte al bloque de atención temporal/inter-timeframe.
- **LSTM multivariante con indicadores** → integración RSI/MACD/Chaikin/volumen.
- **Ensemble + online update** → base para autoaprendizaje con champion/challenger.

> Nota: las referencias marcadas como `[research: n]` deben vincularse en implementación final a DOI/artículos concretos en un `docs/references.bib` para trazabilidad científica.

