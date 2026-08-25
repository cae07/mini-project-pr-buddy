from pathlib import Path
from tools.report_tool import write_report
from langchain_google_genai import ChatGoogleGenerativeAI

from tools.memory_tool import (
    load_review_history,
    save_review_history
)

import json
import re

import os
from dotenv import load_dotenv

load_dotenv()

def load_diff(state):
    content = Path(
        state["file_path"]
    ).read_text(encoding="utf-8")

    return {
        "diff_content": content
    }

def validate_input(state):

    if not state["diff_content"].strip():
        raise ValueError(
            "Arquivo vazio"
        )

    return state

llm = ChatGoogleGenerativeAI(
    model=os.getenv(
        "GEMINI_MODEL",
        "GEMINI_MODEL"
    ),
    google_api_key=os.getenv(
        "GOOGLE_API_KEY"
    ),
    temperature=0
)

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

    path = write_report(
        state["summary"],
        state["risks"],
        state["recommendation"]
    )

    return {
        "report_path": path
    }

def analyze_security(state):

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

# SUBSTITUIR analyze_quality POR ESTA VERSÃO

def analyze_quality(state):

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

def merge_analysis(state):

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

    return {
        "summary": summary,
        "risks": risks,
        "recommendation": recommendation
    }

def load_history(state):

    history = load_review_history()

    return {
        "review_history": history
    }

def save_history(state):

    save_review_history(
        summary=state["summary"],
        risks=state["risks"],
        recommendation=state["recommendation"]
    )

    return state