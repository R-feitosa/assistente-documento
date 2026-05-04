---
title: Assistente de Documentos
emoji: 📄
colorFrom: red
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# Assistente de Documentos — RFeitosa Group

Aplicação Flask que analisa documentos (PDF, DOCX, JPG, PNG) com IA multimodal
(Gemini 2.5 Flash via OpenRouter) e sugere um nome de arquivo descritivo,
permitindo edição antes do download.

## Recursos

- Suporte a PDF (texto digital ou escaneado), DOCX e imagens.
- Renderização automática de PDF→imagem para escaneados.
- Cache por hash SHA-256: o mesmo arquivo nunca chama a IA duas vezes.
- Processamento paralelo de múltiplos uploads.
- Edição do nome sugerido antes da renomeação final.

## Variáveis de ambiente

Configurar como **Secrets** nas configurações do Space:

| Variável | Descrição |
|---|---|
| `OPENROUTER_API_KEY` | Chave da API OpenRouter (obrigatória) |
| `OPENROUTER_MODEL` | Modelo a usar (padrão: `google/gemini-2.5-flash`) |

## Desenvolvimento local

```bash
pip install -r requirements.txt
cp .env.example .env   # preencha OPENROUTER_API_KEY
python app.py          # sobe em http://localhost:5001
```
