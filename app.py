from flask import Flask, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

API_URL = "https://nepselytics-6d61dea19f30.herokuapp.com/api/nepselytics/live-nepse"

@app.route("/api/live-nepse")
def live_nepse():
    """
    Fetch live NEPSE data and wrap it in {"code": null, "data": [...]}
    """
    try:
        r = requests.get(API_URL, timeout=10)
        r.raise_for_status()
        live_data = r.json()  # this is usually a list of stock objects
        return jsonify({
            "code": None,
            "data": live_data
        })
    except Exception as e:
        return jsonify({
            "code": "error",
            "message": str(e),
            "data": []
        }), 500

# Do NOT include app.run(), Render handles WSGI
