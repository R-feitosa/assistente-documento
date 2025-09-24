import os
import fitz  # PyMuPDF
import docx
import json
import uuid
import base64  # <-- NOVO import para converter imagens
from io import BytesIO # <-- NOVO import para manipular imagens em memória
import requests # <-- NOVO import para fazer chamadas de API
from PIL import Image
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

# --- NOVA CONFIGURAÇÃO PARA O OPENROUTER ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# --- A FUNÇÃO DE ANÁLISE FOI COMPLETAMENTE REESCRITA ---
def analisar_conteudo_com_ia(caminho_arquivo):
    """
    Analisa o conteúdo de um arquivo usando um modelo do OpenRouter.
    """
    # Escolha do modelo no OpenRouter. Existem muitos gratuitos!
    # "cognitivecomputations/cogvlm-chat-v1.1" é um bom modelo de visão gratuito.
    # Para apenas texto, "nousresearch/nous-hermes-2-llama-3-8b" é uma boa opção gratuita.
    MODELO_OPENROUTER = "google/gemma-3-27b-it:free"

    extensao = os.path.splitext(caminho_arquivo)[1].lower()
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost", # Opcional, mas recomendado pelo OpenRouter
        "X-Title": "Assistente Feitosa", # Opcional, mas recomendado pelo OpenRouter
    }

    prompt_base = """
    Analise o conteúdo a seguir e retorne as informações no formato JSON.
    1.  **tipo_documento**: Identifique o tipo do documento (ex: 'CONTRATO', 'NOTA_FISCAL', 'FOTO_PAISAGEM', 'GRAFICO', 'IDENTIDADE').
    2.  **titulo_resumido**: Crie um título curto e descritivo para o documento (ex: 'Contrato de Aluguel', 'Conta de Energia'). Máximo de 5 palavras.
    3.  **detalhe_principal**: Extraia o nome da pessoa principal ou da empresa principal mencionada no documento. Identificar os nomes das partes, reclamante/reclamado, exequente/executado, etc. Se não houver, extraia o endereço principal. Use este detalhe para o nome do arquivo.
    4.  **descricao**: Crie uma breve descrição do conteúdo. Se houver texto, resuma as informações mais importantes. Se for uma imagem sem texto, descreva a cena. Máximo de 50 palavras.
    Responda APENAS com o objeto JSON. Não inclua texto explicativo, a palavra 'json' nem ```. Sua resposta deve começar com { e terminar com }.
    """

    data_payload = {
        "model": MODELO_OPENROUTER,
        "messages": [],
        "max_tokens": 512, # Limite de tokens na resposta
    }

    try:
        if extensao in ['.pdf', '.docx']:
            texto = ""
            if extensao == '.pdf':
                with fitz.open(caminho_arquivo) as doc:
                    for pagina in doc:
                        texto += pagina.get_text()
            elif extensao == '.docx':
                doc = docx.Document(caminho_arquivo)
                for para in doc.paragraphs:
                    texto += para.text + '\n'
            
            if not texto or len(texto.strip()) < 20:
                 return json.loads('{"tipo_documento": "N/A", "titulo_resumido": "Conteúdo Ilegível", "descricao": "Não foi possível extrair texto suficiente do arquivo para análise."}')

            conteudo_final_prompt = prompt_base + "\n\n--- CONTEÚDO PARA ANÁLISE ---\n" + texto[:8000]
            data_payload["messages"] = [{"role": "user", "content": conteudo_final_prompt}]

        elif extensao in ['.jpg', '.jpeg', '.png']:
            img = Image.open(caminho_arquivo)
            
            # Converte a imagem para base64 para enviar na API
            buffered = BytesIO()
            img.save(buffered, format="JPEG") # Salva a imagem em memória
            base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

            data_payload["messages"] = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_base},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        },
                    ],
                }
            ]
        else:
            return None

        # Faz a chamada para a API do OpenRouter
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data_payload)
        response.raise_for_status() # Lança um erro se a resposta for mal-sucedida (ex: 4xx, 5xx)

        # Extrai a resposta da IA
        response_json = response.json()
        ia_content = response_json['choices'][0]['message']['content']
        
        # Limpa a resposta para garantir que seja um JSON
        json_response = ia_content.strip().replace('```json', '').replace('```', '')
        return json.loads(json_response)

    except requests.exceptions.RequestException as e:
        print(f"--- ERRO DE API (REQUESTS) ---")
        print(f"Erro ao chamar a API do OpenRouter: {e}")
        if e.response is not None:
            print(f"Status Code: {e.response.status_code}")
            # Tenta imprimir a resposta como JSON formatado para facilitar a leitura
            try:
                print("Resposta do servidor (JSON):")
                print(json.dumps(e.response.json(), indent=2))
            except json.JSONDecodeError:
                print("Resposta do servidor (Texto):")
                print(e.response.text)
        return None
    except Exception as e:
        print(f"--- ERRO DETALHADO NA ANÁLISE ---")
        print(f"Arquivo: {os.path.basename(caminho_arquivo)}")
        print(f"Tipo do Erro: {type(e).__name__}")
        print(f"Mensagem do Erro: {e}")
        return None


