import logging
import os
import random
import time
import requests
from datetime import datetime
from flask import Flask, jsonify, request, render_template_string
from logging.handlers import RotatingFileHandler

# Configure logging
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

# Create file handler
file_handler = RotatingFileHandler('/app/logs/app.log', maxBytes=10485760, backupCount=10)
file_handler.setFormatter(log_formatter)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

# Set up app logger
logger = logging.getLogger()
logger.setLevel(getattr(logging, log_level))
logger.addHandler(file_handler)
logger.addHandler(console_handler)

app = Flask(__name__)

# Chuck Norris facts stats
chuck_stats = {
    "total_requests": 0,
    "categories": {},
    "last_fact": "",
    "errors": 0
}

# HTML template for the main page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Chuck Norris Facts Monitor</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .fact {
            font-size: 24px;
            margin: 20px 0;
            padding: 15px;
            background-color: #fffacd;
            border-left: 5px solid #ffd700;
            border-radius: 4px;
        }
        .buttons {
            margin: 20px 0;
        }
        button {
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 10px 20px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 4px;
        }
        .stats {
            margin-top: 30px;
            padding: 15px;
            background-color: #e6f7ff;
            border-left: 5px solid #1890ff;
            border-radius: 4px;
        }
        .categories {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 20px 0;
        }
        .category-button {
            background-color: #1890ff;
        }
        .error-button {
            background-color: #ff4d4f;
        }
        .slow-button {
            background-color: #faad14;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Chuck Norris Facts Monitor</h1>
        
        <div class="fact">
            {{ fact }}
        </div>
        
        <div class="buttons">
            <button onclick="window.location.href='/'">Random Fact</button>
            <button onclick="window.location.href='/health'">Health Check</button>
            <button class="error-button" onclick="window.location.href='/error'">Trigger Error</button>
            <button class="slow-button" onclick="window.location.href='/slow'">Slow Response</button>
        </div>
        
        <div class="categories">
            <h3>Get fact by category:</h3>
            {% for category in categories %}
                <button class="category-button" onclick="window.location.href='/category/{{ category }}'">{{ category }}</button>
            {% endfor %}
        </div>
        
        <div class="stats">
            <h2>Monitoring Stats</h2>
            <p><strong>Total Requests:</strong> {{ stats.total_requests }}</p>
            <p><strong>Errors:</strong> {{ stats.errors }}</p>
            <p><strong>Categories Requested:</strong></p>
            <ul>
                {% for category, count in stats.categories.items() %}
                    <li>{{ category }}: {{ count }}</li>
                {% endfor %}
            </ul>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    logger.info("Index page accessed - fetching random Chuck Norris fact")
    try:
        response = requests.get('https://api.chucknorris.io/jokes/random')
        if response.status_code == 200:
            fact = response.json()['value']
            chuck_stats["last_fact"] = fact
            chuck_stats["total_requests"] += 1
            logger.info(f"Successfully fetched Chuck Norris fact: {fact[:30]}...")
            
            # Get categories for display
            categories_response = requests.get('https://api.chucknorris.io/jokes/categories')
            categories = categories_response.json() if categories_response.status_code == 200 else []
            
            return render_template_string(
                HTML_TEMPLATE, 
                fact=fact, 
                stats=chuck_stats,
                categories=categories
            )
        else:
            logger.error(f"Failed to fetch Chuck Norris fact, status code: {response.status_code}")
            chuck_stats["errors"] += 1
            return render_template_string(
                HTML_TEMPLATE, 
                fact="Chuck Norris is currently unavailable. Even APIs fear him.", 
                stats=chuck_stats,
                categories=[]
            )
    except Exception as e:
        logger.error(f"Error fetching Chuck Norris fact: {str(e)}")
        chuck_stats["errors"] += 1
        return render_template_string(
            HTML_TEMPLATE, 
            fact="Error fetching Chuck Norris fact. Chuck is investigating.", 
            stats=chuck_stats,
            categories=[]
        )

@app.route('/category/<category>')
def category_fact(category):
    logger.info(f"Category fact requested: {category}")
    try:
        response = requests.get(f'https://api.chucknorris.io/jokes/random?category={category}')
        if response.status_code == 200:
            fact = response.json()['value']
            chuck_stats["last_fact"] = fact
            chuck_stats["total_requests"] += 1
            
            # Update category stats
            if category in chuck_stats["categories"]:
                chuck_stats["categories"][category] += 1
            else:
                chuck_stats["categories"][category] = 1
                
            logger.info(f"Successfully fetched {category} Chuck Norris fact")
            
            # Get categories for display
            categories_response = requests.get('https://api.chucknorris.io/jokes/categories')
            categories = categories_response.json() if categories_response.status_code == 200 else []
            
            return render_template_string(
                HTML_TEMPLATE, 
                fact=fact, 
                stats=chuck_stats,
                categories=categories
            )
        else:
            logger.error(f"Failed to fetch {category} Chuck Norris fact, status code: {response.status_code}")
            chuck_stats["errors"] += 1
            return render_template_string(
                HTML_TEMPLATE, 
                fact=f"Chuck Norris {category} facts are too powerful to display right now.", 
                stats=chuck_stats,
                categories=[]
            )
    except Exception as e:
        logger.error(f"Error fetching {category} Chuck Norris fact: {str(e)}")
        chuck_stats["errors"] += 1
        return render_template_string(
            HTML_TEMPLATE, 
            fact=f"Error fetching {category} Chuck Norris fact.", 
            stats=chuck_stats,
            categories=[]
        )

@app.route('/slow')
def slow_response():
    logger.warning("Slow response endpoint accessed - simulating delay")
    # Simulate a slow response
    sleep_time = random.uniform(3, 8)
    time.sleep(sleep_time)
    logger.warning(f"Slow response completed after {sleep_time:.2f} seconds")
    
    # Get a fact after the delay
    try:
        response = requests.get('https://api.chucknorris.io/jokes/random')
        if response.status_code == 200:
            fact = response.json()['value']
            chuck_stats["last_fact"] = fact
            chuck_stats["total_requests"] += 1
            
            # Get categories for display
            categories_response = requests.get('https://api.chucknorris.io/jokes/categories')
            categories = categories_response.json() if categories_response.status_code == 200 else []
            
            return render_template_string(
                HTML_TEMPLATE, 
                fact=f"SLOW RESPONSE: {fact}", 
                stats=chuck_stats,
                categories=categories
            )
        else:
            chuck_stats["errors"] += 1
            return "Error fetching Chuck Norris fact", 500
    except Exception as e:
        logger.error(f"Error in slow response: {str(e)}")
        chuck_stats["errors"] += 1
        return "Server error", 500

@app.route('/error')
def simulate_error():
    # Route to test error logging
    error_type = request.args.get('type', 'error')
    
    if error_type == 'warning':
        logger.warning("This is a test warning from Chuck Norris")
        return render_template_string(
            HTML_TEMPLATE, 
            fact="WARNING: Chuck Norris doesn't warn, he informs fate.", 
            stats=chuck_stats,
            categories=[]
        )
    elif error_type == 'critical':
        logger.critical("This is a test critical error from Chuck Norris")
        chuck_stats["errors"] += 1
        return "Chuck Norris critical error", 500
    else:
        logger.error("This is a test error from Chuck Norris")
        chuck_stats["errors"] += 1
        return "Chuck Norris error", 500

@app.route('/health')
def health_check():
    # Simulate occasional health check failures
    if random.random() < 0.05:
        logger.error("Health check failed")
        return jsonify({"status": "error", "message": "Chuck Norris is currently busy roundhouse kicking the server"}), 500
    
    logger.info("Health check passed")
    return jsonify({
        "status": "ok", 
        "message": "Chuck Norris approves of this server's health", 
        "stats": chuck_stats
    })

@app.route('/api/stats')
def api_stats():
    logger.info("API stats requested")
    return jsonify(chuck_stats)

# Generate random logs periodically
def generate_logs():
    while True:
        # Generate random log every 20-60 seconds
        sleep_time = random.randint(20, 60)
        time.sleep(sleep_time)
        
        # Try to get a Chuck Norris fact for the log
        try:
            response = requests.get('https://api.chucknorris.io/jokes/random')
            if response.status_code == 200:
                fact = response.json()['value']
                fact_snippet = fact[:50] + "..." if len(fact) > 50 else fact
            else:
                fact_snippet = "Could not fetch Chuck Norris fact"
        except:
            fact_snippet = "Error fetching Chuck Norris fact"
        
        # Random log level distribution
        rand = random.random()
        if rand < 0.7:  # 70% INFO
            logger.info(f"Chuck Norris fact logged: {fact_snippet}")
        elif rand < 0.85:  # 15% WARNING
            logger.warning(f"Chuck Norris warning: {fact_snippet}")
        elif rand < 0.95:  # 10% ERROR
            logger.error(f"Chuck Norris error: {fact_snippet}")
        else:  # 5% CRITICAL
            logger.critical(f"Chuck Norris critical situation: {fact_snippet}")

# Start log generator in a separate thread
import threading
log_thread = threading.Thread(target=generate_logs, daemon=True)
log_thread.start()

if __name__ == '__main__':
    logger.info("Chuck Norris Facts application starting")
    app.run(host='0.0.0.0', port=5000)