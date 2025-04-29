import os
import json
from pathlib import Path
from flask import Flask
from slackeventsapi import SlackEventAdapter
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

# Load .env
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Init Flask + Slack
app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ["SIGNING_SECRET"], "/slack/events", app)
client = WebClient(token=os.environ["SLACK_TOKEN"])
BOT_ID = client.auth_test()["user_id"]

# Load JSON data
with open("data.json") as f:
    candidates = json.load(f)

# Message handler
@slack_event_adapter.on("message")
def handle_message(payload):
    event = payload.get("event", {})
    user_id = event.get("user")
    channel_id = event.get("channel")
    text = event.get("text", "").strip().lower()

    if user_id == BOT_ID or user_id is None:
        return

    response_text = ""

    if text in ["hi", "hello"]:
        response_text = "👋 Hello! Send me a name or email to look up candidate info."
    elif text in ["bye", "exit"]:
        response_text = "👋 Goodbye! Let me know if you need anything else."
    else:
        match = None
        for c in candidates:
            if text in c["name"].lower() or text in c["email"].lower():
                match = c
                break
        if match:
            response_text = f"✅ *{match['name']}* ({match['role']}) — Status: *{match['status']}*"
        else:
            response_text = "❌ I couldn’t find anyone matching that. Try a different name or email."

    # Reply to user
    try:
        client.chat_postMessage(channel=channel_id, text=response_text)
    except SlackApiError as e:
        print("Slack error:", e.response['error'])

# Run Flask server
if __name__ == "__main__":
    app.run(port=5000, debug=True)
