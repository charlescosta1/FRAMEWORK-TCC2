# principais imports do FastAPI
from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# bibliotecas para manipulação de arquivos/pastas
import shutil
import os
import pdfplumber

# cria a aplicação
app = FastAPI()

# monta a instância para a pasta static
app.mount("/static", StaticFiles(directory="static"), name="static")

# configura o caminho dos templates do Jinja (HTML)
templates = Jinja2Templates(directory="templates")

# configura e cria a pasta onde os arquivos PDF serão enviados, caso não exista é criada automaticamente 
UPLOAD_DIR = "uploads" 
os.makedirs(UPLOAD_DIR, exist_ok=True)

# rota da página inicial
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):

    return templates.TemplateResponse("index.html", {"request": request})

# rota para upload dos PDFs e extração com o pdfplumber
@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):

    # caminho onde o arquivo será salvo
    file_location = os.path.join(UPLOAD_DIR, file.filename)

    # abre e copia o conteúdo do arquivo que foi enviado
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)


    # retorna uma resposta JSON simples apenas para confirmar o envio do PDF
   ###### return {"filename": file.filename, "message": "Arquivo PDF enviado com sucesso!"}

    # extrai o texto e tabelas usando pdfplumber
    extracted_text = ""
    extracted_tables = []

    with pdfplumber.open(file_location) as pdf:
        for page in pdf.pages:
            # extrair texto
            extracted_text += page.extract_text() or ""

            # extrair tabelas
            tables = page.extract_tables()
            if tables:
                extracted_tables.extend(tables)

    # Aqui você já poderia passar extracted_text e extracted_tables
    # para o Ollama ou GPT API
    # Por enquanto, vamos só retornar no JSON
    return {
        "filename": file.filename,
        "message": "Arquivo PDF enviado e processado com sucesso!",
        "text_excerpt": extracted_text[:500],  # primeiros 500 caracteres
        "tables_count": len(extracted_tables)
    }

@app.post("/chat/", response_class=HTMLResponse)
async def chat(request: Request, question: str = Form(...)):
    """
    Recebe a pergunta do usuário e envia para o modelo (Ollama ou GPT API)
    """
    global pdf_text, pdf_tables

    # Aqui você chamaria o Ollama ou GPT API
    # Por enquanto simula a resposta
    model_answer = f"Você perguntou: {question}. (Aqui a resposta do Ollama sobre o PDF iria.)"

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "text_excerpt": pdf_text[:500],
            "tables_count": len(pdf_tables),
            "user_question": question,
            "model_answer": model_answer
        }
    )