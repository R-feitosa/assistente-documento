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

load_dotenv()

# --- Configuração de backends ---
# BACKEND_PRIMARY pode ser "local" (Ollama, LM Studio etc.) ou "openrouter" (nuvem).
# BACKEND_FALLBACK é acionado quando o primário falha ou devolve JSON inválido.
# Deixe BACKEND_FALLBACK vazio para desabilitar o fallback.
BACKEND_PRIMARY = os.getenv("BACKEND_PRIMARY", "local").lower()
BACKEND_FALLBACK = os.getenv("BACKEND_FALLBACK", "openrouter").lower()

LOCAL_LLM_URL = os.getenv("LOCAL_LLM_URL", "http://localhost:11434/v1")
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "gemma3:12b")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")

# Limites
PDF_TEXT_MIN_CHARS = 200          # abaixo disso considera PDF escaneado e usa visão
PDF_TEXT_MAX_CHARS = 24000        # truncamento de segurança para prompts textuais
PDF_VISION_MAX_PAGES = 5          # quantas páginas renderizar para modelos de visão
PDF_RENDER_DPI = 150              # DPI da renderização página→imagem

PROMPT_BASE = """
Analise o conteúdo a seguir e retorne as informações no formato JSON.
1.  **tipo_documento**: Identifique o tipo do documento (ex: 'CONTRATO', 'NOTA_FISCAL', 'FOTO_PAISAGEM', 'GRAFICO', 'IDENTIDADE').
2.  **titulo_resumido**: Crie um título curto e descritivo para o documento (ex: 'Contrato de Aluguel', 'Conta de Energia'). Máximo de 5 palavras.
3.  **detalhe_principal**: Extraia o nome da pessoa principal ou da empresa principal mencionada no documento. Identificar os nomes das partes, reclamante/reclamado, exequente/executado, etc. Se não houver, extraia o endereço principal. Use este detalhe para o nome do arquivo.
4.  **descricao**: Crie uma breve descrição do conteúdo. Se houver texto, resuma as informações mais importantes. Se for uma imagem sem texto, descreva a cena. Máximo de 50 palavras.
Responda APENAS com o objeto JSON. Não inclua texto explicativo, a palavra 'json' nem ```. Sua resposta deve começar com { e terminar com }.
"""

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# ---------- Extração de conteúdo dos arquivos ----------

def _extract_pdf_text(caminho_arquivo):
    texto = ""
    with fitz.open(caminho_arquivo) as doc:
        for pagina in doc:
            texto += pagina.get_text()
    return texto


def _render_pdf_to_jpeg_b64(caminho_arquivo, max_pages=PDF_VISION_MAX_PAGES, dpi=PDF_RENDER_DPI):
    """Renderiza as primeiras páginas de um PDF como JPEG base64 (uma string por página)."""
    imagens = []
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    with fitz.open(caminho_arquivo) as doc:
        total = min(len(doc), max_pages)
        for i in range(total):
            pix = doc[i].get_pixmap(matrix=matrix, alpha=False)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=85)
            imagens.append(base64.b64encode(buf.getvalue()).decode("utf-8"))
    return imagens


def _extract_docx_text(caminho_arquivo):
    documento = docx.Document(caminho_arquivo)
    return "\n".join(p.text for p in documento.paragraphs)


def _image_to_jpeg_b64(caminho_arquivo):
    img = Image.open(caminho_arquivo)
    if img.mode != "RGB":
        img = img.convert("RGB")
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# ---------- Construção das mensagens ----------

def _messages_text(texto):
    conteudo = PROMPT_BASE + "\n\n--- CONTEÚDO PARA ANÁLISE ---\n" + texto[:PDF_TEXT_MAX_CHARS]
    return [{"role": "user", "content": conteudo}]


def _messages_vision(imagens_b64):
    content = [{"type": "text", "text": PROMPT_BASE}]
    for b64 in imagens_b64:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
        })
    return [{"role": "user", "content": content}]


# ---------- Chamadas aos backends ----------

