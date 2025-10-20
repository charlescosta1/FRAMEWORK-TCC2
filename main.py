from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import shutil
import os
import pdfplumber
import ollama
from openai import OpenAI

# Cria a aplicação
app = FastAPI()

# Monta a pasta static
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configura templates Jinja
templates = Jinja2Templates(directory="templates")

# Cria pasta de uploads
UPLOAD_DIR = "uploads" 
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Variáveis globais para conteúdo do PDF
pdf_text = ""
pdf_tables = []
current_filename = ""

# Configuração da API GitHub Models
GITHUB_TOKEN = "Chave_aqui"
GITHUB_MODEL_DEFAULT = "openai/gpt-4o-mini"

client_openai = OpenAI(
    base_url="https://models.github.ai/inference",
    api_key=GITHUB_TOKEN
)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/chat/", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    global pdf_text, pdf_tables, current_filename 
    
    try:
        # Valida se é PDF
        if file.content_type != "application/pdf":
            return JSONResponse(
                {"error": "Por favor, envie um arquivo PDF válido"},
                status_code=400
            )
        
        # Salva o arquivo
        file_location = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Extrai texto e tabelas
        extracted_text = ""
        extracted_tables = []
        
        with pdfplumber.open(file_location) as pdf:
            for page in pdf.pages:
                extracted_text += page.extract_text() or ""
                tables = page.extract_tables()
                if tables:
                    extracted_tables.extend(tables)
        
        # Armazena globalmente
        pdf_text = extracted_text
        pdf_tables = extracted_tables
        current_filename = file.filename
        
        return JSONResponse({
            "success": True,
            "filename": file.filename,
            "message": "PDF carregado com sucesso!"
        })
    
    except Exception as e:
        return JSONResponse(
            {"error": f"Erro ao processar PDF: {str(e)}"},
            status_code=500
        )

def query_ollama(model_name: str, prompt: str) -> str:
    try:
        response = ollama.chat(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "Você é um assistente especializado em análise de documentos PDF. Responda de forma clara e concisa."
                },
                {"role": "user", "content": prompt},
            ]
        )
        return response["message"]["content"]
    except Exception as e:
        return f"Erro ao chamar Ollama: {str(e)}"

def query_github_openai(prompt: str, model_name: str = GITHUB_MODEL_DEFAULT) -> str:
    try:
        response = client_openai.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "Você é um assistente especializado em análise de documentos PDF. Responda de forma clara, concisa e use o menor número de tokens possível."
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=1500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erro ao chamar GitHub/OpenAI: {str(e)}"

@app.post("/chat/ask")
async def ask_model(question: str = Form(...), model: str = Form(...)):
    global pdf_text
    
    if not pdf_text:
        return JSONResponse(
            {"error": "Nenhum PDF foi carregado. Por favor, envie um PDF primeiro."},
            status_code=400
        )
    
    if not question.strip():
        return JSONResponse(
            {"error": "Por favor, digite uma pergunta."},
            status_code=400
        )
    
    # Limita o tamanho do contexto para melhor performance
    context_limit = 8000
    truncated_text = pdf_text[:context_limit]
    
    # Monta o prompt
    prompt = f"""Você está analisando o seguinte documento:

---
{truncated_text}
---

Pergunta do usuário: {question}

Por favor, responda com base no documento acima."""

    # Escolhe o modelo
    if model.lower().startswith("gpt-") or model.lower().startswith("openai/"):
        answer = query_github_openai(prompt, model_name=model)
    else:
        answer = query_ollama(model, prompt)
    
    return JSONResponse({"answer": answer})

@app.get("/api/current-pdf")
async def get_current_pdf():
    """Retorna informações do PDF atualmente carregado"""
    return JSONResponse({
        "filename": current_filename,
        "text_length": len(pdf_text),
        "tables_count": len(pdf_tables),
        "is_loaded": bool(pdf_text)
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)