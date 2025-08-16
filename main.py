# principais imports do FastAPI
from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# bibliotecas para manipulação de arquivos/pastas
import shutil
import os
import pdfplumber
import subprocess
import ollama

# cria a aplicação
app = FastAPI()

# monta a instância para a pasta static
app.mount("/static", StaticFiles(directory="static"), name="static")

# configura o caminho dos templates do Jinja (HTML)
templates = Jinja2Templates(directory="templates")

# configura e cria a pasta onde os arquivos PDF serão enviados, caso não exista é criada automaticamente 
UPLOAD_DIR = "uploads" 
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Variáveis globais para armazenar conteúdo do PDF
pdf_text = ""
pdf_tables = []

# rota da página inicial
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# rota para upload dos PDFs e extração com o pdfplumber
@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    global pdf_text, pdf_tables

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

    pdf_text = extracted_text
    pdf_tables = extracted_tables

    return RedirectResponse(url="/chat/", status_code=303)

    # retorno do JSON para testar se está extraindo o pdf
    #return {
    #    "filename": file.filename,
    #    "message": "Arquivo PDF enviado e processado com sucesso!",
    #    "text_excerpt": pdf_text,
    #    "tables_count": len(pdf_tables)
    #}

# rota para a parte de conversação com o modelo, sobre o PDF

@app.get("/chat/", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})
  

def query_ollama(model_name: str, prompt: str) -> str:
    try:
        response = ollama.chat(
            model=model_name, #<- desse modo não executa o DeepSeek,
            #model="llama3.1:8b",
            messages=[
                {"role": "system", "content": "Você é um assistente que responde perguntas sobre documentos PDF."},
                {"role": "user", "content": prompt},
            ]
        )
        return response["message"]["content"]
    except Exception as e:
        return f"Erro ao chamar Ollama: {e}"


# rota para a parte em que o modelo retorna uma resposta

@app.post("/chat/ask")
async def ask_model(question: str = Form(...), model: str = Form(...)):
    global pdf_text

    if not pdf_text:
        return JSONResponse({"error": "Nenhum PDF carregado"}, status_code=400)

    # monta o prompt baseado no conteúdo do PDF
    prompt = f"Baseando-se no seguinte documento:\n\n{pdf_text}\n\nPergunta: {question}"

    # chama o Ollama
    answer = query_ollama(model, prompt)

    return {"answer": answer}


