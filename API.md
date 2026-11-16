# API de la biblioteca de prevención

Base documental: **168 documentos oficiales chilenos** (leyes, DFL, decretos, protocolos MINSAL,
compendio SUSESO, normas NCh), **6.867 páginas**, **13.749 fragmentos** indexados con norma,
página y artículo.

Tres formas de consultarla, de la más simple a la más potente.

---

## 1. HTTP + SQL (sin instalar nada)

Endpoint: `POST https://<host>/sql` — es el driver HTTP de Neon.
Cabecera obligatoria: `Neon-Connection-String: <dsn del rol web_ro>`

```bash
DSN='postgresql://web_ro:...@<host>/neondb?sslmode=require'

curl -s "https://<host>/sql" \
  -H "Content-Type: application/json" \
  -H "Neon-Connection-String: $DSN" \
  -d '{"query":"select * from buscar_cat($1, $2, null)","params":["prexor ruido", 5]}'
```

Respuesta: `{"rows":[{"chunk_id":"5028","norma":"...","page":"30","section":"...","texto":"..."}], ...}`.
Los valores vienen **como texto** (driver HTTP), no como números. CORS abierto: se puede llamar
desde un navegador o desde un agente sin backend propio.

### Funciones disponibles (todas `execute` para `web_ro`)

| función | qué hace |
|---|---|
| `documentos()` | lista los 168 documentos con páginas y nº de fragmentos |
| `documento(id)` | ficha: norma, tipo, año, materia, categoría, páginas, si vino de OCR |
| `fragmento(chunk_id)` | texto completo de un fragmento + metadatos |
| `contexto(chunk_id, radio)` | fragmentos vecinos (±N páginas del mismo documento) |
| `buscar_cat(q, n, categoria)` | búsqueda léxica (tsvector español + bm25) con filtro de carpeta |
| `buscar_vec(vector, n, categoria)` | búsqueda semántica (pgvector, coseno) |
| `buscar_hibrido(q, vector, n, categoria, w_lex)` | fusión RRF de léxica + vectorial; devuelve `origen` |
| `articulo(norma, art, n)` | artículo exacto: `articulo('Ley 16.744','66')` |
| `fragmentos_doc(doc_id, n)` | todos los fragmentos de un documento en orden, con página y artículo (para leer una norma completa) |

Categorías para el filtro: `01-marco-legal`, `02-reglamentos`, `03-protocolos-minsal`,
`04-guias-tecnicas`, `05-suseso`, `06-normas-nch`.

### Ejemplos

```sql
-- artículo exacto
select * from articulo('Ley 16.744', '66', 5);

-- búsqueda con filtro por protocolo
select chunk_id, norma, page, section, left(texto, 200)
from buscar_cat('sílice exposición', 8, '03-protocolos-minsal');

-- vecinos de un fragmento (leer el artículo completo)
select * from contexto(5028, 2);
```

---

## 2. Servidor MCP (lo que usa un agente IA)

`tools/kb_mcp.py` habla MCP por stdio, sin dependencias obligatorias. Registro en el cliente:

```json
{
  "mcpServers": {
    "biblioteca-prevencion": {
      "command": "python3",
      "args": ["/ruta/a/tools/kb_mcp.py"],
      "env": { "KB_DSN": "postgresql://web_ro:...@<host>/neondb?sslmode=require" }
    }
  }
}
```

Herramientas: `buscar`, `fragmento`, `contexto`, `documento`, `documentos`, `articulo`, `citar`.

- `buscar` es híbrida si el cliente tiene `fastembed` instalado (`pip install fastembed`);
  si no, cae a léxica y avisa por stderr. El modelo es
  `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 dimensiones, CPU).
- Cada resultado trae `chunk_id`, `doc_id`, `cita`, `norma`, `pagina`, `seccion` y `texto`.
- `citar` convierte ids en citas listas: `Ley 16.744 (1968), p. 24, Art. 66`.

---

## 3. CLI (para humanos y para scripts)

```bash
export KB_DSN='postgresql://web_ro:...@<host>/neondb?sslmode=require'
python3 tools/kb.py buscar "plazo para denunciar un accidente" -n 5
python3 tools/kb.py articulo "Ley 16.744" 66
python3 tools/kb.py contexto 5028 --radio 2
python3 tools/kb.py documentos --cat 05-
```

`KB_VEC=0` fuerza solo léxica (útil si no hay modelo descargado).

---

## Reglas de uso

- **Solo lectura.** El rol `web_ro` no puede escribir: `delete from chunk` → `42501`. No hace falta
  pedir permiso para consultar; tampoco se puede romper nada.
- **Cita siempre** norma + página + artículo. El valor de esta base es que cada respuesta se puede
  verificar abriendo el PDF original en la página indicada.
- **No inventes artículos.** Si `articulo()` no devuelve nada, el artículo no está en la base:
  usa `buscar_cat` y lee el fragmento antes de afirmar.
- 11 documentos entraron por OCR (293 páginas): pueden tener errores de reconocimiento en números
  y nombres propios. `documento(id)` marca `extraido = 'ocr'`.
- Límites: 8 s por consulta (`statement_timeout`), sin cuota de peticiones. Uso razonable: decenas
  de consultas por minuto.

## Actualización 2026-11-16

**Regla de transporte.** El endpoint HTTP de Neon solo acepta
`Content-Type: text/plain` desde el navegador: su preflight CORS no incluye
`content-type` en `access-control-allow-headers`, así que con
`application/json` el navegador corta con `Failed to fetch`. El cuerpo sigue
siendo JSON.

### Funciones nuevas

| Función | Devuelve |
|---|---|
| `buscar(q,n,cat)` | léxica **con expansión de jerga** (usa `qexpand`) |
| `buscar_q(q,n,cat)` | igual que `buscar`, nombre histórico |
| `buscar_cat(q,n,cat)` | léxica sin expansión |
| `buscar_vec(vec,n,cat)` | semántica pura (`emb <=> vec`) |
| `buscar_hibrido(q,vec,n,cat,w)` | RRF léxico+vector, con `origen` |
| `articulo(norma,art,n)` | artículo exacto (`section = 'Art. '||art`) |
| `fragmentos_doc(doc_id)` | todos los fragmentos de un documento |
| `qexpand(q)` | la `tsquery` expandida, para depurar |

Todas excluyen duplicados (`dup_of is null`) y respetan `p_cat` como prefijo de
`archivo` (`'03-'` = protocolos MINSAL).

### Tesauro

Tabla `syn(term, exps)`, 92 términos con raíces en español
(`ts_lexize('spanish_stem', …)`). Ejemplos: `prexor → ruido, sonido,
audiometría`, `cphs → comité, paritario, higiene, seguridad`, `planesi → sílice,
polvo, neumoconiosis`, `oal → mutual, organismo administrador`. Se edita con
`insert into syn values ('jerga', array['raiz1','raiz2']) on conflict (term) do update set exps=excluded.exps`.

### Permisos

`web_ro` necesita `select` sobre `syn` porque `qexpand` la lee; además
`qexpand` y `buscar` están como `security definer` para que el rol no dependa de
permisos intermedios.
