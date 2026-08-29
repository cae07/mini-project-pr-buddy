import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

from llm.client import LLMClient
from metrics import persist_metrics
from tools import webhook_tool
from tools.extract_json_tool import extract_json
from tools.logger import ensure_trace_id, log_error, log_event
from tools.memory_tool import load_review_history, save_review_history
from tools.report_tool import write_report

MAX_DIFF_SIZE_BYTES = 200000
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "20"))
LLM_MAX_ATTEMPTS = max(1, int(os.getenv("LLM_MAX_ATTEMPTS", "3")))
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(previous|all)\s+instructions",
    r"system\s+prompt",
    r"reveal\s+prompt",
    r"override\s+instructions",
    r"bypass\s+security",
    r"\bact\s+as\b",
    r"developer\s+mode",
    r"jailbreak",
]

load_dotenv()

def load_diff(state):
    try:
        state["trace_id"] = ensure_trace_id(state)
        state["started_at"] = datetime.now(timezone.utc).isoformat()
        log_event(state, "workflow_started", "load_diff")

        content = Path(
            state["file_path"]
        ).read_text(encoding="utf-8")

        log_event(state, "load_diff", "load_diff", file_path=state["file_path"], bytes_count=len(content.encode("utf-8")))

        return {
            "trace_id": state["trace_id"],
            "started_at": state["started_at"],
            "diff_content": content
        }
    except (
        TimeoutError,
        ValueError,
        requests.RequestException,
    ) as exc:
        log_error(state, "load_diff", exc)
        raise


def validate_input(state):
    try:
        state["trace_id"] = ensure_trace_id(state)
        log_event(state, "validate", "validate_input")
        diff_content = state.get("diff_content")

        if not isinstance(diff_content, str):
            raise TypeError("Tipo de entrada inválido")

        if not diff_content.strip():
            raise ValueError("Arquivo vazio")

        if len(diff_content.encode("utf-8")) > MAX_DIFF_SIZE_BYTES:
            raise ValueError("Arquivo excede o tamanho máximo permitido")

        if "\x00" in diff_content or re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", diff_content):
            raise ValueError("Conteúdo não textual ou inválido")

        printable_ratio = (
            sum(ch.isprintable() or ch in "\n\r\t" for ch in diff_content)
            / max(len(diff_content), 1)
        )
        if printable_ratio < 0.85:
            raise ValueError("Conteúdo não textual ou inválido")

        state["diff_content"] = diff_content.strip()
        return state
    except (
        TimeoutError,
        ValueError,
        requests.RequestException,
    ) as exc:
        log_error(state, "validate_input", exc)
        raise


def security_guard(state):
    try:
        state["trace_id"] = ensure_trace_id(state)
        log_event(state, "validate", "security_guard")
        diff_content = state.get("diff_content", "")
        normalized = " ".join(diff_content.lower().split())
        risks = []

        for pattern in PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, normalized):
                risks.append(f"Prompt injection detectado: padrão '{pattern}'")

        if risks:
            summary = "Bloqueado por conteúdo malicioso: instruções de prompt injection foram detectadas."
            result = {
                "security_summary": summary,
                "security_risks": risks,
                "summary": summary,
                "risks": risks,
                "recommendation": "BLOQUEAR",
                "flow_status": "blocked",
            }
            log_event(state, "decision_made", "security_guard", recommendation="BLOQUEAR", flow_status="blocked", total_risks=len(risks))
            return result

        result = {
            "security_summary": "Validação de segurança concluída.",
            "security_risks": [],
            "flow_status": "safe",
        }
        log_event(state, "validate", "security_guard", status="safe")
        return result
    except (
        TimeoutError,
        ValueError,
        requests.RequestException,
    ) as exc:
        log_error(state, "security_guard", exc)
        raise


def route_security(state):
    return "blocked" if state.get("flow_status") == "blocked" else "safe"

llm = LLMClient()


