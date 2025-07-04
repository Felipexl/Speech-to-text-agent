# Usa imagem leve com Python
FROM python:3.11-slim

# Cria diretório de trabalho
WORKDIR /app

# Copia os arquivos
COPY . .

# Instala dependências
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Expõe a porta do FastAPI
EXPOSE 8000

# Entrypoint padrão
CMD ["python", "agent_server.py"]
