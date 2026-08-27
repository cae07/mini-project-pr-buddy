import json
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from graph.workflow import build_graph


def test_metrics_are_persisted_with_started_at_and_tokens():
    graph = build_graph()
    file_path = Path(__file__).resolve().parents[1] / 'examples' / 'diff.txt'

    result = graph.invoke({
        'file_path': str(file_path)
    })

    assert 'started_at' in result
    assert result['started_at']

    metrics_path = Path(__file__).resolve().parents[1] / 'metrics' / 'metrics.json'
    assert metrics_path.exists(), metrics_path

    payload = json.loads(metrics_path.read_text(encoding='utf-8'))
    assert payload['trace_id'] == result['trace_id']
    assert payload['recommendation'] == result['recommendation']
    assert payload['execution_time'] >= 0
    assert payload['total_risks'] >= 0
    assert payload['prompt_tokens'] == 0
    assert payload['completion_tokens'] == 0
    assert payload['total_tokens'] == 0
