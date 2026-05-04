import os
import fitz  # PyMuPDF
import docx
import json
import uuid
import base64
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import requests
from PIL import Image
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

try:
    from unidecode import unidecode
except ImportError:  # fallback se a dependência ainda não estiver instalada
    def unidecode(s):
        return s

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")

# Limites
PDF_TEXT_MIN_CHARS = 200          # abaixo disso considera PDF escaneado e usa visão
PDF_TEXT_MAX_CHARS = 24000        # truncamento de segurança para prompts textuais
PDF_VISION_MAX_PAGES = 5          # quantas páginas renderizar para modelos de visão
PDF_RENDER_DPI = 150              # DPI da renderização página→imagem
IMAGE_MAX_DIM = 1280              # lado maior em pixels antes de enviar à IA
PARALLEL_WORKERS = 5              # threads simultâneas no processamento de lote
MAX_UPLOAD_MB = 50                # limite de tamanho por requisição

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
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_MB * 1024 * 1024
PENDING_FOLDER = os.path.join(app.config['UPLOAD_FOLDER'], '.pending')
os.makedirs(PENDING_FOLDER, exist_ok=True)


# ---------- Cache por hash ----------

CACHE_FILE = "cache.json"
_cache_lock = threading.Lock()


def _carregar_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _salvar_cache(cache):
    tmp = CACHE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CACHE_FILE)


def _hash_arquivo(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _cache_get(file_hash):
    with _cache_lock:
        return _carregar_cache().get(file_hash)


def _cache_set(file_hash, resultado):
    with _cache_lock:
        cache = _carregar_cache()
        cache[file_hash] = resultado
        _salvar_cache(cache)


# ---------- Extração de conteúdo dos arquivos ----------

def _extract_pdf_text(caminho_arquivo):
    texto = ""
    with fitz.open(caminho_arquivo) as doc:
        for pagina in doc:
            texto += pagina.get_text()
    return texto


def _downscale(img, max_dim=IMAGE_MAX_DIM):
    largura, altura = img.size
    maior = max(largura, altura)
    if maior <= max_dim:
        return img
    fator = max_dim / maior
    return img.resize((int(largura * fator), int(altura * fator)), Image.LANCZOS)


def _render_pdf_to_jpeg_b64(caminho_arquivo, max_pages=PDF_VISION_MAX_PAGES, dpi=PDF_RENDER_DPI):
    imagens = []
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    with fitz.open(caminho_arquivo) as doc:
        total = min(len(doc), max_pages)
        for i in range(total):
            pix = doc[i].get_pixmap(matrix=matrix, alpha=False)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            img = _downscale(img)
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
    img = _downscale(img)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
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


# ---------- Chamada ao OpenRouter ----------

def _chamar_openrouter(messages, timeout=180):
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY não configurada.")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "Assistente Feitosa",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "max_tokens": 512,
        "response_format": {"type": "json_object"},
    }
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers, json=payload, timeout=timeout,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


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


# ---------- Orquestrador ----------

def analisar_conteudo_com_ia(caminho_arquivo):
    extensao = os.path.splitext(caminho_arquivo)[1].lower()
    try:
        if extensao == ".pdf":
            texto = _extract_pdf_text(caminho_arquivo)
            if texto and len(texto.strip()) >= PDF_TEXT_MIN_CHARS:
                messages = _messages_text(texto)
            else:
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

        return _parse_json_resposta(_chamar_openrouter(messages))

    except Exception as e:
        print(f"--- ERRO NA ANÁLISE ---")
        print(f"Arquivo: {os.path.basename(caminho_arquivo)}")
        print(f"Tipo do Erro: {type(e).__name__}")
        print(f"Mensagem do Erro: {e}")
        return None


def analisar_com_cache(caminho_arquivo):
    file_hash = _hash_arquivo(caminho_arquivo)
    cached = _cache_get(file_hash)
    if cached is not None:
        print(f"[CACHE] Hit para {os.path.basename(caminho_arquivo)}")
        return cached
    resultado = analisar_conteudo_com_ia(caminho_arquivo)
    if resultado is not None:
        _cache_set(file_hash, resultado)
    return resultado


