from pathlib import Path
from tools.report_tool import write_report
from langchain_google_genai import ChatGoogleGenerativeAI

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

def approve_flow(state):
    return {
        "flow_status": "approved"
    }


def attention_flow(state):
    return {
        "flow_status": "attention"
    }


def block_flow(state):
    return {
        "flow_status": "blocked"
    }


def route_recommendation(state):
    recommendation = state["recommendation"]

    if recommendation == "APROVAR":
        return "approve"

    if recommendation == "BLOQUEAR":
        return "block"

    return "attention"