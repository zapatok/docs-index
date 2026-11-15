# Instrucciones para agentes IA

Esta carpeta es una **biblioteca verificable** de normativa chilena de prevención de riesgos:
168 documentos oficiales, 6.867 páginas, 13.749 fragmentos con norma, página y artículo.
La consulta es de solo lectura y no requiere permisos especiales.

## Regla de oro

**Nunca respondas una pregunta normativa de memoria.** Busca, lee el fragmento, y cita
`norma + página + artículo`. Si la base no lo tiene, dilo: no completes con conocimiento general
sin marcarlo como tal.

## Flujo recomendado (4 pasos)

1. `buscar` con la pregunta en lenguaje natural (`"plazo para denunciar un accidente"`,
   `"sílice exposición"`, `"comité paritario obligación"`). Usa 8 fragmentos; si el tema es
   amplio, pide 15.
2. Si el fragmento está cortado, `contexto(chunk_id, radio=1..2)` para leer la página contigua, o
   `fragmento(chunk_id)` para el texto completo del trozo.
3. Si necesitas el artículo exacto, `articulo(norma, art)`. Los identificadores de norma son los que
   devuelve `documentos()` (`"Ley 16.744"`, `"DS 40"`, `"DFL 1"`, `"NCh 1411"`, …).
4. Redacta citando `citar(chunk_ids)`. Formato esperado: `Ley 16.744 (1968), p. 24, Art. 66`.

## Qué hay dentro

| categoría | documentos | fragmentos | contenido |
|---|---|---|---|
| `01-marco-legal` | 6 | 1.383 | Ley 16.744, DFL 1, Ley 20.123, Ley 21.561… |
| `02-reglamentos` | 14 | 2.623 | DS 40, DS 44, DS 54, DS 594, DS 18… |
| `03-protocolos-minsal` | 46 | 2.029 | PREXOR, sílice, TMERT, psicosocial, asbesto, plaguicidas, citostáticos, metales, UV, hipobaria/hiperbaria, dermatitis, voz, fiebre Q, gripe aviar |
| `04-guias-tecnicas` | 2 | 66 | guías de implementación |
| `05-suseso` | 6 | 4.331 | compendio de normativa SUSESO |
| `06-normas-nch` | 94 | 3.317 | NCh de seguridad y ergonomía |

## Límites y trampas conocidas

- **OCR**: 11 documentos (293 páginas) se leyeron con OCR; `documento(id)` los marca
  `extraido='ocr'`. Pueden fallar cifras o nombres propios: si un dato crítico viene de uno de
  esos, verifica en el PDF antes de afirmarlo.
- **Artículos**: `section` se llena cuando el PDF trae `Art. N` explícito; en los documentos con
  formato de numeral (`1. TÍTULO`) la sección es el encabezado, no el artículo.
- **Duplicados**: el protocolo de sílice está como dos archivos con el mismo texto (852 fragmentos
  repetidos). Si dos resultados son idénticos, quédate con uno.
- **Búsqueda híbrida**: requiere el modelo de embeddings en el cliente. Sin él, la léxica ya
  resuelve bien términos técnicos chilenos (`prexor`, `tmert`, `susESO`).
- Una consulta = 8 s máximo. No hagas barridos masivos: para explorar un tema usa `buscar` con
  `n=15` y filtra por categoría.

## Entrega a terceros

Todo lo necesario está en este repositorio:

- `index.html` — buscador web (léxico, sin dependencias, con filtros y "copiar cita").
- `API.md` — contrato de la API (HTTP+SQL, MCP, CLI).
- `tools/kb.py` — cliente y CLI.
- `tools/kb_mcp.py` — servidor MCP (7 herramientas).
- `data/` (release) — `chunks.jsonl` con todos los fragmentos, `docs.jsonl`, `catalogo.csv`,
  `biblioteca.db` (SQLite con FTS5) y `emb.npy` (embeddings 384d) para uso offline.