# ---------- Helpers de nome ----------

def _construir_nome_sugerido(resultado):
    titulo = (resultado.get('titulo_resumido') or 'SEM_TITULO').replace(' ', '_').replace('/', '_')
    detalhe = (resultado.get('detalhe_principal') or 'SEM_DETALHE').replace(' ', '_').replace('/', '_')
    return f"{titulo}-{detalhe}"


def _sanitizar_nome_final(nome_base, sufixo, extensao):
    base = unidecode(nome_base).strip()
    nome_completo = f"{base}-{sufixo}{extensao}"
    return secure_filename(nome_completo) or f"documento-{sufixo}{extensao}"


# ---------- Rotas ----------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/favicon.ico')
def favicon():
    return '', 204


@app.route('/upload', methods=['POST'])
def upload_arquivo():
    """Salva os arquivos como pendentes e analisa em paralelo. NÃO renomeia ainda."""
    if 'arquivo' not in request.files:
        return jsonify({"erro": "Nenhum arquivo enviado"}), 400

    arquivos = request.files.getlist('arquivo')

    # Fase 1 (sequencial, rápida): salvar todos em .pending/
    pendentes = []
    for arquivo in arquivos:
        if arquivo.filename == '':
            continue
        filename_original = secure_filename(arquivo.filename)
        extensao = os.path.splitext(filename_original)[1].lower()
        pending_id = uuid.uuid4().hex
        pending_path = os.path.join(PENDING_FOLDER, f"{pending_id}{extensao}")
        arquivo.save(pending_path)
        pendentes.append({
            "id": pending_id,
            "filename_original": filename_original,
            "extensao": extensao,
            "pending_path": pending_path,
        })

    # Fase 2 (paralela): hash + cache + IA
    def _processar(item):
        resultado = analisar_com_cache(item["pending_path"])
        if resultado is None:
            try:
                os.remove(item["pending_path"])
            except OSError:
                pass
            return {"nome_original": item["filename_original"], "erro": "Não foi possível analisar este arquivo."}
        return {
            "id": item["id"],
            "extensao": item["extensao"],
            "nome_original": item["filename_original"],
            "novo_nome_sugerido": _construir_nome_sugerido(resultado),
            "descricao": resultado.get('descricao', 'Nenhuma descrição gerada.'),
        }

    with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as pool:
        resultados = list(pool.map(_processar, pendentes))

    return jsonify(resultados)


@app.route('/confirmar', methods=['POST'])
def confirmar_renomeacao():
    """Renomeia o arquivo pendente para o nome final (eventualmente editado pelo usuário)."""
    data = request.get_json(silent=True) or {}
    pending_id = data.get('id', '').strip()
    extensao = (data.get('extensao') or '').lower()
    novo_nome = (data.get('novo_nome') or '').strip()

    if not pending_id or not novo_nome:
        return jsonify({"erro": "id e novo_nome são obrigatórios"}), 400

    # Bloqueio simples contra path traversal no id
    if not pending_id.isalnum():
        return jsonify({"erro": "id inválido"}), 400

    pending_path = os.path.join(PENDING_FOLDER, f"{pending_id}{extensao}")
    if not os.path.exists(pending_path):
        return jsonify({"erro": "Arquivo pendente não encontrado (talvez já confirmado)."}), 404

    nome_final = _sanitizar_nome_final(novo_nome, pending_id[:6], extensao)
    destino = os.path.join(app.config['UPLOAD_FOLDER'], nome_final)

    try:
        os.rename(pending_path, destino)
    except OSError as e:
        return jsonify({"erro": f"Falha ao renomear: {e}"}), 500

    return jsonify({"novo_nome_servidor": nome_final, "novo_nome": nome_final})


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
    porta = int(os.getenv("PORT", "5001"))
    app.run(debug=True, port=porta)