def invoke_llm_with_resilience(state, node, prompt):
    last_error = None

    for attempt in range(1, LLM_MAX_ATTEMPTS + 1):
        try:
            return llm.invoke(prompt, config={"timeout": LLM_TIMEOUT_SECONDS})
        except Exception as exc: # noqa: BLE001
            last_error = exc
            fallback_activated = attempt >= LLM_MAX_ATTEMPTS
            log_event(
                state,
                "llm_failure",
                node,
                attempt=attempt,
                error=str(exc),
                fallback_activated=fallback_activated
            )
            if attempt >= LLM_MAX_ATTEMPTS:
                break

    fallback = {
        "summary": "Falha na análise",
        "risks": ["LLM indisponível"],
        "recommendation": "ATENCAO"
    }
    log_event(
        state,
        "llm_fallback",
        node,
        attempt=LLM_MAX_ATTEMPTS,
        error=str(last_error) if last_error else "LLM indisponível",
        fallback_activated=True
    )
    return fallback


def analyze_pr(state):
    diff_content = state["diff_content"]

    prompt = f"""
Você é um agente revisor de Pull Requests.

Analise o conteúdo abaixo e identifique possíveis riscos para revisão de código.

Critérios de análise:
- ausência de testes;
- alterações relacionadas a autenticação ou autorização;
- mudanças em arquivos de configuração;
- riscos de segurança;
- falta de documentação;
- impacto em funcionalidades existentes;
- clareza geral das alterações.

Retorne apenas um JSON válido no seguinte formato:

{{
  "summary": "Resumo objetivo das alterações analisadas.",
  "risks": [
    "Risco ou ponto de atenção identificado."
  ],
  "recommendation": "APROVAR | ATENCAO | BLOQUEAR"
}}

Regras:
- Use APROVAR apenas quando não houver riscos relevantes.
- Use ATENCAO quando houver pontos que precisam de revisão humana.
- Use BLOQUEAR quando houver risco crítico, ausência grave de validação ou possível exposição de dados sensíveis.
- Não inclua texto fora do JSON.

Conteúdo para análise:
{diff_content}
"""

    response = llm.invoke(prompt)
    raw_content = response.content.strip()

    # Remove blocos markdown caso a LLM retorne ```json ... ```
    cleaned_content = re.sub(
        r"^```json\s*|\s*```$",
        "",
        raw_content,
        flags=re.IGNORECASE | re.MULTILINE
    ).strip()

    try:
        result = json.loads(cleaned_content)
    except json.JSONDecodeError:
        result = {
            "summary": raw_content,
            "risks": [
                "Não foi possível converter a resposta da LLM para JSON válido."
            ],
            "recommendation": "ATENCAO"
        }

    summary = result.get("summary", "Resumo não informado.")
    risks = result.get("risks", [])
    recommendation = result.get("recommendation", "ATENCAO")

    if recommendation not in ["APROVAR", "ATENCAO", "BLOQUEAR"]:
        recommendation = "ATENCAO"

    if not isinstance(risks, list):
        risks = [str(risks)]

    return {
        "summary": summary,
        "risks": risks,
        "recommendation": recommendation
    }

def generate_report(state):
    try:
        state["trace_id"] = ensure_trace_id(state)
        path = write_report(
            state["summary"],
            state["risks"],
            state["recommendation"]
        )
        log_event(state, "report_generated", "generate_report", report_path=path)
        return {
            "report_path": path
        }
    except (
        TimeoutError,
        ValueError,
        requests.RequestException,
    ) as exc:
        log_error(state, "generate_report", exc)
        raise

def _collect_usage(response):
    usage = getattr(response, "usage_metadata", None)
    if not usage:
        usage = {}

    prompt_tokens = usage.get("prompt_token_count", usage.get("input_tokens", 0)) or 0
    completion_tokens = usage.get("completion_token_count", usage.get("output_tokens", 0)) or 0
    total_tokens = usage.get("total_token_count", prompt_tokens + completion_tokens) or 0

    return {
        "prompt_tokens": int(prompt_tokens),
        "completion_tokens": int(completion_tokens),
        "total_tokens": int(total_tokens)
    }


