import json
import logging
import os
import time
from datetime import datetime, timezone

from flask import Flask, Response, g, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

VERSION = "1.0.1"

app = Flask(__name__)

logging.getLogger('werkzeug').setLevel(logging.ERROR)

# --- Metrics ---
REQUESTS = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
LATENCY = Histogram('http_request_duration_seconds', 'Request latency in seconds', ['endpoint'])
APP_INFO = Gauge('app_info', 'Application version and environment', ['version', 'environment'])


def get_environment():
    return os.environ.get('ENVIRONMENT') or os.environ.get('APP_ENV') or 'unknown'


APP_INFO.labels(version=VERSION, environment=get_environment()).set(1)



@app.before_request
def start_timer():
    g.start = time.perf_counter()


@app.after_request
def record_request(response):
    rule = request.url_rule.rule if request.url_rule else 'unmatched'
    REQUESTS.labels(method=request.method, endpoint=rule, status=str(response.status_code)).inc()
    LATENCY.labels(endpoint=rule).observe(time.perf_counter() - g.start)

    entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'level': 'ERROR' if response.status_code >= 500 else 'INFO',
        'message': g.get('log_message', 'request completed'),
        'endpoint': request.path,
        'method': request.method,
        'status': response.status_code,
        'environment': get_environment(),
    }
    print(json.dumps(entry), flush=True)
    return response


# --- Routes ---
@app.route('/health')
def health_check():
    return jsonify({"status": "UP"})


@app.route('/version')
def version():
    return jsonify({"version": VERSION})


@app.route('/environment')
def environment():
    return jsonify({"environment": get_environment()})


@app.route('/metrics')
def metrics():
    return Response(generate_latest(), content_type=CONTENT_TYPE_LATEST)


@app.route('/simulate-error')
def simulate_error():
    if os.environ.get('ENABLE_FAULT_INJECTION', 'false').lower() != 'true':
        return jsonify({"error": "not found"}), 404
    g.log_message = 'simulated fault injected'
    return jsonify({"error": "simulated failure"}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)