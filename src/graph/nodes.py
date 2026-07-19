from pathlib import Path
from tools.report_tool import write_report
from langchain_google_genai import ChatGoogleGenerativeAI

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
    model="gemini-2.5-flash"
)

def analyze_pr(state):

    prompt = f"""
Você é um revisor de código.

Analise o diff abaixo.

Retorne:

1. Resumo
2. Lista de riscos
3. Recomendação:
   APROVAR
   ATENCAO
   BLOQUEAR

Diff:
{state['diff_content']}
"""

    response = llm.invoke(prompt)

    text = response.content

    recommendation = "ATENCAO"

    if "BLOQUEAR" in text:
        recommendation = "BLOQUEAR"
    elif "APROVAR" in text:
        recommendation = "APROVAR"

    return {
        "summary": text,
        "risks": [],
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
