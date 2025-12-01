from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from models.llama_model import query_llama
from models.deepseek_model import query_deepseek
from models.gpt_model import query_gpt
from models.gemini_model import query_gemini
from models.pdf_processor import learn_pdf, search, reset as reset_pdf_index
from datetime import datetime

import time
import shutil
import os
import pdfplumber
import asyncio
import glob

def reset_on_startup():
    global pdf_text, pdf_tables, current_filename

    pdf_text = ""
    pdf_tables = []
    current_filename = ""

    # Remove arquivos gerados
    for file in glob.glob("*.json"):
        os.remove(file)
    for file in glob.glob("*.index"):
        os.remove(file)
    for file in glob.glob("uploads/*"):
         os.remove(file)

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
    global pdf_text, current_filename

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

        # Extrai texto normal
        extracted_text = ""
        with pdfplumber.open(file_location) as pdf:
            for page in pdf.pages:
                extracted_text += page.extract_text() or ""

        # Armazena apenas como texto bruto (backup)
        pdf_text = extracted_text
        current_filename = file.filename

        # Etapa nova: aprendizado REAL do PDF
        n_chunks = learn_pdf(extracted_text, file.filename)

        return JSONResponse({
            "success": True,
            "filename": file.filename,
            "message": "PDF carregado e indexado com sucesso!",
            "chunks": n_chunks
        })

    except Exception as e:
        return JSONResponse(
            {"error": f"Erro ao processar PDF: {str(e)}"},
            status_code=500
        )


@app.post("/clear-context/")
async def clear_context():
    global pdf_text, current_filename

    try:
        pdf_text = ""
        current_filename = ""
        reset_pdf_index()
        return JSONResponse({"success": True, "message": "Contexto limpo com sucesso!"})
    except Exception as e:
        return JSONResponse({"error": f"Erro ao limpar contexto: {str(e)}"}, status_code=500)

    
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
    
    relevant_chunks = search(question)
    context = "\n\n".join(relevant_chunks)

    prompt = f"""
    Você é um sistema de perguntas e respostas baseado em documentos.

    Documento (somente trechos relevantes):
    ---
    {context}
    ---

    Pergunta do usuário:
    {question}

    Responda APENAS com base no conteúdo acima.
    """
        
# Escolhe o modelo com base no select do HTML. OBS: a escolha all (todos os modelos) gerará a resposta de cada modelo, então levará mais tempo para ser processada.
    model = model.lower()
    
    start_time = time.time()

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
        
        elapsed = time.time() - start_time
         
        formatted = "<br><br>".join([
            f"<strong>{r.splitlines()[0]}</strong><br>{'<br>'.join(r.splitlines()[1:])}"
            for r in results
        ])

        # Log para o modo ALL
        log_chat_interaction(question, formatted, "ALL MODELS", elapsed)
       
        return JSONResponse({"answer": formatted})    
    
    # modelos especificados → grava log normal
    elapsed = time.time() - start_time
    log_chat_interaction(question, answer, model, elapsed)

    return JSONResponse({"answer": answer})

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "chat_log.txt")

def log_chat_interaction(question, answer, model_name, elapsed_time):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_entry = (
        f"==============================\n"
        f"Data/Hora: {timestamp}\n"
        f"Modelo: {model_name}\n"
        f"Tempo gasto: {elapsed_time:.2f} segundos\n"
        f"\nPergunta:\n{question}\n"
        f"\nResposta:\n{answer}\n"
        f"==============================\n\n"
    )

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)


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