from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3, uuid
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

DB = "licenses.db"
ADMIN_PASSWORD = "Aviator@Angola2024"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS licenses (
            key TEXT PRIMARY KEY,
            expires_at TEXT,
            type TEXT,
            active INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route('/admin/generate', methods=['POST'])
def generate_license():
    data = request.get_json()
    if data.get("password") != ADMIN_PASSWORD:
        return jsonify({"status": "erro", "mensagem": "Senha errada"}), 403
    hours = int(data.get("hours", 24))
    ltype = data.get("type", "temp")
    new_key = str(uuid.uuid4()).upper().replace("-", "")[:12]
    new_key = f"{new_key[:4]}-{new_key[4:8]}-{new_key[8:12]}"
    if ltype == "lifetime":
        expires_at = "lifetime"
    else:
        expires_at = (datetime.utcnow() + timedelta(hours=hours)).isoformat()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO licenses VALUES (?,?,?,1)", (new_key, expires_at, ltype))
    conn.commit()
    conn.close()
    return jsonify({"status": "sucesso", "key": new_key, "expires": expires_at, "type": ltype})

@app.route('/auth/validate', methods=['POST'])
def validate_license():
    data = request.get_json()
    key = data.get("key", "").strip()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT expires_at, type, active FROM licenses WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    if not row or row[2] == 0:
        return jsonify({"status": "invalido", "mensagem": "Chave invalida"})
    expires_at, ltype, _ = row
    if ltype == "lifetime":
        return jsonify({"status": "valido", "type": "lifetime"})
    if datetime.utcnow() < datetime.fromisoformat(expires_at):
        return jsonify({"status": "valido", "type": ltype, "expires": expires_at})
    return jsonify({"status": "expirado", "mensagem": "Chave expirada"})

@app.route('/api/analyze', methods=['POST'])
def analyze_history():
    data = request.get_json()
    history = data.get("history", [])
    if len(history) < 10:
        return jsonify({"erro": "Envie pelo menos 10 rodadas"}), 400
    total = len(history)
    below_2x = sum(1 for x in history if x < 2.0)
    bet_2_5  = sum(1 for x in history if 2.0 <= x < 5.0)
    above_5x = sum(1 for x in history if x >= 5.0)
    avg      = sum(history) / total
    max_val  = max(history)
    streak = 0
    last_low = history[-1] < 2.0
    for x in reversed(history):
        if (x < 2.0) == last_low:
            streak += 1
        else:
            break
    patterns = []
    if streak >= 3 and last_low:
        patterns.append(f"Sequencia de {streak} baixas detectada")
    if streak >= 3 and not last_low:
        patterns.append(f"Sequencia de {streak} altas detectada")
    if above_5x / total > 0.15:
        patterns.append("Taxa de altas acima da media historica")
    if below_2x / total > 0.60:
        patterns.append("Muitas quedas rapidas detectadas")
    if avg > 3:
        patterns.append("Media de multiplicador elevada")
    if not patterns:
        patterns.append("Historico dentro dos padroes normais")
    return jsonify({
        "total_rodadas": total,
        "abaixo_2x_percent": round(below_2x / total * 100, 1),
        "entre_2_5x_percent": round(bet_2_5 / total * 100, 1),
        "acima_5x_percent": round(above_5x / total * 100, 1),
        "media_multiplicador": round(avg, 2),
        "maximo": round(max_val, 2),
        "sequencia_atual": f"{streak} {'baixas' if last_low else 'altas'}",
        "padroes": patterns,
        "aviso": "Analise estatistica. Nao garante resultado futuro."
    })

@app.route('/admin/keys', methods=['POST'])
def list_keys():
    data = request.get_json()
    if data.get("password") != ADMIN_PASSWORD:
        return jsonify({"status": "erro"}), 403
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT key, expires_at, type, active FROM licenses ORDER BY rowid DESC")
    rows = c.fetchall()
    conn.close()
    keys = [{"key": r[0], "expires": r[1], "type": r[2], "active": r[3]} for r in rows]
    return jsonify({"status": "sucesso", "total": len(keys), "keys": keys})

@app.route('/admin/revoke', methods=['POST'])
def revoke_key():
    data = request.get_json()
    if data.get("password") != ADMIN_PASSWORD:
        return jsonify({"status": "erro"}), 403
    key = data.get("key")
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE licenses SET active=0 WHERE key=?", (key,))
    conn.commit()
    conn.close()
    return jsonify({"status": "sucesso", "mensagem": f"Chave {key} desativada"})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
