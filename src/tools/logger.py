import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[2] / 'logs'
LOG_DIR.mkdir(exist_ok=True, parents=True)
LOG_PATH = LOG_DIR / 'app.log'

logger = logging.getLogger('pr_buddy')
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    file_handler = logging.FileHandler(LOG_PATH, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(file_handler)


def ensure_trace_id(state):
    trace_id = state.get('trace_id')
    if not trace_id:
        trace_id = str(uuid.uuid4())
        state['trace_id'] = trace_id
    return trace_id


def log_event(state, event, node, **details):
    payload = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'trace_id': ensure_trace_id(state),
        'event': event,
        'node': node,
        'details': details or {}
    }
    logger.info(json.dumps(payload, ensure_ascii=False))


def log_error(state, node, error):
    payload = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'trace_id': ensure_trace_id(state),
        'event': 'error',
        'node': node,
        'details': {
            'error': str(error)
        }
    }
    logger.info(json.dumps(payload, ensure_ascii=False))
