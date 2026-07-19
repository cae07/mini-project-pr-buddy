# PR Buddy

Agente de IA simples e funcional para apoiar a revisão de Pull Requests usando **LangGraph** e **Gemini 2.5 Flash**.

O objetivo do projeto é automatizar uma etapa comum do ciclo de desenvolvimento: analisar mudanças de código a partir de um arquivo de entrada e gerar um relatório técnico estruturado com resumo, riscos e recomendação final.

---

## Visão Geral

O **PR Buddy** recebe um arquivo com o conteúdo de um Pull Request, como um `diff.txt`, valida a entrada, analisa o conteúdo com apoio de uma LLM e gera um relatório em Markdown.

A aplicação foi criada como mini-projeto avaliativo da disciplina **IA para Desenvolvedores**, com foco em agentes de IA, uso de estado, ferramentas, contexto e fluxo com LangGraph.

---

## Problema Escolhido

Revisões de Pull Requests são atividades importantes, mas podem ser demoradas e inconsistentes quando feitas apenas manualmente.

Durante uma revisão, alguns pontos podem passar despercebidos, como:

- ausência de testes;
- mudanças sem documentação;
- alterações em arquivos sensíveis;
- riscos de segurança;
- impacto em funcionalidades existentes;
- descrição insuficiente do Pull Request.

O **PR Buddy** não substitui a revisão humana, mas atua como apoio para identificar pontos de atenção de forma rápida e padronizada.

---

## Objetivo do Agente

O agente tem como objetivo analisar um arquivo contendo alterações de código e gerar uma recomendação estruturada para apoiar a revisão do Pull Request.

A recomendação final pode ser:

- `APROVAR`: quando não forem encontrados riscos relevantes;
- `ATENCAO`: quando existirem pontos que precisam de revisão;
- `BLOQUEAR`: quando forem encontrados riscos críticos ou problemas importantes.

---

## Entrada Esperada

A entrada principal da aplicação é um arquivo de texto contendo o conteúdo do Pull Request.

Exemplo:

```text
examples/diff.txt
```

Exemplo de conteúdo:

```txt
+ Added authentication endpoint
- No tests added
+ Updated login page
```

---

## Saída Produzida

A aplicação gera uma resposta no terminal e também cria um relatório em Markdown.

Exemplo de relatório gerado:

```md
# Review Report

## Summary
Resumo da análise realizada pelo agente.

## Risks
- Risco identificado 1
- Risco identificado 2

## Recommendation
ATENCAO
```

Arquivo gerado:

```text
examples/review_report.md
```

---

## Fluxo da Solução com LangGraph

O fluxo do agente foi implementado com **LangGraph**, utilizando um grafo de estados para organizar as etapas de execução.

Fluxo geral:

```text
Entrada do usuário
      ↓
Leitura do arquivo
      ↓
Validação da entrada
      ↓
Análise com LLM
      ↓
Geração do relatório
      ↓
Resposta final estruturada
```

---

## Por que esta solução é um agente?

A solução pode ser considerada um agente porque possui:

- objetivo claro: revisar Pull Requests;
- entrada definida: arquivo com diff ou descrição das mudanças;
- uso de estado compartilhado durante a execução;
- etapas organizadas em nós com LangGraph;
- integração com ferramenta real;
- uso de contexto para apoiar a análise;
- geração de saída estruturada e útil para o usuário.

---

## Estrutura do Projeto

```text
pr-buddy/
│
├── src/
│   ├── app.py
│   │
│   ├── graph/
│   │   ├── state.py
│   │   ├── nodes.py
│   │   └── workflow.py
│   │
│   └── tools/
│       └── report_tool.py
│
├── examples/
│   └── diff.txt
│
├── docs/
│   └── prompts.md
│
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Tecnologias Utilizadas

- Python
- LangGraph
- LangChain
- Google Gemini via `langchain-google-genai`
- Python Dotenv
- Markdown para geração do relatório

---

## Requisitos

Antes de executar a aplicação, é necessário ter instalado:

- Python 3.10 ou superior;
- chave de API do Google Gemini;
- dependências listadas em `requirements.txt`.

---

## Instalação

Clone o repositório:

```bash
git clone <url-do-repositorio>
cd pr-buddy
```

Crie um ambiente virtual:

```bash
python -m venv .venv
```

Ative o ambiente virtual:

No Windows:

```bash
.venv\Scripts\activate
```

No Linux/macOS:

```bash
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

