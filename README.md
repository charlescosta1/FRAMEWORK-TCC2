# 🧠 Framework de Engenharia de Prompt para Extração e Interpretação de Documentos PDF

## 🎓 Trabalho de Conclusão de Curso – Sistemas de Informação  
**Tema:** Modelos de IA Generativa e a Pratica da Engenharia de Prompt
**Autor:** Carlos Henrique e Charles Dayan 
**Instituição:** Universidade Federal de Sergipe (UFS)  

---

## 📘 Objetivo do Projeto

O objetivo geral deste projeto é **desenvolver um framework prático e acessível de engenharia de prompt** voltado para a **extração, interpretação e simplificação de conteúdos especializados presentes em documentos PDF**, utilizando **modelos de linguagem de grande escala (LLMs)**, com foco em **domínios técnicos e normativos**.  

A proposta visa **tornar o acesso a informações complexas mais ágil, acessível e confiável**, permitindo que usuários com diferentes níveis de familiaridade compreendam conteúdos técnicos — como editais, normas e regulamentos — por meio de **interação direta com modelos generativos**.

O framework permite comparar a performance de diferentes **modelos de IA generativa** — tanto **locais (via Ollama)** quanto **em nuvem (via APIs oficiais)** — oferecendo uma base prática para estudos e experimentação em **engenharia de prompt**.

---

## ⚙️ Tecnologias Utilizadas

### 🔹 Backend
- [FastAPI](https://fastapi.tiangolo.com/) – Framework Python para criação de APIs rápidas e assíncronas  
- [Uvicorn](https://www.uvicorn.org/) – Servidor ASGI de alto desempenho  
- [pdfplumber](https://github.com/jsvine/pdfplumber) – Extração de texto de documentos PDF  
- [Ollama](https://ollama.ai/) – Execução local de modelos LLM  
- [OpenAI API](https://platform.openai.com/docs/) – Integração com ChatGPT  
- [Google Generative AI](https://aistudio.google.com/) – Integração com Gemini  
- [DeepSeek API](https://www.deepseek.com/) – Modelo de IA avançado de código aberto  

### 🔹 Frontend
- HTML + Jinja2 (templating)  
- JavaScript (requisições assíncronas e interface dinâmica)  
- CSS

---

## ⚙️ Instalação e Execução

### 1️⃣ Pré-requisitos

Antes de rodar o projeto, garanta que você possui:

- **Python 3.10+**
- **pip** (gerenciador de pacotes)
- **[Ollama](https://ollama.ai/download)** instalado
- Modelos **DeepSeek** e **Llama** baixados via Ollama:
  ```bash
  ollama pull deepseek
  ollama pull llama3

⚠️ Caso o **Ollama** não esteja instalado, o framework funcionará apenas com os modelos via API, como Gemini e GPT.


### 2️⃣ Clonar o repositório

git clone https://github.com/charlescosta1/FRAMEWORK-TCC2.git

cd FRAMEWORK-TCC2

### 3️⃣ Instalar dependências

pip install -r requirements.txt

### 4️⃣ Configurar variáveis de ambiente

cp .env.example .env

## Exemplo de .env

- OPENAI_API_KEY=sua_chave_openai_aqui
- GEMINI_API_KEY=sua_chave_gemini_aqui

### 5️⃣ Executar o servidor
python -m uvicorn main:app --reload

Após iniciar, acesse no navegador:
http://localhost:8000
