# LangChain 1.0 Agent

Este repositório utiliza o novo **LangChain 1.0** e **LangGraph 1.0** para criar agentes de IA avançados.

Quer avançar na construção de soluções de IA? https://www.rhawk.pro/comunidade

## Pré-requisitos

- Python 3.10 ou superior
- Chaves de API necessárias (veja abaixo)

## Chaves de API Necessárias

Este projeto requer as seguintes chaves de API:

- **OPENAI_API_KEY**: Chave de API da OpenAI para acesso aos modelos GPT
  - Obtenha em: https://platform.openai.com/api-keys
  
- **LANGSMITH_API_KEY**: Chave de API do LangSmith para observabilidade e monitoramento
  - Obtenha em: https://smith.langchain.com/  (gratuito)

## Configuração

### 1. Crie um ambiente virtual

```bash
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente

Copie o arquivo `.env.example` para `.env` e preencha com suas chaves de API:

```bash
cp .env.example .env
```

Edite o arquivo `.env` e adicione suas chaves:

```
OPENAI_API_KEY="sua-chave-openai-aqui"
LANGSMITH_API_KEY="sua-chave-langsmith-aqui"
```

## Estrutura do Projeto

```
langchain1.0/
├── src/
│   └── agente.py          # Definição do agente
├── langgraph.json         # Configuração do LangGraph
├── requirements.txt       # Dependências do Python
├── .env.example          # Template de variáveis de ambiente
└── README.md             # Este arquivo
```

## Sobre o Agente

O agente implementado (`hawk`) é um assistente de matrícula para a comunidade TOP HAWKS, que ajuda pessoas interessadas em adquirir conhecimento sobre IA e construir soluções profissionais.

### Funcionalidades

- **Ferramenta de confirmação**: Confirma inscrições na comunidade
- **Middleware de Sumarização**: Mantém conversas longas gerenciáveis
- **Middleware PII**: Protege informações sensíveis como emails
- **Modelo GPT-4.1**: Você pode trocar pelo modelo que quiser

## Como Executar

### Executar o LangGraph API Server

Na raiz do projeto, execute:
```bash
langgraph dev
```

O servidor será iniciado e estará disponível para receber requisições.

### Testar o Agente

Você pode testar o agente através da interface do LangGraph Studio ou fazendo requisições HTTP para o servidor.

## Principais Dependências

- **langchain**: 1.0.2
- **langgraph**: 1.0.1
- **langchain-openai**: 1.0.1


## Desenvolvimento

Para desenvolver e adicionar novas funcionalidades:

1. Edite o arquivo `src/agente.py`
2. Adicione novas ferramentas usando o decorador `@tool`
3. Configure middlewares adicionais conforme necessário
4. Teste localmente com `langgraph dev`

## Configuração do LangGraph

O arquivo `langgraph.json` define:
- **dependencies**: Dependências locais do projeto
- **graphs**: Mapeamento dos grafos disponíveis
- **env**: Arquivo de variáveis de ambiente

## Segurança

- Nunca commite o arquivo `.env` com suas chaves de API
- Use o arquivo `.env.example` como template
- Mantenha suas chaves seguras e privadas
- O middleware PII ajuda a proteger dados sensíveis


## Licença

Tutorial construído para estudos. Uma cortesia da [rhawk.pro](https://www.rhawk.pro) e da comunidade Top Hawks.
