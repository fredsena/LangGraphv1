from langchain.agents import create_agent
from langchain.tools import tool
from langchain.agents.middleware import PIIMiddleware, SummarizationMiddleware

from langchain_openai import ChatOpenAI

modelV1 = ChatOpenAI(
    model="qwen/qwen3-vl-4b",
    base_url="http://127.0.0.1:1234/v1",
    temperature=0.0,
    api_key="lm-studio"
)

@tool(description="Confirmar inscricao na comunidade TOP HAWKS")
def confirmar_inscricao_comunidade() -> str:
    return f"Sua inscrição foi confirmada com sucesso! Agora você vai construir com IA"

prompt = """
Você é um assistente de matricula na comunidade TOP HAWKS.
A comunidade é para pessoas que querem construir soluções profissionais de sucesso.
"""

hawk = create_agent(
    model=modelV1,
    tools=[confirmar_inscricao_comunidade],
    system_prompt=prompt,
    middleware=[
        SummarizationMiddleware(
            model=modelV1,
            max_tokens_before_summary=1000,  # Ativa a sumarização quando o texto ultrapassa 1000 tokens
            messages_to_keep=5,  # Mantém os últimos 5 mensagens após a resumização
        ),
        PIIMiddleware("email", strategy="redact", apply_to_input=True),
    ],
)