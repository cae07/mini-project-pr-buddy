import json
from collections import defaultdict
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_LOG_PATH = ROOT_DIR / 'logs' / 'app.log'
DEFAULT_REPORT_PATH = ROOT_DIR / 'reports' / 'anomaly_report.json'


def _resolve_path(path_value, default_path):
    path = Path(path_value) if path_value is not None else default_path
    if not path.is_absolute():
        path = ROOT_DIR / path
    return path


def _iter_json_lines(log_path):
    for line in log_path.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            yield payload


def analyze_log_file(log_path=DEFAULT_LOG_PATH, report_path=DEFAULT_REPORT_PATH):
    log_file = _resolve_path(log_path, DEFAULT_LOG_PATH)
    output_file = _resolve_path(report_path, DEFAULT_REPORT_PATH)

    if not log_file.exists():
        raise FileNotFoundError(f'Arquivo de log não encontrado: {log_file}')

    events = list(_iter_json_lines(log_file))
    total_events = len(events)
    error_events = [event for event in events if event.get('event') == 'error']
    total_failures = len(error_events)

    recurring_counter = defaultdict(int)
    for event in error_events:
        node = event.get('node', '')
        entry_event = event.get('event', '')
        recurring_counter[(node, entry_event)] += 1

    recurring_failures = [
        {
            'node': node,
            'event': event_name,
            'occurrences': occurrences,
        }
        for (node, event_name), occurrences in sorted(recurring_counter.items())
        if occurrences >= 2
    ]

    payload = {
        'total_events': total_events,
        'total_failures': total_failures,
        'anomalies_detected': bool(recurring_failures),
        'recurring_failures': recurring_failures,
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    return output_file


if __name__ == '__main__':
    analyze_log_file(DEFAULT_LOG_PATH, DEFAULT_REPORT_PATH)
    print(f'Análise concluída. Relatório gerado em: {DEFAULT_REPORT_PATH}')
