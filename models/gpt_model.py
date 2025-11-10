import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o-mini"

client_openai = OpenAI(
    api_key=OPENAI_API_KEY
)

def query_gpt(prompt: str) -> str:
    try:
        response = client_openai.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Você é um assistente especializado em análise de documentos PDF. Seja claro e conciso e não é necessário utilizar texto em negrito ou itálico."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1500,
            temperature=0.7
        )
        return f"<strong>[GPT-4o Mini]</strong><br>{response.choices[0].message.content}"
        
    except Exception as e:
        return f"Erro ao chamar modelo GPT: {str(e)}"
