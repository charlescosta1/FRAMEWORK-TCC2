# main.py

# Importações principais do FastAPI
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# Bibliotecas padrão do Python para manipulação de arquivos e pastas
import shutil
import os

# ----------------------------------------------------
# Criação da aplicação FastAPI
# ----------------------------------------------------
app = FastAPI()

# Monta a pasta "static" para servir arquivos estáticos (CSS, imagens, JS)
# Assim, qualquer arquivo colocado na pasta "static" pode ser acessado via /static/nome-do-arquivo
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configuração para indicar onde ficam os templates HTML
templates = Jinja2Templates(directory="templates")

# ----------------------------------------------------
# Configuração da pasta de uploads
# ----------------------------------------------------
UPLOAD_DIR = "uploads"  # Nome da pasta onde os arquivos enviados serão salvos
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Cria a pasta se ela não existir

# ----------------------------------------------------
# Rota principal (página inicial)
# ----------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Exibe a página inicial com o formulário de envio de PDF.
    O 'request' é obrigatório para o Jinja2Templates funcionar no FastAPI.
    """
    return templates.TemplateResponse("index.html", {"request": request})

# ----------------------------------------------------
# Rota para upload de PDF
# ----------------------------------------------------
@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Recebe um arquivo PDF enviado pelo formulário e salva na pasta 'uploads'.
    - file: arquivo enviado (UploadFile)
    """
    # Define o caminho completo onde o arquivo será salvo
    file_location = os.path.join(UPLOAD_DIR, file.filename)

    # Abre o arquivo no modo binário e copia o conteúdo do arquivo enviado
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Retorna uma resposta simples em JSON confirmando o envio
    return {"filename": file.filename, "message": "Arquivo PDF enviado com sucesso!"}
