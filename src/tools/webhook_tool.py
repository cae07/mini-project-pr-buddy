import requests


def send_review_notification(
    webhook_url: str,
    trace_id: str,
    summary: str,
    recommendation: str,
    risks: list
):
    print("Sending review notification via webhook")
    payload = {
        "trace_id": trace_id,
        "summary": summary,
        "recommendation": recommendation,
        "risks": risks
    }
    print(f"Webhook URL: {webhook_url}")
    print(f"Payload: {payload}")

    requests.post(
        webhook_url,
        json=payload,
        timeout=5
    )