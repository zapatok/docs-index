# Entrega: biblioteca de prevención consultable por una IA

Todo lo necesario para que un tercero (persona + su agente) consulte, cruce y
redacte sobre normativa chilena de prevención, con citas verificables.

## 1. Qué hay

| Pieza | Dónde | Para qué |
|---|---|---|
| Buscador web | https://zapatok.github.io/docs-index/ | consulta humana, login |
| API HTTP + SQL | Neon (endpoint en `API.md`) | cualquier lenguaje, sin backend |
| Servidor MCP | `tools/kb_mcp.py` | Claude Desktop, Cursor, cualquier cliente MCP |
| CLI | `tools/kb.py` | pruebas y scripts |
| Datos crudos | release `datos-v1` | reindexar en otro lado |
| PDFs originales | release `pdfs-v1` | abrir la fuente, `#page=N` |

Cifras: **174 documentos, 6.867+ páginas, 13.847 fragmentos**, 384 dimensiones,
español. Categorías: `01-` leyes y decretos, `02-` reglamentos, `03-` protocolos
MINSAL, `04-` guías técnicas, `05-` SUSESO, `06-` normas NCh, `07-` jurisprudencia.

## 2. Credenciales

- Web: usuario `zapatok`, contraseña entregada aparte por el dueño (el índice
  viaja cifrado en `config.js`; sin la contraseña no se descifra).
- Datos: DSN de PostgreSQL, rol **`web_ro`** (solo `select` y `execute`; sin
  `create`, sin escritura; `statement_timeout` 8 s). Viaja en `_index/cloud.json`
  y en el ejemplo de MCP; es de solo lectura por diseño, se puede rotar sin
  tocar los datos.

## 3. Montar el MCP

```json
{
  "mcpServers": {
    "biblioteca-prevencion": {
      "command": "python3",
      "args": ["/ruta/a/prevencion/tools/kb_mcp.py"],
      "env": { "KB_DSN": "postgresql://web_ro:...@ep-...-pooler.c-16.us-east-1.aws.neon.tech/neondb?sslmode=require" }
    }
  }
}
```

Requiere Python 3.11+ y, para búsqueda semántica, `pip install fastembed`.
Sin `fastembed` el servidor funciona igual: cae a búsqueda léxica expandida.

Siete herramientas: `buscar`, `fragmento`, `contexto`, `documento`,
`documentos`, `articulo`, `citar`.

## 4. Prompt para el agente del tercero

Está en `PROMPT.md`. Se pega tal cual como system prompt. Fija: no responder de
memoria, citar `(Norma, año, p. N, Art. X)`, abrir contexto cuando el fragmento
está cortado y declarar los vacíos.

## 5. Cómo verificar que la entrega funciona

```bash
# 1. la base responde y el rol no escribe
psql "$KB_DSN" -c "select count(*) from chunk"           # 13847
psql "$KB_DSN" -c "delete from chunk where id=1"         # ERROR: permission denied

# 2. la búsqueda con jerga trae el documento correcto
psql "$KB_DSN" -c "select norma,page,section from buscar('cphs',3,null)"
#   Compendio Libro IV … | 137 | …

# 3. el artículo exacto
psql "$KB_DSN" -c "select norma,page from articulo('Ley 16.744','66',2)"
#   Ley 16.744 | 24
```

## 6. Estado y límites

- **Jurisprudencia y dictámenes**: la Dirección del Trabajo no responde desde
  este entorno (`dt.gob.cl` cierra TLS y devuelve 522 en dos proxies distintos;
  Wayback responde 429; el índice de Common Crawl da 504 en esas consultas).
  Quedó sembrado con seis circulares de SUSESO (`07-jurisprudencia`). Para
  cargar dictámenes de la DT: descargarlos desde una conexión chilena a
  `prevencion/07-jurisprudencia/` y correr
  `python3 _meta/ingest_extra.py 07-jurisprudencia --categoria 07-jurisprudencia --tipo "Dictamen DT" --embed`.
- OCR: 293 páginas de 11 documentos escaneados pasaron por tesseract (`spa`).
  Puede haber errores de dígitos; los fragmentos traen página para contrastar.
- Duplicados: 193 fragmentos idénticos marcados (`chunk.dup_of`) y excluidos de
  todas las búsquedas.
- Sin login por usuario: una sola contraseña compartida, como se pidió. Si hace
  falta multiusuario, se cambia el rol y se agrega tabla de sesiones.
