import json
import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault('LLM_PROVIDER', 'mcp')
os.environ.setdefault('MCP_URL', 'https://example.test/mcp')

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))


@pytest.fixture(autouse=True)
def mock_external_dependencies(monkeypatch):
    """Mock LLM and webhook calls so no real HTTP is used during tests."""
    from llm.client import LLMClient

    class FakeLLMResponse:
        def __init__(self, payload):
            self.content = json.dumps(payload, ensure_ascii=False)

    def fake_llm_invoke(self_obj, prompt, config=None):
        prompt_lower = (prompt or '').lower()

        if 'especialista em segurança' in prompt_lower:
            return FakeLLMResponse({'summary': 'Sem riscos de segurança', 'risks': []})
        if 'especialista em qualidade' in prompt_lower:
            return FakeLLMResponse({'summary': 'Sem riscos de qualidade', 'risks': []})
        return FakeLLMResponse({'summary': 'Resposta simulada da LLM', 'risks': [], 'recommendation': 'ATENCAO'})

    def fake_send_review_notification(webhook_url, trace_id, summary, recommendation, risks):
        return {
            'webhook_url': webhook_url,
            'trace_id': trace_id,
            'summary': summary,
            'recommendation': recommendation,
            'risks': risks,
        }

    def fail_real_http(*args, **kwargs):
        raise AssertionError('Nenhuma chamada HTTP real deve ocorrer durante os testes.')

    monkeypatch.setattr(LLMClient, 'invoke', fake_llm_invoke)
    monkeypatch.setattr('tools.webhook_tool.send_review_notification', fake_send_review_notification)
    monkeypatch.setattr('requests.post', fail_real_http)

    return fake_send_review_notification
