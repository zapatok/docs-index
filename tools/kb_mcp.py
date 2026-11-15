#!/usr/bin/env python3
"""Servidor MCP (Model Context Protocol, stdio) sobre la biblioteca de prevención.

Registro típico en el cliente del agente (Claude Desktop / Cursor / Codex / cualquier host MCP):

  {
    "mcpServers": {
      "biblioteca-prevencion": {
        "command": "python3",
        "args": ["/ruta/a/tools/kb_mcp.py"],
        "env": { "KB_DSN": "postgresql://web_ro:...@...neon.tech/neondb?sslmode=require" }
      }
    }
  }

Sin KB_DSN usa la cadena de config.js (rol de solo lectura) si está junto al script.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

def _load_dsn():
    d = os.environ.get('KB_DSN')
    if d:
        return d
    for p in (os.path.join(HERE, 'config.js'), os.path.join(HERE, '..', '_web', 'config.js')):
        try:
            t = open(p, encoding='utf-8').read()
            import re
            m = re.search(r'dsn:\s*"([^"]+)"', t)
            if m:
                return m.group(1)
        except OSError:
            pass
    return ''

os.environ['KB_DSN'] = _load_dsn()
import kb  # noqa: E402

TOOLS = [
    {
        "name": "buscar",
        "description": "Busca en 168 documentos oficiales chilenos de prevencion de riesgos (leyes, decretos, protocolos MINSAL, compendio SUSESO, normas NCh). Devuelve fragmentos con norma, pagina y articulo. Usalo antes de responder cualquier pregunta normativa.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "q": {"type": "string", "description": "consulta en espanol, lenguaje natural o palabras clave"},
                "n": {"type": "integer", "description": "numero de fragmentos (1-20, por defecto 8)"},
                "categoria": {"type": "string", "description": "filtro por carpeta: 01-marco-legal, 02-reglamentos, 03-protocolos-minsal, 04-guias-tecnicas, 05-suseso, 06-normas-nch"},
                "modo": {"type": "string", "enum": ["hibrido", "lexico"], "description": "hibrido (por defecto) usa tambien similitud semantica"}
            },
            "required": ["q"]
        }
    },
    {
        "name": "fragmento",
        "description": "Texto completo de un fragmento por su chunk_id (el que devuelve buscar).",
        "inputSchema": {"type": "object", "properties": {"chunk_id": {"type": "integer"}}, "required": ["chunk_id"]}
    },
    {
        "name": "contexto",
        "description": "Fragmentos vecinos del mismo documento alrededor de un chunk_id, para leer el articulo completo o la seccion contigua.",
        "inputSchema": {"type": "object", "properties": {"chunk_id": {"type": "integer"}, "radio": {"type": "integer", "description": "paginas de distancia (1-5, por defecto 1)"}}, "required": ["chunk_id"]}
    },
    {
        "name": "documento",
        "description": "Ficha de un documento: norma, tipo, anio, materia, paginas, si el texto vino de OCR.",
        "inputSchema": {"type": "object", "properties": {"doc_id": {"type": "integer"}}, "required": ["doc_id"]}
    },
    {
        "name": "documentos",
        "description": "Lista los 168 documentos disponibles (para saber que existe antes de buscar).",
        "inputSchema": {"type": "object", "properties": {"categoria": {"type": "string"}}}
    },
    {
        "name": "articulo",
        "description": "Devuelve el texto de un articulo concreto: articulo(norma='Ley 16.744', art='66').",
        "inputSchema": {"type": "object", "properties": {"norma": {"type": "string"}, "art": {"type": "string"}}, "required": ["norma", "art"]}
    },
    {
        "name": "citar",
        "description": "Convierte chunk_ids en citas listas para pegar: 'Ley 16.744 (1968), p. 24, Art. 66'.",
        "inputSchema": {"type": "object", "properties": {"chunk_ids": {"type": "array", "items": {"type": "integer"}}}, "required": ["chunk_ids"]}
    },
]

def fmt_buscar(rows):
    out = []
    for r in rows:
        out.append({
            "chunk_id": r["chunk_id"], "doc_id": r["doc_id"], "cita": kb.cita(r),
            "norma": r["norma"], "tipo": r["tipo"], "anio": r["anio"], "pagina": r["page"],
            "seccion": r["section"], "archivo": r["archivo"], "score": r["score"],
            "origen": r.get("origen"), "texto": r["texto"]})
    return out

def call(name, a):
    if name == 'buscar':
        rows = kb.buscar(a['q'], int(a.get('n', 8)), a.get('categoria'))
        return {"consulta": a['q'], "fragmentos": fmt_buscar(rows)}
    if name == 'fragmento':
        r = kb.fragmento(int(a['chunk_id']))
        return r[0] if r else {"error": "no existe"}
    if name == 'contexto':
        return {"chunk_id": int(a['chunk_id']), "vecinos": kb.contexto(int(a['chunk_id']), int(a.get('radio', 1)))}
    if name == 'documento':
        r = kb.documento(int(a['doc_id']))
        return r[0] if r else {"error": "no existe"}
    if name == 'documentos':
        rows = kb.documentos(a.get('categoria'))
        return {"total": len(rows), "documentos": rows}
    if name == 'articulo':
        return {"norma": a['norma'], "articulo": a['art'], "fragmentos": kb.articulo(a['norma'], a['art'])}
    if name == 'citar':
        rows = []
        for cid in a['chunk_ids']:
            r = kb.fragmento(int(cid))
            if r: rows.append({"chunk_id": int(cid), "cita": kb.cita(r[0])})
        return {"citas": rows}
    raise KeyError(name)

def reply(rid, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": rid}
    if error: msg["error"] = error
    else: msg["result"] = result
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        method = req.get('method'); rid = req.get('id')
        if method == 'initialize':
            reply(rid, {"protocolVersion": req.get('params', {}).get('protocolVersion', '2024-11-05'),
                        "capabilities": {"tools": {"listChanged": False}},
                        "serverInfo": {"name": "biblioteca-prevencion", "version": "1.0.0"},
                        "instructions": "Normativa chilena de prevención de riesgos: 168 documentos, 6.867 páginas. "
                                        "Busca siempre antes de responder y cita con norma, página y artículo."})
        elif method in ('notifications/initialized', 'initialized'):
            continue
        elif method == 'ping':
            reply(rid, {})
        elif method == 'tools/list':
            reply(rid, {"tools": TOOLS})
        elif method == 'tools/call':
            p = req.get('params', {})
            try:
                data = call(p.get('name'), p.get('arguments') or {})
                reply(rid, {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}],
                            "isError": False})
            except Exception as e:
                reply(rid, {"content": [{"type": "text", "text": "error: %s" % e}], "isError": True})
        elif rid is not None:
            reply(rid, error={"code": -32601, "message": "método no soportado: %s" % method})

if __name__ == '__main__':
    main()
