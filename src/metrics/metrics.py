import json
from datetime import datetime, timezone
from pathlib import Path

METRICS_DIR = Path(__file__).resolve().parents[2] / 'metrics'
METRICS_DIR.mkdir(exist_ok=True, parents=True)
METRICS_PATH = METRICS_DIR / 'metrics.json'


def persist_metrics(state):
    started_at = state.get('started_at')
    started = datetime.fromisoformat(started_at) if started_at else datetime.now(timezone.utc)
    finished_at = datetime.now(timezone.utc)
    execution_time = (finished_at - started).total_seconds()

    payload = {
        'timestamp': finished_at.isoformat(),
        'trace_id': state.get('trace_id', ''),
        'execution_time': float(execution_time),
        'recommendation': state.get('recommendation', ''),
        'total_risks': len(state.get('risks', []) or []),
        'prompt_tokens': int(state.get('prompt_tokens', 0) or 0),
        'completion_tokens': int(state.get('completion_tokens', 0) or 0),
        'total_tokens': int(state.get('total_tokens', 0) or 0),
    }

    METRICS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    return payload
