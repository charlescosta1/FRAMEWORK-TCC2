import ollama

def query_deepseek(prompt: str) -> str:
    """
    Envia o prompt para o modelo DeepSeek (local, via Ollama).
    """
    try:
        response = ollama.chat(
            model="deepseek-r1:8b",
            messages=[
                {"role": "system", "content": "Você é um assistente especializado em análise de documentos PDF. Não tente deixar o texto bonito utilizando negrito, itálico, etc."},
                {"role": "user", "content": prompt},
            ]
        )

        content = response["message"]["content"]

        # remover as tags think
        if "<think>" in content:
            content = content.split("</think>")[-1].strip()

        return f"<strong>[DeepSeek R1]</strong><br>{content}"
    
    except Exception as e:
        return f"Erro ao chamar modelo DeepSeek: {str(e)}"
