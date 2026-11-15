#!/usr/bin/env python3
"""Núcleo de consulta de la biblioteca (HTTP a Neon, sin dependencias obligatorias).

Uso como CLI:
  python3 kb.py buscar "prexor ruido" [-n 8] [--cat 03-] [--vec]
  python3 kb.py fragmento 5028
  python3 kb.py contexto 5028 --radio 2
  python3 kb.py documento 53
  python3 kb.py documentos [--cat 05-]
  python3 kb.py articulo "Ley 16.744" 66
"""
import argparse, json, os, re, sys, urllib.request

DSN = os.environ.get('KB_DSN') or os.environ.get('NEON_DSN') or ''
HOST_OVERRIDE = os.environ.get('KB_HOST')
USE_VEC = os.environ.get('KB_VEC', '1') not in ('0', 'false', 'no')

def _host():
    if HOST_OVERRIDE:
        return HOST_OVERRIDE
    h = DSN.split('@', 1)[1].split('/')[0].split('?')[0]
    return 'https://' + h + '/sql'

def sql(q, params=None, timeout=45):
    if not DSN:
        raise SystemExit('falta KB_DSN (cadena de conexión postgres://...)')
    body = json.dumps({'query': q, 'params': params or []}).encode()
    req = urllib.request.Request(_host(), data=body, headers={
        'Content-Type': 'application/json', 'Neon-Connection-String': DSN})
    try:
        j = json.load(urllib.request.urlopen(req, timeout=timeout))
    except urllib.error.HTTPError as e:
        raise SystemExit('error SQL: ' + e.read().decode()[:300])
    if j.get('message'):
        raise SystemExit('error SQL: ' + j['message'])
    return j['rows']

# ---------- embeddings (opcional) ----------
_model = None
def _embed(texts):
    global _model
    if _model is None:
        from fastembed import TextEmbedding
        _model = TextEmbedding(model_name=os.environ.get(
            'KB_EMB_MODEL', 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'))
    return [list(map(float, v)) for v in _model.embed(texts)]

def _vlit(vec):
    return "'[" + ",".join('%.6f' % x for x in vec) + "]'::vector"

# ---------- operaciones ----------
def buscar(q, n=8, cat=None):
    if USE_VEC:
        try:
            v = _vlit(_embed([q])[0])
            return sql("select chunk_id, doc_id, norma, tipo, anio, archivo, page, section, texto, "
                       "round(score::numeric,6)::text as score, origen "
                       "from buscar_hibrido($1, %s, $2, $3)" % v, [q, n, cat])
        except Exception as e:
            print('aviso: híbrida no disponible (%s), uso léxica' % str(e)[:60], file=sys.stderr)
    return sql("select chunk_id, doc_id, norma, tipo, anio, archivo, page, section, texto, "
               "round(rank::numeric,6)::text as score, 'lexico' as origen "
               "from buscar_cat($1, $2, $3)", [q, n, cat])

def fragmento(cid):
    return sql("select * from fragmento($1)", [cid])

def contexto(cid, radio=1):
    return sql("select * from contexto($1, $2)", [cid, radio])

def documento(did):
    return sql("select * from documento($1)", [did])

def documentos(cat=None):
    rows = sql("select * from documentos()")
    return [r for r in rows if not cat or str(r.get('categoria', '')).startswith(cat)]

def articulo(norma, art, n=10):
    return sql("select * from articulo($1, $2, $3)", [norma, art, n])

def cita(r):
    """Cita legible a partir de una fila de resultado."""
    if isinstance(r, dict) and 'section' in r:
        s = '%s' % r.get('norma')
        if r.get('anio'):
            s += ' (%s)' % r['anio']
        s += ', p. %s' % r.get('page')
        if r.get('section'):
            s += ', %s' % r['section']
        return s
    return str(r)

def main():
    ap = argparse.ArgumentParser(prog='kb')
    sub = ap.add_subparsers(dest='cmd', required=True)
    b = sub.add_parser('buscar'); b.add_argument('q'); b.add_argument('-n', type=int, default=8)
    b.add_argument('--cat'); b.add_argument('--vec', action='store_true'); b.add_argument('--json', action='store_true')
    f = sub.add_parser('fragmento'); f.add_argument('id', type=int)
    c = sub.add_parser('contexto'); c.add_argument('id', type=int); c.add_argument('--radio', type=int, default=1)
    d = sub.add_parser('documento'); d.add_argument('id', type=int)
    ds = sub.add_parser('documentos'); ds.add_argument('--cat')
    a = sub.add_parser('articulo'); a.add_argument('norma'); a.add_argument('art'); a.add_argument('-n', type=int, default=5)
    args = ap.parse_args()
    if args.cmd == 'buscar':
        rows = buscar(args.q, args.n, args.cat)
        if args.json:
            print(json.dumps(rows, ensure_ascii=False, indent=1)); return
        for r in rows:
            print('— ' + cita(r) + '   [chunk %s]' % r['chunk_id'])
            print('  ' + ' '.join((r['texto'] or '').split())[:400] + '\n')
    elif args.cmd == 'fragmento':
        for r in fragmento(args.id): print(json.dumps(r, ensure_ascii=False, indent=1))
    elif args.cmd == 'contexto':
        for r in contexto(args.id, args.radio):
            print('p.%s %s [%s]\n  %s\n' % (r['page'], r.get('section') or '', r['chunk_id'],
                  ' '.join((r['texto'] or '').split())[:700]))
    elif args.cmd == 'documento':
        print(json.dumps(documento(args.id), ensure_ascii=False, indent=1))
    elif args.cmd == 'documentos':
        for r in documentos(args.cat):
            print('%3s  %-52s %-22s %3s pág  %s' % (r['doc_id'], str(r['norma'])[:52], r['tipo'], r['paginas'], r['archivo']))
    elif args.cmd == 'articulo':
        for r in articulo(args.norma, args.art, args.n):
            print('— %s, p.%s, %s\n  %s\n' % (r['norma'], r['page'], r['section'], ' '.join((r['texto'] or '').split())[:600]))

if __name__ == '__main__':
    main()