def analyze_security(state):
    try:
        state["trace_id"] = ensure_trace_id(state)
        log_event(state, "analyze_security", "analyze_security")

        diff_content = state["diff_content"]

        history = state.get(
            "review_history",
            []
        )

        history_context = json.dumps(
            history,
            ensure_ascii=False,
            indent=2
        )

        prompt = f"""
Você é um especialista em segurança.

Histórico das últimas análises:
{history_context}

Analise exclusivamente:

- autenticação
- autorização
- exposição de dados
- credenciais
- arquivos de configuração
- riscos de segurança

Retorne apenas JSON:

{{
  "summary": "...",
  "risks": []
}}

Diff:
{diff_content}
"""

        response = llm.invoke(prompt)
        usage = _collect_usage(response)
        state["prompt_tokens"] = int(state.get("prompt_tokens", 0)) + usage["prompt_tokens"]
        state["completion_tokens"] = int(state.get("completion_tokens", 0)) + usage["completion_tokens"]
        state["total_tokens"] = int(state.get("total_tokens", 0)) + usage["total_tokens"]

        cleaned = extract_json(
            response.content
        )

        result = json.loads(
            cleaned
        )

        return {
            "security_summary": result.get(
                "summary",
                ""
            ),
            "security_risks": result.get(
                "risks",
                []
            )
        }
    except (
        TimeoutError,
        ValueError,
        requests.RequestException,
    ) as exc:
        log_error(state, "analyze_security", exc)
        raise


def analyze_quality(state):
    try:
        state["trace_id"] = ensure_trace_id(state)
        log_event(state, "analyze_quality", "analyze_quality")

        diff_content = state["diff_content"]

        history = state.get(
            "review_history",
            []
        )

        history_context = json.dumps(
            history,
            ensure_ascii=False,
            indent=2
        )

        prompt = f"""
Você é um especialista em qualidade de software.

Histórico das últimas análises:
{history_context}

Analise exclusivamente:

- testes
- documentação
- impacto funcional
- clareza
- qualidade geral

Retorne apenas JSON:

{{
  "summary": "...",
  "risks": []
}}

Diff:
{diff_content}
"""

        response = llm.invoke(prompt)
        usage = _collect_usage(response)
        state["prompt_tokens"] = int(state.get("prompt_tokens", 0)) + usage["prompt_tokens"]
        state["completion_tokens"] = int(state.get("completion_tokens", 0)) + usage["completion_tokens"]
        state["total_tokens"] = int(state.get("total_tokens", 0)) + usage["total_tokens"]

        cleaned = extract_json(
            response.content
        )

        result = json.loads(
            cleaned
        )

        return {
            "quality_summary": result.get(
                "summary",
                ""
            ),
            "quality_risks": result.get(
                "risks",
                []
            )
        }
    except (
        TimeoutError,
        ValueError,
        requests.RequestException,
    ) as exc:
        log_error(state, "analyze_quality", exc)
        raise

def merge_analysis(state):
    try:
        state["trace_id"] = ensure_trace_id(state)
        log_event(state, "merge_analysis", "merge_analysis")

        risks = (
            state["security_risks"]
            + state["quality_risks"]
        )

        summary = f"""
Security:
{state['security_summary']}

Quality:
{state['quality_summary']}
""".strip()

        recommendation = "APROVAR"

        if risks:
            recommendation = "ATENCAO"

        security_text = (
            " ".join(state["security_risks"])
        ).lower()

        critical_terms = [
            "credencial",
            "token",
            "senha",
            "autorização",
            "authentication",
            "security"
        ]

        if any(
            term in security_text
            for term in critical_terms
        ):
            recommendation = "BLOQUEAR"

        result = {
            "summary": summary,
            "risks": risks,
            "recommendation": recommendation
        }
        log_event(state, "decision_made", "merge_analysis", recommendation=recommendation, flow_status="decision", total_risks=len(risks))
        return result
    except (
        TimeoutError,
        ValueError,
        requests.RequestException,
    ) as exc:
        log_error(state, "merge_analysis", exc)
        raise


def load_history(state):
    try:
        state["trace_id"] = ensure_trace_id(state)
        log_event(state, "load_history", "load_history")

        history = load_review_history()

        return {
            "review_history": history
        }
    except (
        TimeoutError,
        ValueError,
        requests.RequestException,
    ) as exc:
        log_error(state, "load_history", exc)
        raise


def approve_flow(state):
    try:
        state["trace_id"] = ensure_trace_id(state)
        result = {
            "summary": state.get("summary", "Aprovação concluída."),
            "risks": state.get("risks", []),
            "recommendation": "APROVAR",
            "flow_status": "approve"
        }
        log_event(state, "decision_made", "approve_flow", recommendation="APROVAR", flow_status="approve", total_risks=len(result["risks"]))
        return result
    except (
        TimeoutError,
        ValueError,
        requests.RequestException,
    ) as exc:
        log_error(state, "approve_flow", exc)
        raise


