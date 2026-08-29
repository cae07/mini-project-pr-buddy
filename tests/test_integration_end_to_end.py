import json
import os
import sys
from pathlib import Path

os.environ.setdefault('LLM_PROVIDER', 'mcp')
os.environ.setdefault('MCP_URL', 'https://example.test/mcp')

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from graph import workflow
from graph.workflow import build_graph


class FakeLLMResponse:
    def __init__(self, payload):
        self.content = json.dumps(payload, ensure_ascii=False)


def test_integration_happy_path(monkeypatch):
    from graph import nodes

    def fake_llm_invoke(prompt, config=None):
        prompt_lower = prompt.lower()
        if 'especialista em segurança' in prompt_lower:
            return FakeLLMResponse({
                'summary': 'Sem riscos de segurança',
                'risks': []
            })
        if 'especialista em qualidade' in prompt_lower:
            return FakeLLMResponse({
                'summary': 'Sem riscos de qualidade',
                'risks': []
            })
        raise AssertionError(f'Prompt inesperado: {prompt[:120]}')

    monkeypatch.setattr(nodes.llm, 'invoke', fake_llm_invoke)
    monkeypatch.setenv('N8N_WEBHOOK_URL', 'https://example.test/webhook')

    webhook_calls = []

    def fake_webhook(**kwargs):
        webhook_calls.append(kwargs)

    monkeypatch.setattr(nodes.webhook_tool, 'send_review_notification', fake_webhook)

    graph = build_graph()
    file_path = Path(__file__).resolve().parents[1] / 'examples' / 'diff.txt'
    result = graph.invoke({'file_path': str(file_path)})

    assert result['summary'] == 'Security:\nSem riscos de segurança\n\nQuality:\nSem riscos de qualidade', result
    assert result['recommendation'] == 'APROVAR', result
    assert result['report_path'] == 'examples/review_report.md', result
    assert result['trace_id']
    assert webhook_calls, 'webhook should be called in the happy path'
    assert webhook_calls[0]['recommendation'] == 'APROVAR', webhook_calls


def test_integration_failure_path_retry_and_fallback(monkeypatch):
    from graph import nodes

    llm_attempts = {'count': 0}

    def fake_llm_invoke(prompt, config=None):
        llm_attempts['count'] += 1
        raise RuntimeError('LLM indisponível')

    def fake_security_node(state):
        response = nodes.invoke_llm_with_resilience(state, 'analyze_security', 'prompt de segurança')
        return {
            'security_summary': response['summary'],
            'security_risks': response['risks'],
        }

    def fake_quality_node(state):
        response = nodes.invoke_llm_with_resilience(state, 'analyze_quality', 'prompt de qualidade')
        return {
            'quality_summary': response['summary'],
            'quality_risks': response['risks'],
        }

    monkeypatch.setattr(workflow, 'analyze_security', fake_security_node)
    monkeypatch.setattr(workflow, 'analyze_quality', fake_quality_node)
    monkeypatch.setattr(nodes.llm, 'invoke', fake_llm_invoke)
    monkeypatch.setenv('N8N_WEBHOOK_URL', 'https://example.test/webhook')

    webhook_calls = []

    def fake_webhook(**kwargs):
        webhook_calls.append(kwargs)

    monkeypatch.setattr(nodes.webhook_tool, 'send_review_notification', fake_webhook)

    graph = build_graph()
    file_path = Path(__file__).resolve().parents[1] / 'examples' / 'diff.txt'
    result = graph.invoke({'file_path': str(file_path)})

    assert llm_attempts['count'] >= 6, llm_attempts
    assert result['recommendation'] == 'ATENCAO', result
    assert 'llm indisponível' in ' '.join(result['risks']).lower(), result
    assert result['summary']
    assert result['report_path'] == 'examples/review_report.md', result
    assert result['trace_id']
    assert webhook_calls, 'webhook should still be called after fallback'
    assert webhook_calls[0]['recommendation'] == 'ATENCAO', webhook_calls
