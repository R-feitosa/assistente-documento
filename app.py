import os
import fitz  # PyMuPDF
import docx
import json
import uuid
import base64
import hashlib
import logging
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import requests
from PIL import Image
from flask import Flask, request, jsonify, render_template, send_from_directory, send_file
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

try:
    from unidecode import unidecode
except ImportError:
    def unidecode(s):
        return s

try:
    from pydantic import BaseModel, Field, ValidationError

    class ResultadoIA(BaseModel):
        tipo_documento: str = Field(default="DESCONHECIDO")
        titulo_resumido: str = Field(default="SEM_TITULO")
        detalhe_principal: str = Field(default="SEM_DETALHE")
        descricao: str = Field(default="")

    PYDANTIC_OK = True
except ImportError:
    PYDANTIC_OK = False

load_dotenv()

# --- Logging ---
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
)
log = logging.getLogger("assistente")

# --- Config ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
DEBUG = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")

# Limites
PDF_TEXT_MIN_CHARS = 200
PDF_TEXT_MAX_CHARS = 24000
PDF_VISION_MAX_PAGES = 5
PDF_RENDER_DPI = 150
IMAGE_MAX_DIM = 1280
PARALLEL_WORKERS = 5
MAX_UPLOAD_MB = 50
RETRY_MAX_TENTATIVAS = 3
RETRY_BACKOFF_BASE = 2  # segundos: 2, 4, 8

