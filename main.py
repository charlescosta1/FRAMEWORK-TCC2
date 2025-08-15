# principais imports do FastAPI
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# bibliotecas para manipulação de arquivos/pastas
import shutil
import os

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

# rota para upload dos PDFs
@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):

    # caminho onde o arquivo será salvo
    file_location = os.path.join(UPLOAD_DIR, file.filename)

    # abre e copia o conteúdo do arquivo que foi enviado
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # retorna uma resposta JSON simples apenas para confirmar o envio do PDF
    return {"filename": file.filename, "message": "Arquivo PDF enviado com sucesso!"}
