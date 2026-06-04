from flask import Flask, jsonify, request, Response
from datetime import datetime
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import os
import socket
import time

app = Flask(__name__)

START_TIME = datetime.utcnow()

# ── Prometheus Metrics ────────────────────────────────────────
# Counts total HTTP requests, broken down by method, endpoint, status code
REQUEST_COUNT = Counter(
    "flask_request_count_total",
    "Total HTTP request count",
    ["method", "endpoint", "http_status"]
)

# Measures how long each request takes
REQUEST_LATENCY = Histogram(
    "flask_request_latency_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"]
)

# Tracks how long the app has been running
APP_UPTIME = Gauge(
    "flask_app_uptime_seconds",
    "Application uptime in seconds"
)
# ─────────────────────────────────────────────────────────────


def track_metrics(method, endpoint, status, start):
    """Helper to record request count and latency after each request."""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, http_status=status).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start)


@app.route("/", methods=["GET"])
def index():
    start = time.time()
    response = jsonify({
        "message": "Welcome to the K8s Demo API",
        "status": "running",
        "hostname": socket.gethostname(),
        "version": "1.0.0"
    })
    track_metrics("GET", "/", 200, start)
    return response


@app.route("/health", methods=["GET"])
def health():
    start = time.time()
    response = jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 200
    track_metrics("GET", "/health", 200, start)
    return response


@app.route("/info", methods=["GET"])
def info():
    start = time.time()
    uptime = (datetime.utcnow() - START_TIME).total_seconds()
    APP_UPTIME.set(uptime)
    response = jsonify({
        "hostname": socket.gethostname(),
        "uptime_seconds": round(uptime, 2),
        "pod_ip": os.environ.get("MY_POD_IP", "N/A"),
        "namespace": os.environ.get("MY_NAMESPACE", "default"),
        "version": "1.0.0"
    })
    track_metrics("GET", "/info", 200, start)
    return response


@app.route("/echo", methods=["POST"])
def echo():
    start = time.time()
    data = request.get_json(silent=True)
    if not data:
        track_metrics("POST", "/echo", 400, start)
        return jsonify({"error": "No JSON body provided"}), 400
    response = jsonify({
        "echo": data,
        "received_at": datetime.utcnow().isoformat() + "Z"
    })
    track_metrics("POST", "/echo", 200, start)
    return response


@app.route("/metrics", methods=["GET"])
def metrics():
    """Prometheus scrape endpoint — returns all metrics in text format."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
