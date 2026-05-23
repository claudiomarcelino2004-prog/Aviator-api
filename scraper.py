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
    print("Base de dados criada!")

def salvar(multiplicador):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO rodadas (multiplicador, timestamp) VALUES (?,?)",
              (multiplicador, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    print(f"Guardado: {multiplicador}x")

def on_message(ws, message):
    try:
        data = json.loads(message)
        print("Mensagem:", data)
        if "crashpoint" in str(data).lower():
            mult = data.get("crashpoint") or data.get("multiplier") or data.get("value")
            if mult:
                salvar(float(mult))
    except Exception as e:
        print("Erro:", e)

def on_error(ws, error):
    print("Erro WebSocket:", error)

def on_close(ws, close_status_code, close_msg):
    print("Ligação fechada. A reconectar em 5s...")
    time.sleep(5)
    iniciar()

def on_open(ws):
    print("Ligado ao Rocketman!")

def iniciar():
    init_db()
    print("A ligar ao Rocketman MegaGame...")
    ws = websocket.WebSocketApp(
        "wss://megagamelive.com/rocketman",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )
    ws.run_forever()

if __name__ == "__main__":
    iniciar()
