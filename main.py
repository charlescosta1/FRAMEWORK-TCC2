from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from models.llama_model import query_llama
from models.deepseek_model import query_deepseek
from models.gpt_model import query_gpt
from models.gemini_model import query_gemini

import shutil
import os
import pdfplumber
import asyncio


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
    
    # Limita o tamanho do contexto para tentar melhorar a performance
    # context_limit = 8000
    # truncated_text = pdf_text[:context_limit]

    # sem limitar o tamanho
    truncated_text = pdf_text
    
    # Salva o conteúdo em um .txt
    txt_filename = os.path.splitext(current_filename)[0] + ".txt"
    txt_path = os.path.join("uploads", txt_filename)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(pdf_text)

    # Monta o prompt
    prompt = f"""Você está analisando o seguinte documento:

---
{truncated_text}
---

Pergunta do usuário: {question}

Por favor, responda com base no documento acima."""
    
    # model_names = ["LLaMA 3.1", "DeepSeek R1", "GPT-4o Mini"] # usado apenas para armazenar os nomes dos modelos para deixar APENAS os nomes dos modelos em negrito na opção "todos".

# Escolhe o modelo com base no select do HTML. OBS: a escolha all (todos os modelos) gerará a resposta de cada modelo, então levará mais tempo para ser processada.
    model = model.lower()
    
    if "gemini" in model:
        answer = query_gemini(prompt)
    elif "gpt" in model or "openai/" in model:
        answer = query_gpt(prompt)  
    elif "llama" in model:
        answer = query_llama(prompt)
    elif "deepseek" in model:
        answer = query_deepseek(prompt)
    elif "all" in model:
        results = await asyncio.gather(
                asyncio.to_thread(query_gemini, prompt),
                asyncio.to_thread(query_gpt, prompt),
                asyncio.to_thread(query_llama, prompt),
                asyncio.to_thread(query_deepseek, prompt)
            )
        formatted = "<br><br>".join([f"<strong>{r.splitlines()[0]}</strong><br>{'<br>'.join(r.splitlines()[1:])}" for r in results])
        return JSONResponse({"answer": formatted})
    
    
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
    uvicorn.run(app, host="localhost", port=8000)