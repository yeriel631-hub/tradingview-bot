from flask import Flask, request, jsonify
import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "PEGA_TU_WEBHOOK_URL_AQUI")
SECRET_TOKEN = os.getenv("SECRET_TOKEN", "mi_token_secreto")


def build_discord_embed(data: dict) -> dict:
    symbol = data.get("symbol", "N/A").upper()
    price = data.get("price", "N/A")
    action = data.get("action", "N/A").upper()
    timeframe = data.get("timeframe", "")
    message = data.get("message", "")
    timestamp = datetime.utcnow().isoformat()

    if action in ("BUY", "LONG"):
        color = 0x00C853
        emoji = "🟢"
        action_label = "📈 COMPRA / LONG"
    elif action in ("SELL", "SHORT"):
        color = 0xFF1744
        emoji = "🔴"
        action_label = "📉 VENTA / SHORT"
    else:
        color = 0xFFAB00
        emoji = "🟡"
        action_label = f"⚡ {action}"

    fields = [
        {"name": "💹 Símbolo", "value": f"```{symbol}```", "inline": True},
        {"name": "💰 Precio", "value": f"```{price}```", "inline": True},
        {"name": "🎯 Acción", "value": action_label, "inline": True},
    ]

    if timeframe:
        fields.append({"name": "⏱ Temporalidad", "value": timeframe, "inline": True})
    if message:
        fields.append({"name": "📝 Nota", "value": message, "inline": False})

    embed = {
        "title": f"{emoji}  Alerta de TradingView",
        "color": color,
        "fields": fields,
        "footer": {"text": "TradingView → Discord Bot"},
        "timestamp": timestamp,
    }
    return embed


@app.route("/webhook", methods=["POST"])
def webhook():
    token = request.headers.get("X-Token") or request.args.get("token")
    if SECRET_TOKEN and token != SECRET_TOKEN:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = json.loads(request.data.decode("utf-8"))
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400

    print(f"[{datetime.now()}] Alerta recibida: {data}")

    embed = build_discord_embed(data)
    payload = {"embeds": [embed]}

    resp = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if resp.status_code not in (200, 204):
        print(f"Error Discord: {resp.status_code} {resp.text}")
        return jsonify({"error": "Discord delivery failed"}), 500

    return jsonify({"status": "ok"}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "running", "time": datetime.utcnow().isoformat()})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"🚀 Servidor iniciado en http://localhost:{port}/webhook")
    app.run(host="0.0.0.0", port=port, debug=False)