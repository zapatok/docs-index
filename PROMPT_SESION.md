# Prompt para abrir una sesión nueva sobre este proyecto

Pégalo entero en una ventana nueva. Está escrito para que la sesión arranque con
todo el contexto y no repita trabajo ni rompa lo que ya funciona.

---

Trabajas en la **Biblioteca de prevención de riesgos laborales (Chile)**, un
corpus normativo consultable por humanos y por agentes.

## Dónde está todo

- Corpus e índice: `/workspace/prevencion` (168 PDFs originales + 6 circulares
  SUSESO en `07-jurisprudencia`).
- Scripts: `_meta/` → `build_index3.py` (extrae y corta), `ocr.py`, `embed.py`,
  `load_cloud.py` (chunks), `load_docs.py` (tabla `doc`), `load_emb.py`,
  `migrate3.py` (dedupe + tesauro + funciones), `ingest_extra.py` (mete
  cualquier carpeta de PDFs al índice).
- Credenciales: `_index/cloud.json` → `uri` (rol `neondb_owner`, escribe) y
  `web_ro_uri` (rol `web_ro`, solo lectura).
- Web publicada: `_web/` → repo `zapatok/docs-index`, Pages en
  https://zapatok.github.io/docs-index/ (login `zapatok`; la contraseña la tiene
  Daniel).
- Herramientas de consulta: `tools/kb.py` (CLI) y `tools/kb_mcp.py` (MCP stdio,
  7 herramientas), ambas leen `KB_DSN`.
- Paquete para terceros: `entrega-agent.zip` (PROMPT.md, API.md, AGENTS.md,
  ENTREGA.md, mcp.json, tools).

## Estado actual (2026-11-16)

- 174 documentos, 13.847 fragmentos, vectores 384d
  (`paraphrase-multilingual-MiniLM-L12-v2`), HNSW cosine.
- Duplicados exactos marcados en `chunk.dup_of` (193) y excluidos de todas las
  funciones.
- Tesauro de jerga chilena en tabla `syn` (92 términos) + `qexpand()`: `prexor`,
  `cphs`, `tmert`, `planesi`, `oal`, `iusc`, `epp` ya funcionan solos.
- Funciones: `buscar`, `buscar_q`, `buscar_cat`, `buscar_vec`, `buscar_hibrido`,
  `articulo`, `fragmentos_doc`, `documento`, `documentos`, `contexto`,
  `fragmento`, `qexpand`.
- PDFs servidos desde el release `pdfs-v1`; la web enlaza `#page=N`.
- Login único con el DSN cifrado en `config.js` (PBKDF2 400k + AES-GCM,
  descifrado en el navegador).

## Invariantes que no se rompen

1. Los fragmentos nunca cruzan página; la cita es `(Norma, año, p. N, Art. X)`.
2. `chunk` duplica `norma/tipo/anio/materia/area` desde `doc`: si insertas sin
   esas columnas, la búsqueda anda pero la ficha sale sin norma.
3. `chunk.id` no tiene secuencia: calcula `max(id)+1` antes de insertar.
4. El endpoint HTTP de Neon exige `Content-Type: text/plain` desde el navegador
   (su preflight CORS no lista `content-type`) y el `host` descifrado viene sin
   esquema: hay que anteponer `https://`.
5. `web_ro` no escribe: cualquier `insert/update/delete` debe fallar. Si no
   falla, el rol está mal.
6. No publiques claves completas en el repo: `config.js` lleva solo el blob
   cifrado.

## Verificación rápida antes de tocar nada

```bash
cd /workspace/prevencion
export KB_DSN=$(python3 -c "import json;print(json.load(open('_index/cloud.json'))['web_ro_uri'])")
python3 tools/kb.py buscar cphs -n 2        # Compendio Libro IV
python3 tools/kb.py articulo "Ley 16.744" 66 -n 1
curl -s -o /dev/null -w "%{http_code}\n" https://zapatok.github.io/docs-index/
```

## Pendiente

- **Dictámenes de la DT**: `dt.gob.cl` no responde desde este entorno (TLS
  cortado; 522 en dos proxies; 429 en Wayback; 504 en Common Crawl). Quedó
  sembrado con 6 circulares SUSESO. Cuando haya PDFs:
  `python3 _meta/ingest_extra.py 07-jurisprudencia --categoria 07-jurisprudencia --tipo "Dictamen DT" --embed`.
- Multiusuario con sesiones, si Daniel lo pide (hoy una sola contraseña).
- Revisar dígitos del OCR en los 11 documentos escaneados cuando una cifra sea
  decisiva.

## Cómo trabajar con Daniel

Directo, sin preámbulos, español neutro con tú. Verifica con comandos y cita la
salida. Si un número no cuadra, dilo. No inventes cifras, artículos ni rutas.