PROMPT_BASE = """
Analise o conteúdo a seguir e retorne as informações no formato JSON, com EXATAMENTE estes 4 campos:

1.  **tipo_documento**: Tipo do documento em MAIÚSCULAS_COM_SUBLINHADO (ex: 'CONTRATO', 'NOTA_FISCAL', 'PETICAO', 'IDENTIDADE', 'COMPROVANTE_RESIDENCIA', 'FOTO').
2.  **titulo_resumido**: Título curto e descritivo, máximo 5 palavras (ex: 'Contrato de Locação', 'Petição Inicial Trabalhista').
3.  **detalhe_principal**: Nome da pessoa/empresa principal. Em peças jurídicas: nomes das partes (reclamante/reclamado, exequente/executado, autor/réu) separados por "_e_". Se não houver nome, use o endereço principal.
4.  **descricao**: Resumo do conteúdo em até 50 palavras. Se for imagem sem texto, descreva a cena.

EXEMPLOS:

Conteúdo: "CONTRATO DE LOCAÇÃO RESIDENCIAL celebrado entre João da Silva (LOCADOR) e Maria Souza (LOCATÁRIA), referente ao imóvel situado na Rua das Flores, 100..."
Resposta:
{"tipo_documento": "CONTRATO", "titulo_resumido": "Contrato de Locacao Residencial", "detalhe_principal": "Joao_da_Silva_e_Maria_Souza", "descricao": "Contrato de locação residencial entre João da Silva (locador) e Maria Souza (locatária) sobre imóvel na Rua das Flores, 100."}

Conteúdo: "PETIÇÃO INICIAL - JUSTIÇA DO TRABALHO. Reclamante: Carlos Pereira. Reclamado: ACME Ltda. Pedido: verbas rescisórias..."
Resposta:
{"tipo_documento": "PETICAO", "titulo_resumido": "Peticao Inicial Trabalhista", "detalhe_principal": "Carlos_Pereira_e_ACME_Ltda", "descricao": "Petição inicial trabalhista. Reclamante: Carlos Pereira. Reclamado: ACME Ltda. Pedido de verbas rescisórias."}

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


# ---------- Extração de conteúdo ----------

def _extract_pdf_text(caminho):
    texto = ""
    with fitz.open(caminho) as doc:
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


def _render_pdf_to_jpeg_b64(caminho, max_pages=PDF_VISION_MAX_PAGES, dpi=PDF_RENDER_DPI):
    imagens = []
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    with fitz.open(caminho) as doc:
        total = min(len(doc), max_pages)
        for i in range(total):
            pix = doc[i].get_pixmap(matrix=matrix, alpha=False)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            img = _downscale(img)
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=85)
            imagens.append(base64.b64encode(buf.getvalue()).decode("utf-8"))
    return imagens


def _extract_docx_text(caminho):
    documento = docx.Document(caminho)
    return "\n".join(p.text for p in documento.paragraphs)


def _image_to_jpeg_b64(caminho):
    img = Image.open(caminho)
    if img.mode != "RGB":
        img = img.convert("RGB")
    img = _downscale(img)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# ---------- Mensagens ----------

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


# ---------- OpenRouter com retry ----------

def _eh_erro_transitorio(e):
    if isinstance(e, (requests.ConnectionError, requests.Timeout)):
        return True
    if isinstance(e, requests.HTTPError) and e.response is not None:
        return e.response.status_code in (429, 500, 502, 503, 504)
    return False


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
    data = response.json()
    usage = data.get("usage", {})
    log.info(
        "Tokens: in=%s out=%s total=%s | modelo=%s",
        usage.get("prompt_tokens", "?"),
        usage.get("completion_tokens", "?"),
        usage.get("total_tokens", "?"),
        OPENROUTER_MODEL,
    )
    return data["choices"][0]["message"]["content"]


def _chamar_openrouter_com_retry(messages):
    for tentativa in range(1, RETRY_MAX_TENTATIVAS + 1):
        try:
            return _chamar_openrouter(messages)
        except Exception as e:
            if tentativa == RETRY_MAX_TENTATIVAS or not _eh_erro_transitorio(e):
                raise
            espera = RETRY_BACKOFF_BASE ** tentativa
            log.warning(
                "Erro transitório (tentativa %d/%d): %s. Aguardando %ds.",
                tentativa, RETRY_MAX_TENTATIVAS, e, espera,
            )
            time.sleep(espera)


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
    bruto = json.loads(limpo[inicio:fim + 1])
    if PYDANTIC_OK:
        try:
            return ResultadoIA(**bruto).model_dump()
        except ValidationError as e:
            log.warning("Resposta da IA falhou na validação Pydantic: %s. Retornando bruto.", e)
            return bruto
    return bruto


# ---------- Orquestrador ----------

def analisar_conteudo_com_ia(caminho):
    extensao = os.path.splitext(caminho)[1].lower()
    try:
        if extensao == ".pdf":
            texto = _extract_pdf_text(caminho)
            if texto and len(texto.strip()) >= PDF_TEXT_MIN_CHARS:
                messages = _messages_text(texto)
            else:
                log.info("PDF com pouco texto (%d chars). Usando visão.", len(texto.strip()))
                imagens = _render_pdf_to_jpeg_b64(caminho)
                if not imagens:
                    return {
                        "tipo_documento": "N/A",
                        "titulo_resumido": "Conteúdo Ilegível",
                        "detalhe_principal": "SEM_DETALHE",
                        "descricao": "Não foi possível extrair conteúdo do PDF.",
                    }
                messages = _messages_vision(imagens)

        elif extensao == ".docx":
            texto = _extract_docx_text(caminho)
            if not texto or len(texto.strip()) < 20:
                return {
                    "tipo_documento": "N/A",
                    "titulo_resumido": "Conteúdo Ilegível",
                    "detalhe_principal": "SEM_DETALHE",
                    "descricao": "Não foi possível extrair texto suficiente do DOCX.",
                }
            messages = _messages_text(texto)

        elif extensao in (".jpg", ".jpeg", ".png"):
            messages = _messages_vision([_image_to_jpeg_b64(caminho)])

        else:
            return None

        return _parse_json_resposta(_chamar_openrouter_com_retry(messages))

    except Exception as e:
        log.error("Erro analisando %s: %s: %s", os.path.basename(caminho), type(e).__name__, e)
        return None


def analisar_com_cache(caminho):
    file_hash = _hash_arquivo(caminho)
    cached = _cache_get(file_hash)
    if cached is not None:
        log.info("Cache HIT para %s", os.path.basename(caminho))
        return cached
    log.info("Cache MISS para %s — chamando IA", os.path.basename(caminho))
    resultado = analisar_conteudo_com_ia(caminho)
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
    return secure_filename(f"{base}-{sufixo}{extensao}") or f"documento-{sufixo}{extensao}"


def _renomear_pendente(item):
    """Move um arquivo de .pending/ para uploads/ com o nome final.
    Retorna (nome_final, caminho_destino) ou None se não foi possível."""
    pending_id = item.get('id', '').strip()
    extensao = (item.get('extensao') or '').lower()
    novo_nome = (item.get('novo_nome') or '').strip()

    if not pending_id or not novo_nome or not pending_id.isalnum():
        return None

    pending_path = os.path.join(PENDING_FOLDER, f"{pending_id}{extensao}")
    if not os.path.exists(pending_path):
        return None

    nome_final = _sanitizar_nome_final(novo_nome, pending_id[:6], extensao)
    destino = os.path.join(app.config['UPLOAD_FOLDER'], nome_final)
    try:
        os.rename(pending_path, destino)
    except OSError as e:
        log.error("Falha ao renomear %s → %s: %s", pending_path, destino, e)
        return None
    return nome_final, destino


# ---------- Rotas ----------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/favicon.ico')
def favicon():
    return '', 204


@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "openrouter_configured": bool(OPENROUTER_API_KEY),
        "model": OPENROUTER_MODEL,
    })


@app.route('/upload', methods=['POST'])
def upload_arquivo():
    if 'arquivo' not in request.files:
        return jsonify({"erro": "Nenhum arquivo enviado"}), 400

    arquivos = request.files.getlist('arquivo')

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

    log.info("Recebidos %d arquivos. Iniciando análise paralela.", len(pendentes))

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
    data = request.get_json(silent=True) or {}
    resultado = _renomear_pendente(data)
    if resultado is None:
        return jsonify({"erro": "Não foi possível confirmar (id/nome inválido ou pendente expirado)."}), 400
    nome_final, _ = resultado
    return jsonify({"novo_nome_servidor": nome_final, "novo_nome": nome_final})


@app.route('/baixar-zip', methods=['POST'])
def baixar_zip():
    """Renomeia todos os pendentes informados e devolve um ZIP em memória."""
    data = request.get_json(silent=True) or {}
    itens = data.get('itens', [])
    if not itens:
        return jsonify({"erro": "Nenhum item enviado"}), 400

    arquivos_finais = []
    for item in itens:
        resultado = _renomear_pendente(item)
        if resultado:
            arquivos_finais.append(resultado)

    if not arquivos_finais:
        return jsonify({"erro": "Nenhum arquivo válido para zipar (pode já ter sido baixado)."}), 400

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for nome_final, caminho in arquivos_finais:
            zf.write(caminho, arcname=nome_final)
    buffer.seek(0)

    log.info("ZIP com %d arquivos gerado.", len(arquivos_finais))
    return send_file(
        buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='documentos-renomeados.zip',
    )


@app.route('/download/<path:filename>')
def download_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except FileNotFoundError:
        return "Arquivo não encontrado.", 404


if __name__ == '__main__':
    porta = int(os.getenv("PORT", "5001"))
    log.info("Subindo Flask em :%d (debug=%s, modelo=%s)", porta, DEBUG, OPENROUTER_MODEL)
    app.run(debug=DEBUG, port=porta, host="0.0.0.0")