def _call_openai_compatible(base_url, api_key, model, messages, timeout=180):
    """Chamada genérica para qualquer endpoint compatível com /chat/completions."""
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    if "openrouter.ai" in base_url:
        headers["HTTP-Referer"] = "http://localhost"
        headers["X-Title"] = "Assistente Feitosa"

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 512,
        "response_format": {"type": "json_object"},
    }
    url = base_url.rstrip("/") + "/chat/completions"
    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def _call_backend(backend, messages):
    if backend == "local":
        return _call_openai_compatible(LOCAL_LLM_URL, None, LOCAL_LLM_MODEL, messages)
    if backend == "openrouter":
        if not OPENROUTER_API_KEY:
            raise RuntimeError("OPENROUTER_API_KEY não configurada.")
        return _call_openai_compatible(
            "https://openrouter.ai/api/v1", OPENROUTER_API_KEY, OPENROUTER_MODEL, messages
        )
    raise ValueError(f"Backend desconhecido: {backend}")


def _parse_json_resposta(content):
    limpo = content.strip()
    if limpo.startswith("```"):
        limpo = limpo.split("```", 2)[-1]
        if limpo.lstrip().lower().startswith("json"):
            limpo = limpo.split("\n", 1)[1] if "\n" in limpo else limpo
        limpo = limpo.rstrip("`").strip()
    inicio = limpo.find("{")
    fim = limpo.rfind("}")
    if inicio == -1 or fim == -1:
        raise ValueError("Resposta sem objeto JSON identificável.")
    return json.loads(limpo[inicio:fim + 1])


def _executar_com_fallback(messages):
    """Tenta o backend primário; em caso de falha, usa o fallback (se configurado)."""
    tentativas = [BACKEND_PRIMARY]
    if BACKEND_FALLBACK and BACKEND_FALLBACK != BACKEND_PRIMARY:
        tentativas.append(BACKEND_FALLBACK)

    ultimo_erro = None
    for backend in tentativas:
        try:
            print(f"[IA] Tentando backend: {backend}")
            content = _call_backend(backend, messages)
            return _parse_json_resposta(content)
        except Exception as e:
            ultimo_erro = e
            print(f"[IA] Backend '{backend}' falhou: {type(e).__name__}: {e}")
            continue
    raise RuntimeError(f"Todos os backends falharam. Último erro: {ultimo_erro}")


# ---------- Orquestrador ----------

def analisar_conteudo_com_ia(caminho_arquivo):
    extensao = os.path.splitext(caminho_arquivo)[1].lower()
    try:
        if extensao == ".pdf":
            texto = _extract_pdf_text(caminho_arquivo)
            if texto and len(texto.strip()) >= PDF_TEXT_MIN_CHARS:
                messages = _messages_text(texto)
            else:
                # PDF provavelmente escaneado: usa visão multimodal
                print(f"[IA] PDF com pouco texto ({len(texto.strip())} chars). Usando visão.")
                imagens = _render_pdf_to_jpeg_b64(caminho_arquivo)
                if not imagens:
                    return {
                        "tipo_documento": "N/A",
                        "titulo_resumido": "Conteúdo Ilegível",
                        "detalhe_principal": "SEM_DETALHE",
                        "descricao": "Não foi possível extrair conteúdo do PDF.",
                    }
                messages = _messages_vision(imagens)

        elif extensao == ".docx":
            texto = _extract_docx_text(caminho_arquivo)
            if not texto or len(texto.strip()) < 20:
                return {
                    "tipo_documento": "N/A",
                    "titulo_resumido": "Conteúdo Ilegível",
                    "detalhe_principal": "SEM_DETALHE",
                    "descricao": "Não foi possível extrair texto suficiente do DOCX.",
                }
            messages = _messages_text(texto)

        elif extensao in (".jpg", ".jpeg", ".png"):
            messages = _messages_vision([_image_to_jpeg_b64(caminho_arquivo)])

        else:
            return None

        return _executar_com_fallback(messages)

    except Exception as e:
        print(f"--- ERRO NA ANÁLISE ---")
        print(f"Arquivo: {os.path.basename(caminho_arquivo)}")
        print(f"Tipo do Erro: {type(e).__name__}")
        print(f"Mensagem do Erro: {e}")
        return None


# ---------- Rotas ----------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/favicon.ico')
def favicon():
    return '', 204


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
            if os.path.exists(caminho_arquivo_original):
                os.remove(caminho_arquivo_original)
            continue

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
            print(f"Erro ao renomear arquivo: {e}")
            resultados_finais.append({"nome_original": filename_original, "erro": "Não foi possível renomear o arquivo no servidor."})
            if os.path.exists(caminho_arquivo_original):
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
