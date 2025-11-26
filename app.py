import os
import fitz  # PyMuPDF
import docx
import json
import uuid
import base64
from io import BytesIO
import requests
from PIL import Image
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import time

# Carrega as variáveis de ambiente
load_dotenv()

# --- CONFIGURAÇÃO ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def analisar_conteudo_com_ia(caminho_arquivo):
    """
    Analisa o conteúdo de um ficheiro, com capacidade de OCR para PDFs escaneados.
    Mantém os modelos visuais originais.
    """
    # MANTIDO: Os modelos originais que você solicitou
    modelos_para_tentar = [
        "google/gemma-3-27b-it:free",
        "openai/gpt-oss-20b:free"
    ]

    extensao = os.path.splitext(caminho_arquivo)[1].lower()
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://huggingface.co/spaces/Roneely/assistente-de-documentos",
        "X-Title": "Assistente Feitosa",
    }
    
    prompt_base = """
    Analise o conteúdo do(s) documento(s) a seguir e retorne as informações no formato JSON.
    1.  **tipo_documento**: Identifique o tipo do documento (ex: 'CONTRATO', 'NOTA_FISCAL', 'FOTO_PAISAGEM', 'GRAFICO', 'IDENTIDADE').
    2.  **titulo_resumido**: Crie um título curto e descritivo para o documento (ex: 'Contrato de Aluguel', 'Conta de Energia'). Máximo de 5 palavras.
    3.  **detalhe_principal**: Extraia o nome da pessoa principal ou da empresa principal mencionada no documento. Identificar os nomes das partes, reclamante/reclamado, exequente/executado, etc. Se não houver, extraia o endereço principal. Use este detalhe para o nome do ficheiro.
    4.  **descricao**: Crie uma breve descrição do conteúdo. Se houver texto, resuma as informações mais importantes. Se for uma imagem sem texto, descreva a cena. Máximo de 50 palavras.
    Responda APENAS com o objeto JSON. Não inclua texto explicativo, a palavra 'json' nem ```. A sua resposta deve começar com { e terminar com }.
    """

    for modelo in modelos_para_tentar:
        print(f"--- Tentando análise com o modelo: {modelo} ---")
        
        data_payload = { "model": modelo, "messages": [], "max_tokens": 1024 }

        try:
            # --- LÓGICA PARA PDF (TEXTO OU IMAGEM/OCR) ---
            if extensao == '.pdf':
                texto_extraido = ""
                with fitz.open(caminho_arquivo) as doc:
                    for pagina in doc:
                        texto_extraido += pagina.get_text()
                
                # MANTIDO: Lógica de OCR se tiver pouco texto
                if len(texto_extraido.strip()) < 100: 
                    print("--- PDF com pouco texto detetado. A processar com OCR. ---")
                    conteudo_para_ia = [{"type": "text", "text": prompt_base}]
                    with fitz.open(caminho_arquivo) as doc:
                        for i, pagina in enumerate(doc):
                            if i >= 5: 
                                print("--- AVISO: PDF tem mais de 5 páginas. A analisar apenas as 5 primeiras. ---")
                                break
                            pix = pagina.get_pixmap(dpi=150) 
                            img_bytes = pix.tobytes("jpeg")
                            base64_image = base64.b64encode(img_bytes).decode('utf-8')
                            conteudo_para_ia.append({
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                            })
                    data_payload["messages"] = [{"role": "user", "content": conteudo_para_ia}]
                else:
                    conteudo_final_prompt = prompt_base + "\n\n--- CONTEÚDO PARA ANÁLISE ---\n" + texto_extraido[:8000]
                    data_payload["messages"] = [{"role": "user", "content": conteudo_final_prompt}]

            # --- LÓGICA PARA DOCX ---
            elif extensao == '.docx':
                texto = ""
                doc = docx.Document(caminho_arquivo)
                for para in doc.paragraphs:
                    texto += para.text + '\n'
                
                if not texto or len(texto.strip()) < 20:
                    # Retorna um objeto de erro válido
                    return {"tipo_documento": "N/A", "titulo_resumido": "Conteudo Ilegivel", "descricao": "Não foi possível extrair texto suficiente."}

                conteudo_final_prompt = prompt_base + "\n\n--- CONTEÚDO PARA ANÁLISE ---\n" + texto[:8000]
                data_payload["messages"] = [{"role": "user", "content": conteudo_final_prompt}]
            
            # --- LÓGICA PARA IMAGENS ---
            elif extensao in ['.jpg', '.jpeg', '.png']:
                img = Image.open(caminho_arquivo)
                buffered = BytesIO()
                img.save(buffered, format="JPEG")
                base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

                data_payload["messages"] = [
                    { "role": "user", "content": [ {"type": "text", "text": prompt_base}, { "type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"} } ] }
                ]
            else:
                return None

            # --- CHAMADA API ---
            # MANTIDO: URL Correta
            response = requests.post("[https://openrouter.ai/api/v1/chat/completions](https://openrouter.ai/api/v1/chat/completions)", headers=headers, json=data_payload)
            response.raise_for_status()
            
            response_json = response.json()
            ia_content = response_json['choices'][0]['message']['content']
            json_limpo = ia_content.strip().replace('```json', '').replace('```', '')
            
            # --- CORREÇÃO IMPORTANTE AQUI ---
            # Verifica se a resposta é uma Lista ou um Dicionário para evitar o erro AttributeError
            try:
                dados_estruturados = json.loads(json_limpo)
                
                if isinstance(dados_estruturados, list):
                    if len(dados_estruturados) > 0:
                        print(f"--- AVISO: Modelo retornou uma LISTA. Convertendo para dicionário. ---")
                        return dados_estruturados[0] # Pega o primeiro item da lista
                    else:
                        print(f"--- AVISO: Lista vazia retornada pelo modelo. ---")
                        continue
                
                print(f"--- Análise bem-sucedida com o modelo: {modelo} ---")
                return dados_estruturados # Retorna o dicionário normal

            except Exception as e:
                print(f"--- Erro ao processar JSON do modelo {modelo}: {e} ---")
                continue

        except Exception as e:
            print(f"--- FALHA com o modelo {modelo}. Mensagem: {e} ---")
            continue

    print("--- ERRO: Todos os modelos falharam na análise. ---")
    return None

