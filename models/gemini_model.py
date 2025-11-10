import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

def query_gemini(prompt: str) -> str:
    try:
        model_name = "gemini-2.5-flash"
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )

        text = response.text.strip()
        return f"<strong>[Gemini-2.5-flash]</strong><br>{text}"
    except Exception as e:
        return f"Erro ao chamar modelo Gemini: {str(e)}"
