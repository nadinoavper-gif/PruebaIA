from __future__ import annotations


def dashboard_html() -> str:
    return """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>XAU/USD AI Dashboard</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; background: #0f172a; color: #e2e8f0; }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px; }
    .card { background: #111827; border: 1px solid #334155; border-radius: 10px; padding: 12px; }
    h1, h2 { margin: 0 0 8px; }
    label { display:block; margin-top:6px; font-size:12px; color:#94a3b8; }
    input, textarea, select { width:100%; background:#0b1220; color:#e2e8f0; border:1px solid #334155; border-radius:6px; padding:8px; }
    button { background:#2563eb; color:white; border:0; border-radius:6px; padding:8px 12px; cursor:pointer; margin-right:6px; margin-top:8px; }
    pre { white-space: pre-wrap; background:#020617; border:1px solid #334155; border-radius:6px; padding:8px; }
    .muted { color:#94a3b8; font-size:12px; }
  </style>
</head>
<body>
  <h1>Panel IA XAU/USD</h1>
  <p class="muted">Interfaz para precio automático, señal, entrenamiento online y feed TradingView.</p>
  <div class="row"><div class="card"><h2>Mercado</h2><button onclick="getPrice()">Obtener precio XAUUSD</button><pre id="priceOut">-</pre></div>
  <div class="card"><h2>Entrenamiento online</h2><button onclick="trainingStart()">Start</button><button onclick="trainingStatus()">Status</button><button onclick="trainingStop()">Stop</button><pre id="trainOut">-</pre></div></div>
  <div class="row"><div class="card"><h2>Generar señal</h2>
      <label>ATR</label><input id="atr" value="12" />
      <label>Pattern quality</label><input id="pq" value="0.8" />
      <label>Régimen</label><select id="regime"><option>trend</option><option>range</option><option>shock</option></select>
      <label>D1 probs [buy,sell,neutral]</label><input id="d1" value="0.55,0.2,0.25" />
      <label>Votes JSON</label>
      <textarea id="votes" rows="6">[{"timeframe":"1H","probs":[0.7,0.15,0.15],"confidence":0.8,"weight":1.0},{"timeframe":"4H","probs":[0.66,0.18,0.16],"confidence":0.8,"weight":1.0}]</textarea>
      <button onclick="getSignal()">Calcular señal</button>
      <pre id="signalOut">-</pre></div>
      <div class="card"><h2>TradingView Analysis</h2><label>Payload JSON</label>
      <textarea id="tvPayload" rows="8">{"symbol":"XAUUSD","timeframe":"1H","pattern":"triangle","note":"setup usuario","rsi":58.2,"fundamental_bias":0.3,"chart_image_url":"https://example.com/chart.png"}</textarea>
      <button onclick="sendTV()">Enviar análisis</button><button onclick="latestTV()">Ver últimos</button><pre id="tvOut">-</pre></div></div>
<script>
const api = ""; const j = (x) => JSON.stringify(x, null, 2);
async function getPrice(){ const r = await fetch(api + '/market/xauusd/price'); document.getElementById('priceOut').textContent = j(await r.json()); }
async function trainingStart(){ const r = await fetch(api + '/training/start', {method:'POST'}); document.getElementById('trainOut').textContent = j(await r.json()); }
async function trainingStatus(){ const r = await fetch(api + '/training/status'); document.getElementById('trainOut').textContent = j(await r.json()); }
async function trainingStop(){ const r = await fetch(api + '/training/stop', {method:'POST'}); document.getElementById('trainOut').textContent = j(await r.json()); }
async function getSignal(){ const d1 = document.getElementById('d1').value.split(',').map(Number); const votes = JSON.parse(document.getElementById('votes').value); const payload = { atr:Number(document.getElementById('atr').value), pattern_quality:Number(document.getElementById('pq').value), regime:document.getElementById('regime').value, d1_probs:d1, votes:votes, chaikin_ok:true, fundamentals:{ usd_index:100, real_yield_10y:1.0, fed_rate:4.5, risk_aversion_score:0.2 } }; const r = await fetch(api + '/signal/xauusd', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)}); document.getElementById('signalOut').textContent = j(await r.json()); }
async function sendTV(){ const payload = JSON.parse(document.getElementById('tvPayload').value); const r = await fetch(api + '/tradingview/analysis', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)}); document.getElementById('tvOut').textContent = j(await r.json()); }
async function latestTV(){ const r = await fetch(api + '/tradingview/analysis/latest?n=20'); document.getElementById('tvOut').textContent = j(await r.json()); }
</script></body></html>
"""


def dashboard_response():
    from fastapi.responses import HTMLResponse

    return HTMLResponse(dashboard_html())
