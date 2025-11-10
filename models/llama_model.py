import ollama

def query_llama(prompt: str) -> str:
    """
    Envia o prompt para o modelo LLaMA (local, via Ollama).
    """
    try:
        response = ollama.chat(
            model="llama3.1:8b",
            messages=[
                {"role": "system", "content": "Você é um assistente especializado em análise de documentos PDF. Responda de forma clara e concisa."},
                {"role": "user", "content": prompt},
            ]
        )
        content = response["message"]["content"].strip()
        return f"<strong>[LLaMA 3.1]</strong><br>{content}"
    except Exception as e:
        return f"Erro ao chamar modelo LLaMA: {str(e)}"