# Rota principal que serve a página HTML
@app.route('/')
def index():
    return render_template('index.html')

# Rota de upload MODIFICADA para usar a nova função
@app.route('/upload', methods=['POST'])
def upload_arquivo():
    if 'arquivo' not in request.files:
        return jsonify({"erro": "Nenhum arquivo enviado"}), 400

    arquivos = request.files.getlist('arquivo')
    resultados_finais = []

    for arquivo in arquivos:
        if arquivo.filename == '':
            continue

        filename_original = secure_filename(arquivo.filename)
        caminho_arquivo_original = os.path.join(app.config['UPLOAD_FOLDER'], filename_original)
        arquivo.save(caminho_arquivo_original)

        resultado_ia = analisar_conteudo_com_ia(caminho_arquivo_original)
        
        if resultado_ia is None:
            resultados_finais.append({"nome_original": filename_original, "erro": "Não foi possível analisar este arquivo."})
            os.remove(caminho_arquivo_original)
            continue
        
        extensao = os.path.splitext(filename_original)[1]
        tipo = resultado_ia.get('tipo_documento', 'DESCONHECIDO').upper().replace(' ', '_')
        titulo = resultado_ia.get('titulo_resumido', 'SEM_TITULO').replace(' ', '_').replace('/', '_')
        # Pega o novo campo "detalhe_principal" que pedimos para a IA
        detalhe = resultado_ia.get('detalhe_principal', 'SEM_DETALHE').replace(' ', '_').replace('/', '_')
        sufixo_unico = uuid.uuid4().hex[:6]
        
        # O 'tipo' foi removido do início do nome do ficheiro
        novo_nome = f"{titulo}-{detalhe}-{sufixo_unico}{extensao}"
        novo_nome_seguro = secure_filename(novo_nome)
        
        caminho_arquivo_renomeado = os.path.join(app.config['UPLOAD_FOLDER'], novo_nome_seguro)

        try:
            os.rename(caminho_arquivo_original, caminho_arquivo_renomeado)
        except OSError as e:
            print(f"Erro ao renomear arquivo: {e}")
            resultados_finais.append({"nome_original": filename_original, "erro": "Não foi possível renomear o arquivo no servidor."})
            os.remove(caminho_arquivo_original)
            continue

        resultados_finais.append({
            "nome_original": filename_original,
            "novo_nome": novo_nome,
            "novo_nome_servidor": novo_nome_seguro,
            "descricao": resultado_ia.get('descricao', 'Nenhuma descrição gerada.')
        })

    return jsonify(resultados_finais)


@app.route('/download/<path:filename>')
def download_file(filename):
    """Rota para servir os arquivos renomeados para download."""
    try:
        return send_from_directory(
            app.config['UPLOAD_FOLDER'], 
            filename, 
            as_attachment=True
        )
    except FileNotFoundError:
        return "Arquivo não encontrado.", 404

if __name__ == '__main__':
    app.run(debug=True)