---

## Configuração das Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```text
pr-buddy/.env
```

Adicione sua chave da LLM no arquivo `.env`:

```env
GOOGLE_API_KEY=sua_chave_google_aqui
GEMINI_MODEL=gemini-2.5-flash
```

> Atenção: o arquivo `.env` não deve ser versionado no GitHub.

O projeto deve conter apenas o arquivo `.env.example` com nomes das variáveis, sem valores reais:

```env
GOOGLE_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
```

---

## Executando a Aplicação

Na raiz do projeto, execute:

```bash
python src/app.py
```

---

## Exemplo de Execução

Arquivo de entrada:

```text
examples/diff.txt
```

Conteúdo de exemplo:

```txt
+ Added authentication endpoint
- No tests added
+ Updated login page
```

Saída esperada no terminal:

```text
RESUMO
Alteração inclui novo endpoint de autenticação e atualização da tela de login.

RECOMENDACAO
ATENCAO

RELATORIO
examples/review_report.md
```

---

## Ferramenta Integrada

A aplicação utiliza uma ferramenta simples e real para geração de relatório.

A ferramenta é responsável por:

- receber o resumo da análise;
- receber a lista de riscos identificados;
- receber a recomendação final;
- gerar um arquivo Markdown com o resultado.

Arquivo responsável:

```text
src/tools/report_tool.py
```

Relatório gerado:

```text
examples/review_report.md
```

---

## Estado e Contexto

O estado do agente armazena informações importantes durante a execução do fluxo.

Exemplos de informações mantidas no estado:

- caminho do arquivo analisado;
- conteúdo do diff;
- resumo da análise;
- riscos encontrados;
- recomendação final;
- caminho do relatório gerado.

Arquivo responsável pelo estado:

```text
src/graph/state.py
```

---

## Validações Básicas

A aplicação realiza validações simples antes de processar a entrada.

Exemplos:

- verifica se o arquivo existe;
- verifica se o conteúdo não está vazio;
- evita processar entradas inválidas;
- pode ser expandida para limitar tamanho de arquivo ou bloquear dados sensíveis.

Essas validações ajudam a manter o uso da ferramenta mais controlado e seguro.

---

## Cuidados de Segurança

O projeto adota cuidados básicos para evitar exposição de dados sensíveis:

- não versiona o arquivo `.env`;
- utiliza `.env.example` apenas como modelo;
- ignora arquivos de ambiente no `.gitignore`;
- não coloca chaves de API diretamente no código;
- gera relatórios locais sem expor dados externos desnecessariamente.

---

## Prompts Utilizados

Os principais prompts utilizados no planejamento, implementação e melhoria do agente devem ser documentados em:

```text
docs/prompts.md
```

Esse arquivo pode conter prompts usados para:

- definir a ideia do projeto;
- estruturar o agente;
- implementar o fluxo com LangGraph;
- corrigir erros;
- melhorar a saída estruturada;
- documentar o projeto.

---

## Decisões Técnicas

Principais decisões adotadas no projeto:

1. **Uso de LangGraph**  
   Escolhido para representar o fluxo do agente com estado, nós e conexões.

2. **Uso de Gemini 2.5 Flash**  
   Escolhido como modelo de LLM por ser uma opção rápida e suficiente para análise textual simples.

3. **Entrada via arquivo local**  
   Mantém a demonstração simples e evita dependência de integrações externas complexas.

4. **Relatório em Markdown**  
   Facilita leitura, versionamento e demonstração do resultado.

5. **Validação básica antes da análise**  
   Evita processar entradas vazias ou inválidas.

---

## Limitações da Solução

Esta é uma versão simples para fins acadêmicos. Algumas limitações conhecidas:

- não acessa Pull Requests reais de plataformas como GitHub ou Azure DevOps;
- não executa testes automatizados;
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