# --- ROTAS (Nenhuma mudança necessária aqui) ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_arquivo():
    if 'arquivo' not in request.files:
        return jsonify({"erro": "Nenhum ficheiro enviado"}), 400

    arquivos = request.files.getlist('arquivo')
    resultados_finais = []

    for arquivo in arquivos:
        if arquivo.filename == '':
            continue

        filename_original = secure_filename(arquivo.filename)
        caminho_arquivo_original = os.path.join(app.config['UPLOAD_FOLDER'], filename_original)
        arquivo.save(caminho_arquivo_original)

        resultado_ia = analisar_conteudo_com_ia(caminho_arquivo_original)
        
        # Tratamento de erro robusto
        if resultado_ia is None:
            resultados_finais.append({"nome_original": filename_original, "erro": "Não foi possível analisar este ficheiro."})
            if os.path.exists(caminho_arquivo_original):
                os.remove(caminho_arquivo_original)
            continue
        
        # Garante que resultado_ia é um dicionário antes de usar .get()
        if not isinstance(resultado_ia, dict):
             resultado_ia = {"titulo_resumido": "ERRO_FORMATO", "detalhe_principal": "ERRO", "descricao": "Erro de formato JSON"}

        extensao = os.path.splitext(filename_original)[1]
        titulo = resultado_ia.get('titulo_resumido', 'SEM_TITULO').replace(' ', '_').replace('/', '_')
        detalhe = resultado_ia.get('detalhe_principal', 'SEM_DETALHE').replace(' ', '_').replace('/', '_')
        sufixo_unico = uuid.uuid4().hex[:6]
        
        novo_nome = f"{titulo}-{detalhe}-{sufixo_unico}{extensao}"
        novo_nome_seguro = secure_filename(novo_nome)
        
        caminho_arquivo_renomeado = os.path.join(app.config['UPLOAD_FOLDER'], novo_nome_seguro)

        try:
            os.rename(caminho_arquivo_original, caminho_arquivo_renomeado)
        except OSError as e:
            print(f"Erro ao renomear ficheiro: {e}")
            resultados_finais.append({"nome_original": filename_original, "erro": "Não foi possível renomear o ficheiro no servidor."})
            if os.path.exists(caminho_arquivo_original):
                os.remove(caminho_arquivo_original)
            continue

        resultados_finais.append({
            "nome_original": filename_original,
            "novo_nome": novo_nome,
            "novo_nome_servidor": novo_nome_seguro,
            "descricao": resultado_ia.get('descricao', 'Nenhuma descrição gerada.')
        })

        time.sleep(1)

    return jsonify(resultados_finais)


@app.route('/download/<path:filename>')
def download_file(filename):
    try:
        return send_from_directory(
            app.config['UPLOAD_FOLDER'], 
            filename, 
            as_attachment=True
        )
    except FileNotFoundError:
        return "Ficheiro não encontrado.", 404

if __name__ == '__main__':
    app.run(debug=True)