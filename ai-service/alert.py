import requests

WEBHOOK_URL = None  # Put Slack/Webhook URL here later


def send_alert(payload):
    print("ALERT TRIGGERED:")
    print(payload)

    if WEBHOOK_URL:
        try:
            requests.post(WEBHOOK_URL, json=payload)
        except Exception as e:
            print("Failed to send webhook:", e)