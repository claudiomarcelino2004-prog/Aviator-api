import websocket
import json
import sqlite3
import time
from datetime import datetime

DB = "rocketman.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS rodadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            multiplicador REAL,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("Base de dados pronta!")

def salvar(multiplicador):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO rodadas (multiplicador, timestamp) VALUES (?,?)",
              (multiplicador, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    total = c.execute("SELECT COUNT(*) FROM rodadas").fetchone()[0]
    print(f"✅ Guardado: {multiplicador}x | Total: {total} rodadas")

def on_message(ws, message):
    try:
        print("📨 Mensagem:", message[:200])
        data = json.loads(message)
        mult = None
        if isinstance(data, dict):
            for key in ["crashpoint","multiplier","value","coef","coefficient","crash","result"]:
                if key in data:
                    mult = data[key]
                    break
        if mult:
            salvar(float(mult))
    except Exception as e:
        print("Erro:", e)

def on_error(ws, error):
    print("❌ Erro:", error)

def on_close(ws, a, b):
    print("🔄 Reconectar em 5s...")
    time.sleep(5)
    iniciar()

def on_open(ws):
    print("🚀 Ligado!")
    ws.send(json.dumps({"action":"subscribe","game":"rocketman"}))

URLS = [
    "wss://rocketman.elbet.com/socket.io/?transport=websocket",
    "wss://rocketman-api.elbet.com/ws",
    "wss://api.rocketman.elbet.com/ws",
    "wss://games.elbet.com/rocketman/ws",
]

def iniciar():
    init_db()
    for url in URLS:
        try:
            print(f"🔌 A tentar: {url}")
            ws = websocket.WebSocketApp(
                url,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )
            ws.run_forever()
        except Exception as e:
            print(f"❌ Falhou: {e}")
            time.sleep(2)

if __name__ == "__main__":
    iniciar()
