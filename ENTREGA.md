# Cómo entregar la biblioteca a otra persona (y a su IA)

Tres niveles, según lo que quieras dar.

## Nivel 1 — solo mirar (30 segundos)

Manda el enlace: **https://zapatok.github.io/docs-index/**
Funciona en cualquier navegador, sin cuenta ni instalación. Busca, filtra por categoría y copia
citas con norma, página y artículo.

## Nivel 2 — que su IA consulte en vivo (5 minutos)

Su agente (Claude Desktop, Cursor, Codex, cualquier cliente MCP) se conecta a la misma base:

```json
{
  "mcpServers": {
    "biblioteca-prevencion": {
      "command": "python3",
      "args": ["/ruta/a/tools/kb_mcp.py"],
      "env": { "KB_DSN": "postgresql://web_ro:...@...neon.tech/neondb?sslmode=require" }
    }
  }
}
```

El `KB_DSN` se lo pasas tú (está en `config.js` del repo). Es un rol **de solo lectura**: no puede
escribir nada. Su IA tendrá 7 herramientas (`buscar`, `fragmento`, `contexto`, `documento`,
`documentos`, `articulo`, `citar`) y respuestas con cita verificable.

Para que la búsqueda sea **semántica** y no solo por palabras, que instale el modelo (una vez):

```bash
pip install fastembed   # ~80 MB, corre en CPU
```

Sin eso igual funciona: cae a búsqueda léxica, que ya resuelve los términos técnicos chilenos.

## Nivel 3 — los datos completos, offline (release `datos-v1`)

| archivo | qué es |
|---|---|
| `chunks.jsonl` | 13.749 fragmentos con norma, página, artículo y texto (18 MB) |
| `docs.jsonl` | 168 documentos con metadatos y ruta del PDF original |
| `catalogo.csv` | catálogo original (categoría, área, norma, tipo, año, materia, páginas) |
| `biblioteca.db` | SQLite con FTS5, listo para consultar sin servidor |
| `emb.npy` + `emb_ids.json` | embeddings 384d alineados con `chunks.jsonl` (20 MB) |
| `api.sql` | funciones SQL (`buscar_cat`, `buscar_vec`, `buscar_hibrido`, `articulo`…) |
| `build_index.py`, `ocr.py`, `embed.py`, `load_cloud.py`, `load_emb.py` | pipeline reproducible |

Con eso puede montar su propia copia en Postgres+pgvector, en SQLite, o cargar los fragmentos en
cualquier otro motor vectorial. Los PDF originales son públicos (fuentes oficiales: MINSAL, SUSESO,
DT, INN) y se pueden volver a descargar con `_meta/descarga.py` del proyecto.

## Qué decirle a su IA (pegando esto en el prompt de sistema)

> Tienes acceso a la biblioteca `biblioteca-prevencion`: 168 documentos oficiales chilenos de
> prevención de riesgos (6.867 páginas) con búsqueda léxica y semántica. Antes de responder
> cualquier pregunta normativa, usa `buscar`; si el fragmento está cortado, usa `contexto`; si
> necesitas el artículo exacto, usa `articulo`. Cita siempre norma, página y artículo con `citar`.
> Si la base no contiene el dato, dilo en vez de completar de memoria. Hay 11 documentos que
> vinieron de OCR: si el dato es crítico y viene de uno de ellos, avísalo.

## Límites

- Solo lectura, sin cuota de peticiones, 8 s por consulta.
- La base no contiene doctrina ni interpretación: solo el texto oficial.
- No incluye jurisprudencia ni dictámenes de la Dirección del Trabajo (pendiente).
