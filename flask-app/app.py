import logging
import random
import time
import requests
from flask import Flask, jsonify, render_template_string
from logging.handlers import RotatingFileHandler

# ----- LOGIMINE -----
# NB! Logivorming peab vastama Telegrafi grok_patterns'ile!
# Format: "2024-01-15T10:30:00 INFO mingi sõnum"
log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

file_handler = RotatingFileHandler('/app/logs/app.log', maxBytes=10485760, backupCount=5)
file_handler.setFormatter(log_formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

app = Flask(__name__)

# Statistika (näitamiseks UI-s)
stats = {"requests": 0, "errors": 0}

# HTML mall
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Chuck Norris Monitor</title>
    <style>
        * { font-family: 'Segoe UI', Arial, sans-serif; }
        body { max-width: 700px; margin: 40px auto; padding: 20px; background: #1a1a2e; color: #eee; }
        .card { background: #16213e; border-radius: 12px; padding: 25px; margin: 20px 0; }
        .fact { font-size: 20px; line-height: 1.6; color: #ffd700; border-left: 4px solid #ffd700; padding-left: 20px; }
        .btn { background: #e94560; border: none; color: white; padding: 12px 24px; margin: 8px; 
               cursor: pointer; border-radius: 6px; font-size: 14px; }
        .btn:hover { background: #ff6b6b; }
        .btn-warn { background: #f39c12; }
        .btn-err { background: #c0392b; }
        .stats { display: flex; gap: 30px; margin-top: 20px; }
        .stat { text-align: center; }
        .stat-num { font-size: 36px; font-weight: bold; color: #00d9ff; }
        h1 { color: #ffd700; }
    </style>
</head>
<body>
    <h1>🥋 Chuck Norris Facts</h1>
    <p style="color: #888;">Monitooritav TICK Stack'iga</p>
    
    <div class="card">
        <div class="fact">{{ fact }}</div>
    </div>
    
    <div>
        <button class="btn" onclick="location.href='/'">🎲 Uus nali</button>
        <button class="btn" onclick="location.href='/health'">💚 Health</button>
        <button class="btn btn-warn" onclick="location.href='/slow'">🐌 Aeglane</button>
        <button class="btn btn-err" onclick="location.href='/error'">💥 Viga</button>
    </div>
    
    <div class="card">
        <h3>📊 Statistika</h3>
        <div class="stats">
            <div class="stat">
                <div class="stat-num">{{ stats.requests }}</div>
                <div>Päringuid</div>
            </div>
            <div class="stat">
                <div class="stat-num">{{ stats.errors }}</div>
                <div>Vigu</div>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    """Avalehe päring - toob Chuck Norris nalju"""
    logger.info("Päring avalehele")
    try:
        r = requests.get('https://api.chucknorris.io/jokes/random', timeout=5)
        if r.status_code == 200:
            fact = r.json()['value']
            stats["requests"] += 1
            logger.info(f"Nali toodud: {fact[:50]}...")
            return render_template_string(HTML, fact=fact, stats=stats)
    except Exception as e:
        logger.error(f"API viga: {e}")
        stats["errors"] += 1
    return render_template_string(HTML, fact="Chuck Norris ei vastanud. Haruldane.", stats=stats)

@app.route('/slow')
def slow():
    """Simuleerib aeglast vastust - näed http_response graafikul spike'i"""
    delay = random.uniform(3, 7)
    logger.warning(f"Aeglane päring algab: {delay:.1f}s")
    time.sleep(delay)
    logger.warning(f"Aeglane päring lõppes")
    stats["requests"] += 1
    return render_template_string(HTML, fact=f"See võttis {delay:.1f} sekundit.", stats=stats)

@app.route('/error')
def error():
    """Simuleerib viga - näed logides ERROR taseme kirjet"""
    logger.error("Simuleeritud viga!")
    stats["errors"] += 1
    return "Viga!", 500

@app.route('/health')
def health():
    """Health check endpoint - Telegraf küsib seda iga 10 sek"""
    # 2% tõenäosusega simuleerime viga (testimiseks)
    if random.random() < 0.02:
        logger.error("Health check failed")
        return jsonify({"status": "error"}), 500
    return jsonify({"status": "ok", "stats": stats})

if __name__ == '__main__':
    logger.info("Chuck Norris Monitor käivitub...")
    app.run(host='0.0.0.0', port=5000)
