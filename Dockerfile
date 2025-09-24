# Usar a imagem oficial do Python 3.9
FROM python:3.9-slim

# Definir o diretório de trabalho dentro do container
WORKDIR /app

# Copiar o arquivo de dependências para o container
COPY requirements.txt .

# Instalar as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o resto do código do seu projeto para o container
COPY . .

# O Hugging Face Spaces expõe a porta 7860 por padrão
EXPOSE 7860

# Comando para iniciar a aplicação usando Gunicorn
# Isso vai procurar por uma variável 'app' dentro do arquivo 'app.py'
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "app:app"]