import requests


def send_review_notification(
    webhook_url: str,
    trace_id: str,
    summary: str,
    recommendation: str,
    risks: list
):
    payload = {
        "trace_id": trace_id,
        "summary": summary,
        "recommendation": recommendation,
        "risks": risks
    }

    requests.post(
        webhook_url,
        json=payload,
        timeout=5
    )