# PR Buddy

Agente de análise de Pull Requests baseado em LangGraph e Google Gemini. Recebe um `diff` (arquivo de alterações), executa validações, análises paralelas e consolida uma saída estruturada composta por resumo, riscos e recomendação, além de gerar um relatório em Markdown.

---

## 1. Visão Geral

O projeto converte um arquivo de diff em uma análise automatizada para apoiar revisões de código. O fluxo inclui validação, verificações de segurança (prompt injection guard), análises paralelas (segurança + qualidade), consolidação, e geração de relatório. Integração opcional com um fluxo low-code via webhook n8n está disponível.

---

## 2. Arquitetura

- Entrada: [examples/diff.txt](examples/diff.txt)
- Orquestração: `src/graph/workflow.py` (grafo LangGraph)
- Nós / Ferramentas: `src/graph/nodes.py` (validação, análise LLM, paralelização, fallback)
- Estado tipado: `src/graph/state.py`
- Ferramentas auxiliares: `src/tools/*` (ex.: `report_tool.py`, `webhook_tool.py`, `memory_tool.py`)
- Persistência de revisões: `data/reviews.json`

---

## 3. Fluxo do Workflow

Fluxo resumido:

1. Leitura do arquivo de entrada
2. Validação (existência, não-vazio)
3. Executa verificações paralelas: segurança (prompt injection + análise de risco) e qualidade
4. Consolida resultados (summary, risks, recommendation)
5. Persiste análise em `data/reviews.json`
6. Gera `examples/review_report.md` e logs
7. Envia notificação para webhook n8n quando configurado

---

## 4. Tecnologias Utilizadas

- Python 3.10+
- LangGraph (fluxo/estado)
- LangChain + langchain-google-genai (integração com Google Gemini)
- python-dotenv (carregar `.env`)
- n8n (integração via webhook, fluxo low-code)

---

## 5. Estrutura do Projeto

Veja a estrutura principal:

```
.
├── data/
│   └── reviews.json
├── docs/
│   └── prompts.md
├── examples/
│   ├── diff.txt
│   └── review_report.md    # saída de exemplo
├── src/
│   ├── app.py
│   ├── graph/
│   │   ├── nodes.py
│   │   ├── state.py
│   │   └── workflow.py
 │   ├── llm/
 │   │   └── client.py      # wrapper agnóstico para provedores LLM
│   └── tools/
│       ├── report_tool.py
│       ├── webhook_tool.py
│       └── memory_tool.py
├── tests/
│   ├── test_integration_end_to_end.py
│   ├── test_metrics.py
│   ├── test_observability.py
│   └── test_security_guard.py
└── requirements.txt
```

Observação: o projeto inclui um wrapper LLM em `src/llm/client.py` que unifica chamadas a diferentes provedores. O wrapper:

- Suporta `LLM_PROVIDER=google` (padrão) — usa `GOOGLE_API_KEY` e o cliente Google GenAI.
- Suporta `LLM_PROVIDER=groq` — requer `GROQ_API_KEY` e a biblioteca `langchain-groq` instalada.
- Suporta `LLM_PROVIDER=mcp` — envia prompts como `POST` para a URL definida em `MCP_URL` (requere `requests`).

A lógica do wrapper permite trocar de provedor apenas ajustando variáveis de ambiente, sem alterar `src/graph/nodes.py`.

---

## 6. Configuração do Ambiente

1. Criar e ativar um ambiente virtual:

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
```

2. Instalar dependências:

```bash
pip install -r requirements.txt
```

3. Criar `.env` a partir de `.env.example` e preencher variáveis (ver seção 7).

---

## 7. Variáveis de Ambiente

Adicione um arquivo `.env` na raiz com pelo menos:

```env
LLM_PROVIDER=groq|google
GOOGLE_API_KEY=seu_google_api_key
      ou
GROQ_API_KEY=seu_groq_api_key

GEMINI_MODEL=gemini-2.5-flash
      ou