def attention_flow(state):
    try:
        state["trace_id"] = ensure_trace_id(state)
        result = {
            "summary": state.get("summary", "Revisão com atenção necessária."),
            "risks": state.get("risks", []),
            "recommendation": "ATENCAO",
            "flow_status": "attention"
        }
        log_event(state, "decision_made", "attention_flow", recommendation="ATENCAO", flow_status="attention", total_risks=len(result["risks"]))
        return result
    except (
        TimeoutError,
        ValueError,
        requests.RequestException,
    ) as exc:
        log_error(state, "attention_flow", exc)
        raise


def block_flow(state):
    try:
        state["trace_id"] = ensure_trace_id(state)
        risks = state.get("risks") or state.get("security_risks") or ["Conteúdo malicioso detectado."]
        summary = "Bloqueado por conteúdo malicioso ou instruções de prompt injection."
        result = {
            "summary": summary,
            "risks": risks,
            "recommendation": "BLOQUEAR",
            "flow_status": "blocked"
        }
        log_event(state, "decision_made", "block_flow", recommendation="BLOQUEAR", flow_status="blocked", total_risks=len(risks))
        return result
    except (
        TimeoutError,
        ValueError,
        requests.RequestException,
    ) as exc:
        log_error(state, "block_flow", exc)
        raise


def route_recommendation(state):
    try:
        state["trace_id"] = ensure_trace_id(state)
        recommendation = (state.get("recommendation") or "ATENCAO").upper()

        if recommendation == "APROVAR":
            log_event(state, "decision_made", "route_recommendation", recommendation="APROVAR", flow_status="approve", total_risks=len(state.get("risks", [])))
            return "approve"
        if recommendation == "BLOQUEAR":
            log_event(state, "decision_made", "route_recommendation", recommendation="BLOQUEAR", flow_status="blocked", total_risks=len(state.get("risks", [])))
            return "block"
        log_event(state, "decision_made", "route_recommendation", recommendation="ATENCAO", flow_status="attention", total_risks=len(state.get("risks", [])))
        return "attention"
    except (
        TimeoutError,
        ValueError,
        requests.RequestException,
    ) as exc:
        log_error(state, "route_recommendation", exc)
        raise


def send_notification(state):
    try:
        print("Sending notification...")
        state["trace_id"] = ensure_trace_id(state)
        webhook_url = os.getenv("N8N_WEBHOOK_URL", "").strip()

        if not webhook_url:
            log_event(
                state,
                "webhook_skipped",
                "send_notification",
                reason="N8N_WEBHOOK_URL not configured",
                recommendation=state.get("recommendation", "ATENCAO")
            )
            return state

        try:
            print("Invoking webhook...")
            webhook_tool.send_review_notification(
                webhook_url=webhook_url,
                trace_id=state["trace_id"],
                summary=state.get("summary", ""),
                recommendation=state.get("recommendation", "ATENCAO"),
                risks=state.get("risks", [])
            )
            log_event(
                state,
                "webhook_sent",
                "send_notification",
                webhook_url=webhook_url,
                recommendation=state.get("recommendation", "ATENCAO"),
                total_risks=len(state.get("risks", []))
            )
            return state
        except Exception as exc: # noqa: BLE001
            log_error(state, "send_notification", exc)
            log_event(
                state,
                "webhook_failed",
                "send_notification",
                webhook_url=webhook_url,
                recommendation=state.get("recommendation", "ATENCAO"),
                total_risks=len(state.get("risks", []))
            )
            return state
    except (
        TimeoutError,
        ValueError,
        requests.RequestException,
    ) as exc:
        log_error(state, "send_notification", exc)
        return state


def save_history(state):
    try:
        state["trace_id"] = ensure_trace_id(state)
        log_event(state, "history_saved", "save_history", recommendation=state["recommendation"], total_risks=len(state.get("risks", [])))

        save_review_history(
            summary=state["summary"],
            risks=state["risks"],
            recommendation=state["recommendation"]
        )

        persist_metrics(state)

        log_event(state, "workflow_finished", "save_history", recommendation=state["recommendation"], flow_status=state.get("flow_status", "unknown"))
        return state
    except (
        TimeoutError,
        ValueError,
        requests.RequestException,
    ) as exc:
        log_error(state, "save_history", exc)
        raise
