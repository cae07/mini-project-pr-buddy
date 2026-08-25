import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from graph.workflow import build_graph


def test_trace_id_and_json_logs_are_produced():
    graph = build_graph()
    file_path = Path(__file__).resolve().parents[1] / 'examples' / 'diff.txt'

    result = graph.invoke({
        'file_path': str(file_path)
    })

    assert 'trace_id' in result
    assert result['trace_id']

    log_path = Path(__file__).resolve().parents[1] / 'logs' / 'app.log'
    assert log_path.exists(), log_path

    lines = [json.loads(line) for line in log_path.read_text(encoding='utf-8').splitlines() if line.strip()]
    assert any(item.get('trace_id') == result['trace_id'] for item in lines)
    assert any(item.get('event') == 'workflow_started' for item in lines)
    assert any(item.get('event') == 'workflow_finished' for item in lines)
