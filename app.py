from flask import Flask, jsonify, request
from datetime import datetime
import os
import socket

app = Flask(__name__)

START_TIME = datetime.utcnow()


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "message": "Welcome to the K8s Demo API",
        "status": "running",
        "hostname": socket.gethostname(),
        "version": "1.0.0"
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 200


@app.route("/info", methods=["GET"])
def info():
    uptime = (datetime.utcnow() - START_TIME).total_seconds()
    return jsonify({
        "hostname": socket.gethostname(),
        "uptime_seconds": round(uptime, 2),
        "pod_ip": os.environ.get("MY_POD_IP", "N/A"),
        "namespace": os.environ.get("MY_NAMESPACE", "default"),
        "version": "1.0.0"
    })


@app.route("/echo", methods=["POST"])
def echo():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No JSON body provided"}), 400
    return jsonify({
        "echo": data,
        "received_at": datetime.utcnow().isoformat() + "Z"
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
