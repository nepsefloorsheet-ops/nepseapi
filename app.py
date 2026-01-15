from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

API_URL = "https://nepselytics-6d61dea19f30.herokuapp.com/api/nepselytics/live-nepse"

@app.route("/api/live-nepse")
def live_nepse():
    try:
        r = requests.get(API_URL, timeout=10)
        r.raise_for_status()
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def index():
    return send_from_directory(os.getcwd(), "index.html")
