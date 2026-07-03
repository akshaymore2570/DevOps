#!/usr/bin/env python3
"""
Vertoz Ad Analytics Application - CI/CD Demo
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, jsonify

app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Version info
VERSION = os.getenv("APP_VERSION", "1.0.0")
COMMIT = os.getenv("GIT_COMMIT", "local")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


@app.route("/")
def home():
    return jsonify(
        {
            "app": "Vertoz Ad Analytics",
            "version": VERSION,
            "environment": ENVIRONMENT,
            "status": "running",
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/health")
def health():
    return jsonify(
        {
            "status": "healthy",
            "version": VERSION,
            "commit": COMMIT,
            "environment": ENVIRONMENT,
        }
    )


@app.route("/api/status")
def status():
    return jsonify(
        {
            "status": "ok",
            "version": VERSION,
            "services": {
                "api": "running",
                "database": "connected",
                "cache": "connected",
            },
        }
    )


@app.route("/api/ad/<ad_id>/stats")
def ad_stats(ad_id):
    return jsonify(
        {
            "ad_id": ad_id,
            "impressions": 1250,
            "clicks": 85,
            "ctr": 6.8,
            "timestamp": datetime.now().isoformat(),
        }
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8084))
    app.run(host="0.0.0.0", port=port)
