from pathlib import Path
from datetime import datetime
import json

MEMORY_FILE = Path(
    "data/reviews.json"
)


def load_review_history(
    limit: int = 5
):
    if not MEMORY_FILE.exists():
        return []

    try:
        data = json.loads(
            MEMORY_FILE.read_text(
                encoding="utf-8"
            )
        )

        return data[-limit:]

    except Exception:
        return []


def save_review_history(
    summary: str,
    risks: list,
    recommendation: str
):

    MEMORY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    history = load_review_history(
        limit=1000
    )

    history.append({
        "timestamp": datetime.utcnow().isoformat(),
        "summary": summary,
        "risks": risks,
        "recommendation": recommendation
    })

    MEMORY_FILE.write_text(
        json.dumps(
            history,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )