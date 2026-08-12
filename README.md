# markdown-transformer

Microservicio HTTP en Python (FastAPI) que convierte archivos a Markdown, usando [MarkItDown](https://github.com/microsoft/markitdown) (Microsoft, MIT).

Formatos soportados: PDF, Word, PowerPoint, Excel, HTML, CSV, JSON, XML, e imágenes (JPG/PNG, con descripción generada por Gemini). Audio no está implementado todavía.

## Endpoints

- `GET /health` — estado del servicio, incluye `vision_enabled` (si hay una `GEMINI_API_KEY` configurada)
- `POST /convert` — recibe un archivo (`multipart/form-data`, campo `file`), devuelve `{"filename": ..., "markdown": ...}`. Requiere el header `x-api-key`.

## Variables de entorno

Ver `.env` (no versionado — crear a partir de este listado):

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `API_KEY` | Sí | Contraseña que deben mandar los clientes de este servicio en el header `x-api-key` |
| `GEMINI_API_KEY` | No | Habilita descripción de imágenes vía Gemini. Sin ella, las imágenes se convierten igual pero sin descripción |
| `GEMINI_MODEL` | No | Modelo de Gemini a usar. Default: `gemini-3.5-flash-lite` |
| `MAX_FILE_SIZE_MB` | No | Límite de tamaño de archivo aceptado. Default: `20` |

## Correr local

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Correr con Docker

```bash
docker compose up -d --build
```

No expone puerto al host a propósito — pensado para correr en una red Docker interna (ver `docker-compose.yml`), sin acceso directo desde internet.

## Licencia

MIT — ver [`LICENSE`](./LICENSE).

Usa la librería [MarkItDown](https://github.com/microsoft/markitdown) de Microsoft, también MIT.
