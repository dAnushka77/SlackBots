import os
import json
import requests
from flask import Flask
from slackeventsapi import SlackEventAdapter
from dotenv import load_dotenv
from pathlib import Path

# Load .env
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

SLACK_TOKEN = os.environ["SLACK_TOKEN"]
SIGNING_SECRET = os.environ["SIGNING_SECRET"]
HEADERS = {
    "Authorization": f"Bearer {SLACK_TOKEN}",
    "Content-Type": "application/json"
}

# Flask + Slack events setup
app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(SIGNING_SECRET, "/slack/events", app)

# Load file data
with open("data.json") as f:
    candidates = json.load(f)

# Get bot user ID (using Slack Web API)
def get_bot_id():
    url = "https://slack.com/api/auth.test"
    res = requests.post(url, headers=HEADERS).json()
    return res["user_id"]

BOT_ID = get_bot_id()

# Event handler
@slack_event_adapter.on("message")
def handle_message(payload):
    event = payload.get("event", {})
    user_id = event.get("user")
    channel_id = event.get("channel")
    text = event.get("text", "").strip().lower()

    if user_id == BOT_ID or user_id is None:
        return

    # Determine reply
    if text in ["hi", "hello"]:
        reply = "👋 Hello! Send me a name or email to look up candidate info."
    elif text in ["bye", "exit"]:
        reply = "👋 Goodbye! Let me know if you need anything else."
    else:
        match = next((c for c in candidates if text in c["name"].lower() or text in c["email"].lower()), None)
        if match:
            reply = f"✅ *{match['name']}* ({match['role']}) — Status: *{match['status']}*"
        else:
            reply = "❌ I couldn't find anyone matching that. Try a different name or email."

    # Post response using Slack's Web API (chat.postMessage)
    message_data = {
        "channel": channel_id,
        "text": reply
    }
    requests.post("https://slack.com/api/chat.postMessage", headers=HEADERS, json=message_data)

# Run Flask app
if __name__ == "__main__":
    app.run(port=5000, debug=True)
