import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from tools.log_analyzer import analyze_log_file


def test_log_analyzer_detects_recurring_failures(tmp_path):
    logs_dir = tmp_path / 'logs'
    reports_dir = tmp_path / 'reports'
    logs_dir.mkdir()
    reports_dir.mkdir()

    log_path = logs_dir / 'app.log'
    lines = [
        {'timestamp': '2026-08-29T00:00:00Z', 'trace_id': 'trace-1', 'event': 'workflow_started', 'node': 'orchestrator'},
        {'timestamp': '2026-08-29T00:00:01Z', 'trace_id': 'trace-2', 'event': 'error', 'node': 'parser', 'details': {'error': 'timeout'}},
        {'timestamp': '2026-08-29T00:00:02Z', 'trace_id': 'trace-3', 'event': 'error', 'node': 'parser', 'details': {'error': 'timeout'}},
        {'timestamp': '2026-08-29T00:00:03Z', 'trace_id': 'trace-4', 'event': 'error', 'node': 'validator', 'details': {'error': 'bad input'}},
        {'timestamp': '2026-08-29T00:00:04Z', 'trace_id': 'trace-5', 'event': 'workflow_finished', 'node': 'orchestrator'}
    ]
    log_path.write_text('\n'.join(json.dumps(item, ensure_ascii=False) for item in lines) + '\n', encoding='utf-8')

    report_path = analyze_log_file(log_path, reports_dir / 'anomaly_report.json')

    assert report_path.exists()

    report = json.loads(report_path.read_text(encoding='utf-8'))
    assert report['total_events'] == 5
    assert report['total_failures'] == 3
    assert report['anomalies_detected'] is True
    assert report['recurring_failures'] == [
        {
            'node': 'parser',
            'event': 'error',
            'occurrences': 2,
        }
    ]
