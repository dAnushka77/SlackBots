import os
import json
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from pathlib import Path

# Load token
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

SLACK_TOKEN = os.getenv("SLACK_TOKEN")
HEADERS = {
    "Authorization": f"Bearer {SLACK_TOKEN}",
    "Content-Type": "application/json"
}

# Init Flask
app = Flask(__name__)

# Load data from file
def load_candidates():
    with open("data.json") as f:
        return json.load(f)

# Lookup by name or email
def find_candidate(query):
    candidates = load_candidates()
    for c in candidates:
        if query.lower() in c["name"].lower() or query.lower() in c["email"].lower():
            return c
    return None

# Get user ID by email (to DM)
def get_user_id_by_email(email):
    url = f"https://slack.com/api/users.lookupByEmail?email={email}"
    res = requests.get(url, headers=HEADERS).json()
    return res["user"]["id"] if res.get("ok") else None

# POST endpoint to trigger Slack message
@app.route("/lookup", methods=["POST"])
def handle_lookup():
    data = request.json
    query = data.get("query")
    user_email = data.get("user_email")  # who should receive the DM

    if not query or not user_email:
        return jsonify({"error": "Missing query or user_email"}), 400

    result = find_candidate(query)
    user_id = get_user_id_by_email(user_email)

    if not user_id:
        return jsonify({"error": "Invalid Slack user email"}), 404

    if result:
        message = f"✅ *{result['name']}* ({result['role']}) — Status: *{result['status']}*"
    else:
        message = "❌ No matching candidate found."

    payload = {
        "channel": user_id,
        "text": message
    }

    res = requests.post("https://slack.com/api/chat.postMessage", headers=HEADERS, json=payload).json()
    return jsonify(res)

# Just a GET endpoint to test the server
@app.route("/", methods=["GET"])
def test():
    return "Slack bot server is running!", 200

if __name__ == "__main__":
    app.run(port=5000, debug=True)
