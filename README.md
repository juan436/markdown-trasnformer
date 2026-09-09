# markdown-transformer

Microservicio HTTP en Python (FastAPI) que convierte archivos a Markdown, usando [MarkItDown](https://github.com/microsoft/markitdown) (Microsoft, MIT).

Formatos soportados: PDF, Word, PowerPoint, Excel, HTML, CSV, JSON, XML, e imágenes (JPG/PNG, con descripción generada por Gemini cuando hay clave configurada). Audio no está implementado todavía.

---

## Para qué existe

Otros servicios propios (el portafolio, agentes) necesitan aceptar archivos que sube el usuario y trabajarlos como texto. En vez de meter la librería de conversión en cada uno, vive una sola vez acá: un endpoint pequeño, sin estado, con una sola responsabilidad.

```
consumidor  ──POST /convert (multipart + x-api-key)──►  markdown-transformer  ──►  { filename, markdown }
```

Sin acceso directo desde internet: el `docker-compose.yml` no publica puerto al host, el servicio se alcanza solo desde la red Docker interna donde corre. El contenedor arranca sin privilegios (`cap_drop: ALL`, `no-new-privileges`, usuario `appuser`).

---

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Estado del servicio; incluye `vision_enabled` (si hay `GEMINI_API_KEY`) |
| `POST` | `/convert` | Recibe un archivo (`multipart/form-data`, campo `file`), devuelve `{"filename": ..., "markdown": ...}`. Requiere el header `x-api-key` |

Respuestas de error: `401` clave inválida · `413` archivo demasiado grande · `422` la conversión falló.

---

## Diseño

- **Autenticación:** comparación en tiempo constante (`hmac.compare_digest`) de `x-api-key` contra `API_KEY`.
- **Límite de tamaño:** el archivo se lee por chunks de 1 MB y se aborta apenas supera `MAX_FILE_SIZE_MB`, sin cargar todo en memoria.
- **Extensión segura:** solo se conserva el sufijo del archivo si matchea `^\.[A-Za-z0-9]{1,10}$`, para no pasar nombres raros al conversor.
- **Sin estado:** cada request escribe a un archivo temporal que se borra en el `finally`. No hay disco persistente ni base de datos.
- **Visión opcional:** si hay `GEMINI_API_KEY`, las imágenes se describen vía la API compatible con OpenAI de Gemini; sin ella se convierten igual, sin descripción.

---

## Variables de entorno

Ver [`.env.example`](.env.example). Resumen:

| Variable | Requerida | Descripción |
|---|---|---|
| `API_KEY` | sí | Clave que deben mandar los consumidores en `x-api-key` |
| `GEMINI_API_KEY` | no | Habilita descripción de imágenes |
| `GEMINI_MODEL` | no | Default: `gemini-3.5-flash-lite` |
| `MAX_FILE_SIZE_MB` | no | Default: `20` |

---

## Correr en local

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell  (source .venv/bin/activate en Linux/Mac)
pip install -r requirements.txt
cp .env.example .env               # completar API_KEY
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Prueba rápida:

```bash
curl -H "x-api-key: $API_KEY" -F "file=@documento.pdf" http://127.0.0.1:8000/convert
```

## Correr con Docker

```bash
docker compose up -d --build
```

---

## Forma de trabajo

- **Rama única `main`**, commits con Conventional Commits (`feat:`, `chore:`, `fix:`).
- **Alcance cerrado a propósito:** un archivo (`app/main.py`), sin capas ni framework de más. Cualquier feature nueva (audio, otro proveedor de visión) entra sin romper el contrato `{ filename, markdown }`.
- **Dependencias pinneadas** a versión exacta en `requirements.txt`.

---

## Licencia

MIT — ver [`LICENSE`](./LICENSE). Usa [MarkItDown](https://github.com/microsoft/markitdown) de Microsoft, también MIT.