GROQ_MODEL=llama-3.3-70b-versatile
N8N_WEBHOOK_URL=https://seu-n8n.example/webhook  # opcional
```

Não versionar o `.env`.

Observação sobre provedores LLM e opções de configuração:

- `LLM_PROVIDER`: define qual provedor será usado pelo wrapper LLM. Valores suportados: `google` (padrão), `groq`, `mcp`.
- Quando `LLM_PROVIDER=groq` use:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=seu_groq_api_key
GROQ_MODEL=groq-alpha   # opcional, ajuste conforme disponibilidade
```

- Quando `LLM_PROVIDER=mcp` (usar um MCP self-hosted ou remoto que aceite prompts JSON):

```env
LLM_PROVIDER=mcp
MCP_URL=https://seu-mcp/endpoint
```

O wrapper LLM incluído no projeto busca as variáveis acima e mapeia chamadas para:
- cliente Google GenAI quando `LLM_PROVIDER=google` (usa `GOOGLE_API_KEY`);
- cliente Groq quando `LLM_PROVIDER=groq` (requer `langchain-groq` instalado);
- uma chamada HTTP POST para `MCP_URL` quando `LLM_PROVIDER=mcp` (requer `requests`).

Dependências opcionais (instalar apenas se utilizar o provedor correspondente):

- `langchain-groq` — necessário para `groq`.
- `requests` — necessário para `mcp` (já adicionado ao `requirements.txt`).


---

## 8. Modo de Uso

Passos mínimos para executar a análise:

1. Instalar dependências (`requirements.txt`).
2. Configurar `.env` com `GOOGLE_API_KEY` e `GEMINI_MODEL`.
3. Colocar o diff de entrada em [examples/diff.txt](examples/diff.txt).
4. Executar a aplicação:

```bash
python src/app.py
```

O que é gerado:

- Relatório Markdown consolidado: [examples/review_report.md](examples/review_report.md)
- Registro persistente das revisões: `data/reviews.json` (append/atualização)
- Logs de execução: `logs/` (tempo de execução, eventos, erros)
- Métricas: `metrics/metrics.json` (tempos, sucessos/falhas, retries)

Quando ocorre envio para o n8n:

- Se a variável `N8N_WEBHOOK_URL` estiver configurada e o nó de notificação estiver habilitado no fluxo, após a consolidação da análise o sistema tenta enviar um POST ao webhook n8n com o payload de notificação.
- Em caso de falha no envio, o sistema aplica políticas de retry e fallback configuradas no fluxo.

---

## 9. Fluxo n8n

Fluxo esperado no n8n:

Aplicação
            ↓
Webhook n8n
            ↓
Prepare Data
            ↓
Build File Content
            ↓
Write File
            ↓
Respond

Dados enviados no `POST` para o webhook n8n (exemplo):

```json
{
      "trace_id": "<uuid>",
      "summary": "Resumo curto da análise",
      "recommendation": "ATENCAO",
      "risks": [
            "Risco A",
            "Risco B"
      ]
}
```

Observações:

- O n8n pode receber o payload, transformar e escrever arquivos (ex.: criar `review_report.md`) ou notificar canais externos.

---

## 10. Segurança

- Prompt Injection Guard: proteção e validações antes de enviar conteúdo para a LLM.
- Não versionar segredos (`.env`).
- Validações básicas de entrada (arquivo existente, não vazio).
- Logs e métricas não armazenam chaves sensíveis.

---

## 11. Observabilidade

- Logs organizados em `logs/` com eventos de workflow, erros e chamadas externas.
- Tracing/`trace_id` por execução para correlação entre logs, métricas e webhook.
- Métricas de execução em `metrics/metrics.json` (latência, número de retries, sucesso/erro por nó).

---

## 12. Métricas

Registro principal: `metrics/metrics.json`.

Exemplos de métricas coletadas:

