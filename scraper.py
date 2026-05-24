import websocket
import json
import sqlite3
import time
from datetime import datetime

DB = "aviator.db"

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
    conn2 = sqlite3.connect(DB)
    total = conn2.execute("SELECT COUNT(*) FROM rodadas").fetchone()[0]
    conn2.close()
    print(f"✅ Guardado: {multiplicador}x | Total: {total} rodadas")

def on_message(ws, message):
    try:
        print("📨", message[:150])
        data = json.loads(message)
        if isinstance(data, dict):
            for key in ["cashout","multiplier","value","coef","crash","result","coefficient","x"]:
                if key in data:
                    mult = data[key]
                    if mult and float(mult) > 1:
                        salvar(float(mult))
                        break
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

URLS = [
    "wss://aviator-odd.spribe.co/",
    "wss://api.spribe.co/aviator/ws",
    "wss://aviator.spribe.co/ws",
    "wss://spribe.co/ws/aviator",
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
