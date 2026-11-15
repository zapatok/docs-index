# Biblioteca de prevención de riesgos (Chile)

Buscador sobre **168 documentos oficiales** (6.867 páginas, 13.749 fragmentos) de normativa chilena de seguridad y
salud laboral, indexados a nivel de artículo con cita verificable.

**Buscador:** https://zapatok.github.io/docs-index/

| | |
|---|---|
| documentos | 168 (PDF originales: 2.861 archivos, 657 MB) |
| páginas | 6.867 |
| fragmentos indexados | 13.749 |
| con artículo detectado | 2.755 |
| leídos por OCR | 11 documentos / 293 páginas |
| búsqueda | léxica (tsvector español) + semántica (pgvector 384d) + fusión RRF |
| infraestructura | Neon Postgres serverless, rol de solo lectura, sin backend propio |

## Contenido

- `index.html` · buscador web (filtros por categoría, copiar cita, ver completo).
- `API.md` · cómo consultar: HTTP+SQL, servidor MCP, CLI.
- `AGENTS.md` · instrucciones para que un agente IA use la base sin inventar artículos.
- `tools/kb.py` · cliente/CLI (`buscar`, `fragmento`, `contexto`, `documento`, `documentos`, `articulo`).
- `tools/kb_mcp.py` · servidor MCP por stdio con 7 herramientas.
- Release `datos-v1` · `chunks.jsonl`, `docs.jsonl`, `catalogo.csv`, `biblioteca.db`, `emb.npy`.

## Cómo se generó

`pdftotext -layout` por página → chunks ≤1.500 caracteres sin cruzar página → detección de
`Art. N` y encabezados → OCR con tesseract (spa, 200 dpi) en los 11 escaneados → carga a
Postgres con `tsvector('spanish')` y `vector(384)` → índices GIN + HNSW (coseno).

Reproducible: ver `_meta/build_index2.py`, `_meta/ocr.py`, `_meta/embed.py`, `_meta/load_cloud.py`.