- `execution_time_ms` — tempo total de execução
- `llm_call_count` — número de chamadas à LLM
- `retries` — número de tentativas em operações com retry
- `webhook_success` / `webhook_failure`

Essas métricas são usadas para observabilidade e para alimentar alertas no ambiente onde for necessário.

---

## 13. Resiliência

- Timeout e retry aplicados a chamadas externas (LLM, webhook).
- Fallbacks: quando a análise crítica falha, o sistema tenta gerar uma resposta parcial e registrar a falha para investigação.
- Execução paralela de checks para reduzir latência e isolar falhas.

---

## 14. Memória Persistente

- Revisões armazenadas em `data/reviews.json` com o formato mínimo:

```json
{
      "trace_id": "<uuid>",
      "timestamp": "2026-08-27T12:00:00Z",
      "summary": "...",
      "recommendation": "ATENCAO",
      "risks": ["..."],
      "report_path": "examples/review_report.md"
}
```

- Essa memória permite histórico de análises para auditoria e consultas posteriores.

---

## 15. Exemplo de Saída

- `examples/review_report.md` (trecho):

```md
# Review Report

## Summary
Alterações adicionam endpoint de autenticação; testes ausentes; alteração de rota crítica.

## Risks
- Ausência de testes automatizados
- Possível quebra de autenticação

## Recommendation
ATENCAO
```

- Payload enviado ao n8n (exemplo já mostrado na Seção 9).

---

## 16. Testes de Integração

O projeto contém testes de integração focados no comportamento ponta a ponta do fluxo LangGraph, sem depender de provedores LLM reais ou webhook externo real.

Cenários cobertos em `tests/test_integration_end_to_end.py`:

- Happy path: valida execução completa via `graph.invoke()`, mock da LLM, mock do webhook, preenchimento de `summary`, `recommendation`, `report_path` e conclusão do workflow sem exceções.
- Failure path: simula falha da LLM, verifica retry e fallback, exige `recommendation == "ATENCAO"`, confirma geração de relatório e continuidade do workflow sem interrupções.

---

## 17. Próximos Passos

- Melhorias em prompts e cobertura de checagens automatizadas.
- Normalização e enriquecimento das métricas para dashboards.
- Políticas de retenção e indexação de `data/reviews.json`.

---

Se quiser, eu posso (opcional):

- rodar a aplicação localmente com seu `.env` configurado; 
- executar um teste que demonstre o envio para n8n (mockado);
- ou atualizar o `examples/review_report.md` com um relatório gerado a partir do `examples/diff.txt`.


- não acessa Pull Requests reais de plataformas como GitHub ou Azure DevOps;
- não valida a compilação do projeto analisado;
- depende da qualidade do conteúdo fornecido no arquivo de entrada;
- a análise feita pela LLM deve ser revisada por um desenvolvedor.

---

## Possíveis Melhorias Futuras

- integração com API do GitHub;
- análise automática de arquivos modificados;
- classificação de severidade por categoria;
- geração de checklist de revisão;
- comparação com padrões internos de código;
- exportação do relatório em PDF;
- suporte a múltiplos arquivos de entrada.

---

## Checklist dos Requisitos da Atividade

- [x] Processo real definido
- [x] Agente com objetivo claro
- [x] Entrada e saída definidas
- [x] Implementação com LangGraph
- [x] Uso de StateGraph
- [x] Estado compartilhado
- [x] Nós e conexões entre etapas
- [x] Ferramenta integrada
- [x] Leitura de arquivo
- [x] Escrita de relatório
- [x] Contexto durante a execução
- [x] Validação básica
- [x] Uso de `.env` para chave de API
- [x] `.env.example` sem credenciais reais
- [x] README documentando execução e decisões
- [x] Registro de prompts em `docs/prompts.md`

---

## Autor

Projeto desenvolvido para o mini-projeto avaliativo da disciplina **IA para Desenvolvedores**.

---

## Licença

Este projeto possui finalidade acadêmica.
